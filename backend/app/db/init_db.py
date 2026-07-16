"""建表并确保默认管理员存在。"""

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.session import Base, SessionLocal, engine
from app.models import Conversation, Document, Message, MessageFeedback, User  # noqa: F401


def init_db() -> None:
    """创建数据目录、建表、初始化 admin。"""
    settings = get_settings()
    settings.data_path.mkdir(parents=True, exist_ok=True)
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.chroma_dir.mkdir(parents=True, exist_ok=True)

    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == settings.admin_username).first()
        if not admin:
            admin = User(
                username=settings.admin_username,
                password_hash=hash_password(settings.admin_password),
                role="admin",
            )
            db.add(admin)
            db.commit()
            print(f"[init] 已创建管理员账号: {settings.admin_username}")
        else:
            print(f"[init] 管理员已存在: {settings.admin_username}")
    finally:
        db.close()
