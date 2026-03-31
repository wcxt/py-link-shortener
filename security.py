from datetime import timedelta, datetime, timezone
from typing import Any
from fastapi import HTTPException, status
import jwt
from sqlmodel import Session, select
from database import User
from settings import settings

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

def get_current_user(session: Session, token: str) -> User:
    credential_error = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    try:
        decoded = decode_access_token(token)
    except jwt.InvalidTokenError:
        raise credential_error

    subject = decoded.get("sub")
    if subject is None or not isinstance(subject, str):
        raise credential_error

    try:
        user_id = int(subject)
    except ValueError:
        raise credential_error

    statement = select(User).where(User.id == user_id)
    results = session.exec(statement)
    user = results.first()
    if not user:
        raise credential_error

    return user

def get_current_enabled_user(session: Session, token: str) -> User:
    user = get_current_user(session, token)
    if user.disabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Disabled user")
    return user


