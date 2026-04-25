from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Response, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestFormStrict
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.models import ShortenedURL, User
from app.schemas import AccessTokenPublic, ShortenedURLCreate, ShortenedURLPublic, UserCreate, UserPublic
from app.core.database import SessionDep
from app.core.security import OAuth2PasswordException, authenticate_user, create_access_token, get_hashed_password
from app.core.settings import settings

CODE_MAX_RETRY = 10

router = APIRouter(prefix="/api")

@router.post("/short", status_code=status.HTTP_201_CREATED, response_model=ShortenedURLPublic)
def create_short_url(body: ShortenedURLCreate, session: SessionDep):
    for _ in range(CODE_MAX_RETRY):
        try:
            short_url_db = ShortenedURL(url=str(body.url))
            session.add(short_url_db)
            session.commit()
            session.refresh(short_url_db)
            return {"url": short_url_db.url, "short_code": short_url_db.code}
        except IntegrityError:
            session.rollback()

    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@router.post("/users", status_code=status.HTTP_201_CREATED, response_model=UserPublic)
def create_user(body: UserCreate, session: SessionDep):
    statement = select(User).where(User.email == body.email)
    results = session.exec(statement)
    user = results.first()

    if user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User with the same email already exists")

    hashed_password = get_hashed_password(body.password)
    user_db = User(email=body.email, password_hash=hashed_password)
    session.add(user_db)
    session.commit()
    session.refresh(user_db)

    return user_db

@router.post("/token", response_model=AccessTokenPublic)
def create_access_token_from_login(session: SessionDep,
                                   form_body: Annotated[OAuth2PasswordRequestFormStrict, Depends()],
                                   client_type: Annotated[str | None, Form()] = None):
    user = authenticate_user(session, form_body.username, form_body.password)
    if not user:
        raise OAuth2PasswordException("invalid_grant", description="Incorrect username or password")

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token({"sub": str(user.id)}, expires_delta=access_token_expires)
    response = JSONResponse(content=AccessTokenPublic(access_token=access_token, token_type="Bearer").model_dump())
    if client_type == "web":
        response.set_cookie(
            "access_token",
            access_token,
            max_age=access_token_expires.seconds,
            samesite="lax",
            secure=settings.cookie_secure,
            httponly=True,
        ) 

    return response

@router.delete("/token", status_code=status.HTTP_204_NO_CONTENT)
def delete_access_token_cookie(response: Response):
    response.delete_cookie("access_token")
    return None