"""pytest 公共夹具：临时数据库与测试客户端，不污染业务 data/app.db。"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# 测试环境变量：在导入 app 前设置
os.environ.setdefault("JWT_SECRET", "unit-test-secret-key-not-for-production")
os.environ.setdefault("ADMIN_USERNAME", "admin")
os.environ.setdefault("ADMIN_PASSWORD", "123456")
os.environ.setdefault("EMBEDDING_PROVIDER", "local")
os.environ.setdefault("OPENAI_API_KEY", "sk-test-placeholder")
os.environ.setdefault("OPENAI_BASE_URL", "http://127.0.0.1:9/v1")
os.environ.setdefault("OPENAI_CHAT_MODEL", "test-model")


@pytest.fixture()
def temp_data_dir(tmp_path: Path) -> Path:
    """每个用例独立的数据目录。"""
    data = tmp_path / "data"
    (data / "uploads").mkdir(parents=True)
    (data / "chroma").mkdir(parents=True)
    return data


@pytest.fixture()
def db_session(temp_data_dir: Path):
    """内存 SQLite 会话（StaticPool 保证同连接）。"""
    from app.db.session import Base
    from app.models import Conversation, Document, Message, MessageFeedback, User  # noqa: F401

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def client(temp_data_dir: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    """带临时库的 FastAPI 测试客户端。"""
    from app.core.config import get_settings
    from app.core.security import hash_password
    from app.db.session import Base, get_db
    from app.main import create_app
    from app.models.user import User
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    get_settings.cache_clear()

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    # 指向临时上传目录
    settings = get_settings()
    monkeypatch.setattr(settings, "data_dir", str(temp_data_dir))

    def _override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db

    # 手动写入 admin（不走 lifespan 里的真实 init 路径）
    db = TestingSessionLocal()
    try:
        if not db.query(User).filter(User.username == "admin").first():
            db.add(
                User(
                    username="admin",
                    password_hash=hash_password("123456"),
                    role="admin",
                )
            )
            db.commit()
    finally:
        db.close()

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    get_settings.cache_clear()
