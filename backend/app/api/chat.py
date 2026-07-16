"""会话管理与知识库问答（含 SSE 流式）。"""

import json
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, DbSession
from app.models.feedback import MessageFeedback
from app.models.message import Message
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ConversationCreate,
    ConversationList,
    ConversationOut,
    ConversationUpdate,
    FeedbackOut,
    FeedbackRequest,
    MessageList,
    MessageOut,
    PageMeta,
)
from app.services import chat_service
from app.services.rag_service import generate_answer, sources_to_json, stream_answer
from app.utils.rate_limit import limiter

router = APIRouter(prefix="/chat", tags=["问答与会话"])


@router.get("/conversations", response_model=ConversationList)
def list_conversations(
    user: CurrentUser,
    db: DbSession,
    page: int = 1,
    page_size: int = 50,
) -> ConversationList:
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    items, total = chat_service.list_conversations(db, user.id, page, page_size)
    return ConversationList(
        items=[ConversationOut.model_validate(i) for i in items],
        meta=PageMeta(total=total, page=page, page_size=page_size),
    )


@router.post("/conversations", response_model=ConversationOut, status_code=status.HTTP_201_CREATED)
def create_conversation(
    user: CurrentUser,
    db: DbSession,
    body: Optional[ConversationCreate] = None,
) -> ConversationOut:
    title = (body.title if body else None) or "新会话"
    conv = chat_service.create_conversation(db, user.id, title)
    return ConversationOut.model_validate(conv)


@router.patch("/conversations/{conversation_id}", response_model=ConversationOut)
def rename_conversation(
    conversation_id: int,
    body: ConversationUpdate,
    user: CurrentUser,
    db: DbSession,
) -> ConversationOut:
    conv = chat_service.rename_conversation(db, conversation_id, user.id, body.title.strip())
    return ConversationOut.model_validate(conv)


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(conversation_id: int, user: CurrentUser, db: DbSession) -> None:
    chat_service.delete_conversation(db, conversation_id, user.id)


@router.get("/conversations/{conversation_id}/messages", response_model=MessageList)
def list_messages(
    conversation_id: int,
    user: CurrentUser,
    db: DbSession,
    page: int = 1,
    page_size: int = 200,
) -> MessageList:
    page = max(page, 1)
    page_size = min(max(page_size, 1), 500)
    items, total = chat_service.list_messages(db, conversation_id, user.id, page, page_size)
    return MessageList(
        items=[chat_service.message_to_out(m) for m in items],
        meta=PageMeta(total=total, page=page, page_size=page_size),
    )


@router.post("/ask", response_model=ChatResponse)
async def ask_non_stream(body: ChatRequest, user: CurrentUser, db: DbSession, request: Request) -> ChatResponse:
    """非流式问答（调试/兼容用）。"""
    limiter.check(f"ask:{user.id}", limit=30, window_seconds=60)
    conv_id, user_msg, assistant_msg, answer, sources = await _prepare_and_answer(
        db, user.id, body, stream=False
    )
    return ChatResponse(
        conversation_id=conv_id,
        user_message_id=user_msg.id,
        assistant_message_id=assistant_msg.id,
        answer=answer,
        sources=sources,
    )


