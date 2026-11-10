import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.db import get_db
from models.member import Member

ACCESS_TOKEN_COOKIE = "autoutline_access_token"
JWT_ISSUER = "autoutline-api"
bearer_scheme = HTTPBearer(auto_error=False, scheme_name="JWTBearer")


def _jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET_KEY", "")
    session_secret = os.getenv("SESSION_SECRET_KEY", "")
    if (
        len(secret) < 32
        or secret.startswith("replace-with-")
        or secret == session_secret
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured on this server.",
        )
    return secret


def create_access_token(member_id: int) -> tuple[str, int]:
    try:
        expires_in = int(os.getenv("ACCESS_TOKEN_EXPIRE_SECONDS", "28800"))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication token lifetime is misconfigured.",
        ) from exc
    if expires_in <= 0:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication token lifetime is misconfigured.",
        )

    now = datetime.now(timezone.utc)
    claims = {
        "sub": str(member_id),
        "iss": JWT_ISSUER,
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
    }
    return jwt.encode(claims, _jwt_secret(), algorithm="HS256"), expires_in


def get_authenticated_member_id(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> int:
    if credentials is not None:
        token = credentials.credentials
    elif request.headers.get("authorization"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    else:
        token = request.cookies.get(ACCESS_TOKEN_COOKIE)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        claims = jwt.decode(
            token,
            _jwt_secret(),
            algorithms=["HS256"],
            issuer=JWT_ISSUER,
            options={"require": ["exp", "iat", "iss", "sub"]},
        )
        subject = claims["sub"]
        if not isinstance(subject, str) or not subject.isdecimal() or len(subject) > 19:
            raise ValueError("Invalid member ID")
        member_id = int(subject)
    except (jwt.InvalidTokenError, TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    if member_id <= 0 or member_id > 9_223_372_036_854_775_807:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return member_id


def get_current_member(
    member_id: int = Depends(get_authenticated_member_id),
    db: Session = Depends(get_db),
) -> Member:
    member = db.scalar(
        select(Member).where(
            Member.id == member_id,
            Member.is_active.is_(True),
            Member.email_verified.is_(True),
        )
    )
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The account is no longer active.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return member
