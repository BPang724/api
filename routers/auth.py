import os
import secrets
from urllib.parse import urlsplit

from authlib.integrations.base_client.errors import OAuthError
from authlib.integrations.starlette_client import OAuth
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from core.db import get_db
from core.security import (
    ACCESS_TOKEN_COOKIE,
    create_access_token,
    get_current_member,
)
from models.member import Member
from repositories.members import upsert_google_member
from schemas.auth import MemberProfile

load_dotenv()

router = APIRouter(prefix="/auth", tags=["auth"])

oauth = OAuth()
google = oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


def _cookie_secure() -> bool:
    value = os.getenv("AUTH_COOKIE_SECURE", "true").lower()
    if value not in {"true", "false"}:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication cookie security setting is misconfigured.",
        )
    return value == "true"


def _validate_auth_configuration(request: Request) -> tuple[str, int]:
    if "session" not in request.scope:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OAuth session middleware is not configured.",
        )

    required_settings = (
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET",
        "GOOGLE_REDIRECT_URI",
        "JWT_SECRET_KEY",
        "SESSION_SECRET_KEY",
    )
    if any(not os.getenv(setting) for setting in required_settings):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google authentication is not configured on this server.",
        )

    jwt_secret = os.environ["JWT_SECRET_KEY"]
    session_secret = os.environ["SESSION_SECRET_KEY"]
    if len(jwt_secret) < 32 or len(session_secret) < 32:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication secrets must each be at least 32 characters.",
        )
    if jwt_secret.startswith("replace-with-") or session_secret.startswith("replace-with-"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Replace the example authentication secrets with random values.",
        )
    if jwt_secret == session_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="JWT and session secrets must be different.",
        )

    redirect_uri = os.environ["GOOGLE_REDIRECT_URI"]
    parsed_uri = urlsplit(redirect_uri)
    if (
        parsed_uri.scheme not in {"http", "https"}
        or not parsed_uri.netloc
        or parsed_uri.path.rstrip("/").split("/")[-3:] != ["auth", "google", "callback"]
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google callback URL must end in /api/auth/google/callback.",
        )

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

    _cookie_secure()
    return redirect_uri, expires_in


@router.get("/google/login")
async def google_login(request: Request):
    redirect_uri, _ = _validate_auth_configuration(request)
    nonce = secrets.token_urlsafe(32)
    return await google.authorize_redirect(request, redirect_uri, nonce=nonce)


@router.get("/google/callback", include_in_schema=False)
async def google_callback(request: Request, db: Session = Depends(get_db)):
    _validate_auth_configuration(request)
    try:
        token = await google.authorize_access_token(request)
    except OAuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google sign-in could not be completed. Please try again.",
        ) from exc

    userinfo = token.get("userinfo")
    if not userinfo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google did not return a verified identity.",
        )

    google_sub = userinfo.get("sub")
    email = userinfo.get("email")
    if (
        not isinstance(google_sub, str)
        or not google_sub
        or not isinstance(email, str)
        or not email
        or userinfo.get("email_verified") is not True
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="A verified Google email address is required.",
        )

    name = userinfo.get("name")
    picture = userinfo.get("picture")
    member = upsert_google_member(
        db,
        google_sub=google_sub,
        email=email,
        name=name if isinstance(name, str) else None,
        picture=picture if isinstance(picture, str) else None,
    )
    if not member.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been disabled.",
        )
    access_token, expires_in = create_access_token(member.id)

    success_url = os.getenv("AUTH_SUCCESS_REDIRECT_URL", "/")
    response = RedirectResponse(success_url, status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE,
        value=access_token,
        max_age=expires_in,
        httponly=True,
        secure=_cookie_secure(),
        samesite="lax",
        path="/",
    )
    response.headers["Cache-Control"] = "no-store"
    return response


@router.get("/me", response_model=MemberProfile)
def read_current_member(
    response: Response,
    member: Member = Depends(get_current_member),
) -> Member:
    response.headers["Cache-Control"] = "no-store"
    return member


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> Response:
    response.delete_cookie(
        key=ACCESS_TOKEN_COOKIE,
        httponly=True,
        secure=_cookie_secure(),
        samesite="lax",
        path="/",
    )
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
