from contextlib import asynccontextmanager
from typing import Annotated
from fastapi import FastAPI, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, HttpUrl, ValidationError
from database import SessionDep, ShortenedURL 

app = FastAPI()

templates = Jinja2Templates(directory="templates")

class ShortenedURLCreate(BaseModel):
    url: HttpUrl

@app.exception_handler(status.HTTP_404_NOT_FOUND)
def http_not_found_exception_handler(request, exc):
    return templates.TemplateResponse(request=request, name="404_global.html",
                                      status_code=status.HTTP_404_NOT_FOUND)

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.post("/", response_class=HTMLResponse)
def shorten_url(request: Request, url: Annotated[str, Form()], session: SessionDep):
    try:
        data = ShortenedURLCreate.model_validate({"url": url})
    except ValidationError:
        return templates.TemplateResponse(request=request, name="index.html",
                                          context={"error": "Invalid URL. Please enter a valid URL."},
                                          status_code=status.HTTP_422_UNPROCESSABLE_CONTENT)

    short_url_db = ShortenedURL(url=str(data.url))
    session.add(short_url_db)
    session.commit()
    session.refresh(short_url_db)
    return templates.TemplateResponse(request=request, name="code.html",
                                      context={"code_id": short_url_db.id},
                                      status_code=status.HTTP_201_CREATED)

@app.get("/{code_id:int}", response_class=RedirectResponse, status_code=status.HTTP_301_MOVED_PERMANENTLY)
def redirect_code(request: Request, code_id: int, session: SessionDep):
    shortened_url = session.get(ShortenedURL, code_id)
    if not shortened_url:
        return templates.TemplateResponse(request=request, name="404.html",
                                          status_code=status.HTTP_404_NOT_FOUND)

    return shortened_url.url


