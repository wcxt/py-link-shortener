from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import status
from sqlmodel import select

from app.core.database import SessionDep
from app.models import ShortenedURL
from app.settings import templates

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@router.get("/register", response_class=HTMLResponse)
def read_register(request: Request):
    return templates.TemplateResponse(request=request, name="register.html")

@router.get("/login", response_class=HTMLResponse)
def read_login(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")

@router.get("/{code}", response_class=RedirectResponse, status_code=status.HTTP_301_MOVED_PERMANENTLY)
def redirect_code(request: Request, code: str, session: SessionDep):
    statement = select(ShortenedURL).where(ShortenedURL.code == code)
    results = session.exec(statement)
    shortened_url = results.first()
    if not shortened_url:
        return templates.TemplateResponse(request=request, name="404.html",
                                          status_code=status.HTTP_404_NOT_FOUND)

    return shortened_url.url