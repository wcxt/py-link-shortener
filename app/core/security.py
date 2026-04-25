from datetime import timedelta, datetime, timezone
from typing import Annotated, Any
from fastapi import Cookie, Depends, HTTPException, status
import jwt
from pwdlib import PasswordHash
from sqlmodel import Session, select
from app.core.database import SessionDep
from app.core.exceptions import OAuth2PasswordException
from app.models import User
from app.core.settings import settings
from fastapi.security import OAuth2PasswordBearer

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token", auto_error=False)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)

def get_hashed_password(plain_password: str) -> str:
    return password_hash.hash(plain_password)

def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expires = datetime.now(timezone.utc) + expires_delta
    else:
        expires = datetime.now(timezone.utc) + timedelta(minutes=30)
    to_encode.update({"exp": expires})
    encoded = jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return encoded

def decode_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])

def get_token_from_cookie_or_header(header_token: Annotated[str | None, Depends(oauth2_scheme)], access_token: Annotated[str | None, Cookie()]) -> str:
    if access_token:
        return access_token
    if header_token:
        return header_token
    raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
    )

def get_current_user(session: SessionDep, token: Annotated[str, Depends(get_token_from_cookie_or_header)]) -> User:
    try:
        decoded = decode_access_token(token)
    except jwt.InvalidTokenError:
        raise OAuth2PasswordException("invalid_token")

    subject = decoded.get("sub")
    if subject is None or not isinstance(subject, str):
        raise OAuth2PasswordException("invalid_token")

    try:
        user_id = int(subject)
    except ValueError:
        raise OAuth2PasswordException("invalid_token")

    statement = select(User).where(User.id == user_id)
    results = session.exec(statement)
    user = results.first()
    if not user:
        raise OAuth2PasswordException("invalid_token")

    return user

def get_current_enabled_user(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.disabled:
        raise OAuth2PasswordException("invalid_token", description="User is disabled")
    return user

def authenticate_user(session: Session, email: str, password: str) -> User | None:
    statement = select(User).where(User.email == email)
    results = session.exec(statement)
    user = results.first()
    if not user:
        return None

    if user.disabled:
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user



