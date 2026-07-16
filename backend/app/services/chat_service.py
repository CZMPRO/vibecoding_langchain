"""会话与消息业务逻辑。"""

import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas.chat import MessageOut, SourceItem


def get_user_conversation(db: Session, conversation_id: int, user_id: int) -> Conversation:
    conv = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == user_id)
        .first()
    )
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")
    return conv


def create_conversation(db: Session, user_id: int, title: str = "新会话") -> Conversation:
    conv = Conversation(user_id=user_id, title=title or "新会话")
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def list_conversations(
    db: Session, user_id: int, page: int = 1, page_size: int = 20
) -> Tuple[List[Conversation], int]:
    q = db.query(Conversation).filter(Conversation.user_id == user_id)
    total = q.count()
    items = (
        q.order_by(Conversation.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total


def rename_conversation(db: Session, conversation_id: int, user_id: int, title: str) -> Conversation:
    conv = get_user_conversation(db, conversation_id, user_id)
    conv.title = title
    conv.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(conv)
    return conv


def delete_conversation(db: Session, conversation_id: int, user_id: int) -> None:
    conv = get_user_conversation(db, conversation_id, user_id)
    db.delete(conv)
    db.commit()


def list_messages(
    db: Session, conversation_id: int, user_id: int, page: int = 1, page_size: int = 100
) -> Tuple[List[Message], int]:
    get_user_conversation(db, conversation_id, user_id)
    q = db.query(Message).filter(Message.conversation_id == conversation_id)
    total = q.count()
    items = (
        q.order_by(Message.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total


def parse_sources(sources_json: Optional[str]) -> List[SourceItem]:
    if not sources_json:
        return []
    try:
        data = json.loads(sources_json)
        return [SourceItem(**item) for item in data]
    except Exception:  # noqa: BLE001
        return []


def message_to_out(msg: Message) -> MessageOut:
    return MessageOut(
        id=msg.id,
        conversation_id=msg.conversation_id,
        role=msg.role,
        content=msg.content,
        sources=parse_sources(msg.sources_json),
        created_at=msg.created_at,
    )


def get_recent_history(db: Session, conversation_id: int) -> List[Dict[str, str]]:
    """取最近若干轮对话，供 RAG 上下文使用。"""
    settings = get_settings()
    limit = max(settings.history_turns * 2, 2)
    rows = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.id.desc())
        .limit(limit)
        .all()
    )
    rows = list(reversed(rows))
    return [{"role": m.role, "content": m.content} for m in rows if m.role in ("user", "assistant")]


def auto_title_from_question(question: str) -> str:
    q = question.strip().replace("\n", " ")
    return q[:20] + ("…" if len(q) > 20 else "")


def add_message(
    db: Session,
    conversation_id: int,
    role: str,
    content: str,
    sources_json: Optional[str] = None,
) -> Message:
    msg = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        sources_json=sources_json,
    )
    db.add(msg)
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if conv:
        conv.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(msg)
    return msg
