"""问答反馈：点赞 / 点踩。"""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint

from app.db.session import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MessageFeedback(Base):
    __tablename__ = "message_feedback"
    __table_args__ = (UniqueConstraint("message_id", "user_id", name="uq_feedback_msg_user"),)

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1 赞 / -1 踩
    comment = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
