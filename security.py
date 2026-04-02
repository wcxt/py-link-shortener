from datetime import timedelta, datetime, timezone
from typing import Annotated, Any
from fastapi import Depends, HTTPException, status
import jwt
from pwdlib import PasswordHash
from pydantic import BaseModel
from sqlmodel import Session, select
from database import SessionDep, User
from settings import settings
from fastapi.security import OAuth2PasswordBearer

class AccessTokenPublic(BaseModel):
    access_token: str
    token_type: str

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token")

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

def get_current_user(session: SessionDep, token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    credential_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )

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

def get_current_enabled_user(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.disabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Disabled user")
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



