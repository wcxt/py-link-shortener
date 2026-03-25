from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl 
from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from database import SessionDep, ShortenedURL 

CODE_MAX_RETRY = 10

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

class ShortenedURLCreate(BaseModel):
    url: HttpUrl

class ShortenedURLPublic(BaseModel):
    url: HttpUrl
    short_code: str

@app.exception_handler(status.HTTP_404_NOT_FOUND)
def http_not_found_exception_handler(request, exc):
    return templates.TemplateResponse(request=request, name="404_global.html",
                                      status_code=status.HTTP_404_NOT_FOUND)

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

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

