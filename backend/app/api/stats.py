"""管理员简易运营统计。"""

from datetime import datetime, timezone

from sqlalchemy import func

from app.core.deps import AdminUser, DbSession
from app.models.conversation import Conversation
from app.models.document import Document
from app.models.message import Message
from app.models.user import User
from app.schemas.kb import StatsOut
from fastapi import APIRouter

router = APIRouter(prefix="/stats", tags=["统计"])


@router.get("/overview", response_model=StatsOut)
def overview(admin: AdminUser, db: DbSession) -> StatsOut:
    user_count = db.query(func.count(User.id)).scalar() or 0
    document_count = db.query(func.count(Document.id)).scalar() or 0
    ready_document_count = (
        db.query(func.count(Document.id)).filter(Document.status == "ready").scalar() or 0
    )
    conversation_count = db.query(func.count(Conversation.id)).scalar() or 0
    message_count = db.query(func.count(Message.id)).scalar() or 0

    # 今日问答：今天创建的 user 角色消息数
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_qa_count = (
        db.query(func.count(Message.id))
        .filter(Message.role == "user", Message.created_at >= today_start)
        .scalar()
        or 0
    )

    return StatsOut(
        user_count=user_count,
        document_count=document_count,
        ready_document_count=ready_document_count,
        conversation_count=conversation_count,
        message_count=message_count,
        today_qa_count=today_qa_count,
    )
