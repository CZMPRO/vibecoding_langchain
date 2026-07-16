"""会话服务纯逻辑与隔离。"""

import pytest
from fastapi import HTTPException

from app.core.security import hash_password
from app.models.conversation import Conversation
from app.models.user import User
from app.services import chat_service


def _seed_user(db, username: str, role: str = "user") -> User:
    u = User(username=username, password_hash=hash_password("123456"), role=role)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def test_auto_title_from_question():
    assert chat_service.auto_title_from_question("短问") == "短问"
    long_q = "这是一个非常非常长的用户问题用来测试截断效果是否正确"
    title = chat_service.auto_title_from_question(long_q)
    assert len(title) <= 21
    assert title.endswith("…")


def test_parse_sources_valid_and_invalid():
    assert chat_service.parse_sources(None) == []
    assert chat_service.parse_sources("not-json") == []
    items = chat_service.parse_sources(
        '[{"filename":"a.md","content":"hello","score":0.9,"chunk_id":"1_0"}]'
    )
    assert len(items) == 1
    assert items[0].filename == "a.md"


def test_conversation_user_isolation(db_session):
    """用户 A 不能访问用户 B 的会话。"""
    a = _seed_user(db_session, "user_a")
    b = _seed_user(db_session, "user_b")
    conv_a = chat_service.create_conversation(db_session, a.id, "A的会话")
    chat_service.create_conversation(db_session, b.id, "B的会话")

    items_a, total_a = chat_service.list_conversations(db_session, a.id)
    assert total_a == 1
    assert items_a[0].title == "A的会话"

    with pytest.raises(HTTPException) as exc:
        chat_service.get_user_conversation(db_session, conv_a.id, b.id)
    assert exc.value.status_code == 404


def test_rename_and_delete_conversation(db_session):
    u = _seed_user(db_session, "user_c")
    conv = chat_service.create_conversation(db_session, u.id, "旧标题")
    renamed = chat_service.rename_conversation(db_session, conv.id, u.id, "新标题")
    assert renamed.title == "新标题"
    chat_service.delete_conversation(db_session, conv.id, u.id)
    left = db_session.query(Conversation).filter(Conversation.id == conv.id).first()
    assert left is None


def test_add_message_and_history(db_session):
    u = _seed_user(db_session, "user_d")
    conv = chat_service.create_conversation(db_session, u.id, "会话")
    chat_service.add_message(db_session, conv.id, "user", "你好")
    chat_service.add_message(db_session, conv.id, "assistant", "您好，请问需要什么帮助？")
    history = chat_service.get_recent_history(db_session, conv.id)
    assert len(history) == 2
    assert history[0]["role"] == "user"
