"""注册、登录、改密、当前用户信息。"""

from fastapi import APIRouter, HTTPException, Request, status

from app.core.deps import CurrentUser, DbSession
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    TokenResponse,
    UserOut,
)
from app.utils.rate_limit import limiter

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=TokenResponse)
def register(body: RegisterRequest, db: DbSession, request: Request) -> TokenResponse:
    """普通用户注册。"""
    client = request.client.host if request.client else "unknown"
    limiter.check(f"register:{client}", limit=10, window_seconds=60)

    username = body.username.strip()
    if username.lower() == "admin":
        raise HTTPException(status_code=400, detail="不能注册保留用户名 admin")

    exists = db.query(User).filter(User.username == username).first()
    if exists:
        raise HTTPException(status_code=400, detail="用户名已存在")

    user = User(username=username, password_hash=hash_password(body.password), role="user")
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(str(user.id), extra={"role": user.role, "username": user.username})
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: DbSession, request: Request) -> TokenResponse:
    """用户登录，返回 JWT。"""
    client = request.client.host if request.client else "unknown"
    limiter.check(f"login:{client}", limit=20, window_seconds=60)

    user = db.query(User).filter(User.username == body.username.strip()).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")

    token = create_access_token(str(user.id), extra={"role": user.role, "username": user.username})
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser) -> UserOut:
    """获取当前登录用户信息。"""
    return UserOut.model_validate(user)


@router.post("/change-password", response_model=MessageResponse)
def change_password(body: ChangePasswordRequest, user: CurrentUser, db: DbSession) -> MessageResponse:
    """修改密码。"""
    if not verify_password(body.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="原密码不正确")
    user.password_hash = hash_password(body.new_password)
    db.add(user)
    db.commit()
    return MessageResponse(message="密码修改成功，请使用新密码重新登录")
