from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field, HttpUrl 
from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from database import SessionDep, ShortenedURL, User
from security import AccessTokenPublic, authenticate_user, get_hashed_password, create_access_token 

CODE_MAX_RETRY = 10

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

class ShortenedURLCreate(BaseModel):
    url: HttpUrl

class ShortenedURLPublic(BaseModel):
    url: HttpUrl
    short_code: str

class UserCreate(BaseModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=6, max_length=64)

class UserPublic(BaseModel):
    id: int
    email: str
    disabled: bool

@app.exception_handler(status.HTTP_404_NOT_FOUND)
def http_not_found_exception_handler(request, exc):
    return templates.TemplateResponse(request=request, name="404_global.html",
                                      status_code=status.HTTP_404_NOT_FOUND)

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/register", response_class=HTMLResponse)
def read_register(request: Request):
    return templates.TemplateResponse(request=request, name="register.html")

@app.get("/{code}", response_class=RedirectResponse, status_code=status.HTTP_301_MOVED_PERMANENTLY)
def redirect_code(request: Request, code: str, session: SessionDep):
    statement = select(ShortenedURL).where(ShortenedURL.code == code)
    results = session.exec(statement)
    shortened_url = results.first()
    if not shortened_url:
        return templates.TemplateResponse(request=request, name="404.html",
                                          status_code=status.HTTP_404_NOT_FOUND)

    return shortened_url.url

@app.post("/api/short", status_code=status.HTTP_201_CREATED, response_model=ShortenedURLPublic)
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

@app.post("/api/users", status_code=status.HTTP_201_CREATED, response_model=UserPublic)
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

@app.post("/api/token", response_model=AccessTokenPublic)
def create_access_token_from_login(form_body: Annotated[OAuth2PasswordRequestForm, Depends()], session: SessionDep):
    user = authenticate_user(session, form_body.username, form_body.password)
    if not user:
        # NOTE: detail key not followed by OAuth2 standards
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail={
                                "error": "invalid_grant",
                                "error_description": "Incorrect username or password"
                            })
    access_token = create_access_token({"sub": user.id})
    return AccessTokenPublic(access_token=access_token, token_type="Bearer")

