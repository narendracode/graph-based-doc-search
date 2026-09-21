from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from api.config import get_settings
from api.db import get_db
from api.deps import get_current_user
from api.models.user import User
from api.schemas.auth import LoginRequest, MeResponse
from api.security import create_access_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()

COOKIE_NAME = "access_token"


@router.post("/login", response_model=MeResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> User:
    user = db.query(User).filter(User.username == payload.username).first()
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid username or password")

    token = create_access_token(user.id, user.role.value)
    response.set_cookie(
        COOKIE_NAME,
        token,
        httponly=True,
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
    )
    return user


@router.post("/logout")
def logout(response: Response) -> dict:
    response.delete_cookie(COOKIE_NAME)
    return {"ok": True}


@router.get("/me", response_model=MeResponse)
def me(user: User = Depends(get_current_user)) -> User:
    return user