@router.post("/ask/stream")
async def ask_stream(body: ChatRequest, user: CurrentUser, db: DbSession, request: Request):
    """SSE 流式问答。"""
    limiter.check(f"ask:{user.id}", limit=30, window_seconds=60)

    # 先准备会话与用户消息
    conversation_id = body.conversation_id
    if conversation_id is None:
        title = chat_service.auto_title_from_question(body.question)
        conv = chat_service.create_conversation(db, user.id, title)
        conversation_id = conv.id
    else:
        conv = chat_service.get_user_conversation(db, conversation_id, user.id)
        # 若仍是默认标题，用首问自动命名
        if conv.title in ("新会话", "") and body.question.strip():
            conv.title = chat_service.auto_title_from_question(body.question)
            db.commit()

    user_msg = chat_service.add_message(db, conversation_id, "user", body.question.strip())
    history = chat_service.get_recent_history(db, conversation_id)
    # 历史里已含刚写入的 user，生成时可用（最后一条是当前问题，prompt 里也有 question）

    async def event_generator():
        # 先告知会话与用户消息 id
        meta = {
            "type": "meta",
            "conversation_id": conversation_id,
            "user_message_id": user_msg.id,
        }
        yield f"data: {json.dumps(meta, ensure_ascii=False)}\n\n"

        full_answer = ""
        sources_payload = []
        try:
            async for event in stream_answer(body.question.strip(), history=history[:-1]):
                etype = event.get("type")
                if etype == "sources":
                    sources_payload = event.get("sources") or []
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                elif etype == "token":
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                elif etype == "done":
                    full_answer = event.get("answer") or ""
        except Exception as exc:  # noqa: BLE001
            err = {"type": "error", "message": f"生成失败: {exc}"}
            yield f"data: {json.dumps(err, ensure_ascii=False)}\n\n"
            full_answer = full_answer or f"抱歉，生成回答时出错：{exc}"

        # 落库助手消息
        from app.db.session import SessionLocal

        db2: Session = SessionLocal()
        try:
            assistant = chat_service.add_message(
                db2,
                conversation_id,
                "assistant",
                full_answer,
                sources_json=json.dumps(sources_payload, ensure_ascii=False),
            )
            done = {
                "type": "done",
                "answer": full_answer,
                "assistant_message_id": assistant.id,
                "conversation_id": conversation_id,
                "sources": sources_payload,
            }
            yield f"data: {json.dumps(done, ensure_ascii=False)}\n\n"
        finally:
            db2.close()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def _prepare_and_answer(db: Session, user_id: int, body: ChatRequest, stream: bool = False):
    conversation_id = body.conversation_id
    if conversation_id is None:
        title = chat_service.auto_title_from_question(body.question)
        conv = chat_service.create_conversation(db, user_id, title)
        conversation_id = conv.id
    else:
        conv = chat_service.get_user_conversation(db, conversation_id, user_id)
        if conv.title in ("新会话", "") and body.question.strip():
            conv.title = chat_service.auto_title_from_question(body.question)
            db.commit()

    user_msg = chat_service.add_message(db, conversation_id, "user", body.question.strip())
    history = chat_service.get_recent_history(db, conversation_id)
    answer, sources = await generate_answer(body.question.strip(), history=history[:-1])
    assistant_msg = chat_service.add_message(
        db,
        conversation_id,
        "assistant",
        answer,
        sources_json=sources_to_json(sources),
    )
    return conversation_id, user_msg, assistant_msg, answer, sources


@router.post("/messages/{message_id}/feedback", response_model=FeedbackOut)
def feedback_message(
    message_id: int,
    body: FeedbackRequest,
    user: CurrentUser,
    db: DbSession,
) -> FeedbackOut:
    if body.rating not in (1, -1):
        raise HTTPException(status_code=400, detail="rating 只能是 1（赞）或 -1（踩）")

    msg = db.query(Message).filter(Message.id == message_id).first()
    if not msg or msg.role != "assistant":
        raise HTTPException(status_code=404, detail="助手消息不存在")

    # 校验消息所属会话是当前用户的
    chat_service.get_user_conversation(db, msg.conversation_id, user.id)

    existing = (
        db.query(MessageFeedback)
        .filter(MessageFeedback.message_id == message_id, MessageFeedback.user_id == user.id)
        .first()
    )
    if existing:
        existing.rating = body.rating
        existing.comment = body.comment
        db.commit()
        db.refresh(existing)
        return FeedbackOut.model_validate(existing)

    fb = MessageFeedback(
        message_id=message_id,
        user_id=user.id,
        rating=body.rating,
        comment=body.comment,
    )
    db.add(fb)
    db.commit()
    db.refresh(fb)
    return FeedbackOut.model_validate(fb)
