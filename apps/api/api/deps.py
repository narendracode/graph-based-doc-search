import uuid
from collections.abc import Generator

import jwt
from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.db import get_db
from api.models.user import User, UserRole
from api.security import decode_access_token


def get_current_user(
    access_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not access_token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    try:
        payload = decode_access_token(access_token)
    except jwt.PyJWTError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token") from exc

    user = db.get(User, uuid.UUID(payload["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found or inactive")
    return user


def require_super_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.super_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Super admin access required")
    return user
