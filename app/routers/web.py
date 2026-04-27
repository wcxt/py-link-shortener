from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import status
from sqlmodel import select

from app.core.database import SessionDep
from app.core.security import get_current_enabled_user_optional
from app.models import ShortenedURL, User
from app.core.settings import templates

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
def read_root(request: Request, current_user: Annotated[User | None, Depends(get_current_enabled_user_optional)]):
    return templates.TemplateResponse(request=request, name="index.html", context={"current_user": current_user})

@router.get("/register", response_class=HTMLResponse)
def read_register(request: Request, current_user: Annotated[User | None, Depends(get_current_enabled_user_optional)]):
    return templates.TemplateResponse(request=request, name="register.html", context={"current_user": current_user})

@router.get("/login", response_class=HTMLResponse)
def read_login(request: Request, current_user: Annotated[User | None, Depends(get_current_enabled_user_optional)]):
    return templates.TemplateResponse(request=request, name="login.html", context={"current_user": current_user})

@router.get("/{code}", response_class=RedirectResponse, status_code=status.HTTP_301_MOVED_PERMANENTLY)
def redirect_code(request: Request, code: str, session: SessionDep):
    statement = select(ShortenedURL).where(ShortenedURL.code == code)
    results = session.exec(statement)
    shortened_url = results.first()
    if not shortened_url:
        return templates.TemplateResponse(request=request, name="404.html",
                                          status_code=status.HTTP_404_NOT_FOUND)

    return shortened_url.url