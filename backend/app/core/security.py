"""密码哈希与 JWT 签发/校验。"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

# bcrypt 用于密码「单向加密」——只能验证，不能反推明文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """把明文密码变成哈希字符串再入库。"""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """登录时比对明文与库里的哈希是否匹配。"""
    return pwd_context.verify(plain, hashed)


def create_access_token(subject: str, extra: Optional[Dict[str, Any]] = None) -> str:
    """签发访问令牌（门禁卡），前端后续请求要带上它。"""
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload: Dict[str, Any] = {"sub": subject, "exp": expire}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> Dict[str, Any]:
    """解析令牌；失败则抛 JWTError。"""
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


def safe_decode_token(token: str) -> Optional[Dict[str, Any]]:
    """解析令牌，失败返回 None。"""
    try:
        return decode_access_token(token)
    except JWTError:
        return None
