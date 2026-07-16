"""鉴权工具：密码哈希与 JWT。"""

from app.core.security import (
    create_access_token,
    hash_password,
    safe_decode_token,
    verify_password,
)


def test_hash_and_verify_password():
    """正确密码能通过，错误密码不能通过。"""
    hashed = hash_password("123456")
    assert hashed != "123456"
    assert verify_password("123456", hashed) is True
    assert verify_password("wrong", hashed) is False


def test_create_and_decode_token():
    """签发的令牌能解析出用户 id 与角色。"""
    token = create_access_token("42", extra={"role": "admin", "username": "admin"})
    payload = safe_decode_token(token)
    assert payload is not None
    assert payload["sub"] == "42"
    assert payload["role"] == "admin"


def test_invalid_token_returns_none():
    """伪造令牌应安全失败。"""
    assert safe_decode_token("not.a.real.token") is None
