from contextlib import asynccontextmanager
from typing import Annotated
from fastapi import Depends, FastAPI, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, HttpUrl, PostgresDsn, ValidationError, field_validator
from sqlmodel import Session, create_engine, SQLModel
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    postgres_url: PostgresDsn

    @field_validator("postgres_url", mode='after')
    @classmethod
    def is_db(cls, postgres_url: PostgresDsn):
        path = postgres_url.path or ""
        db_name = path.lstrip("/")
        if not db_name:
            raise ValueError("Postgres URL must include a database name")
        return postgres_url

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings() # type: ignore

engine = create_engine(str(settings.postgres_url))

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# This is a generator which will
# - 1. return new session with first .next()
# - 2. close session with second .next()
def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

# This is just a function which is essentialy a python context manager but async
# We can use it like this: async with lifespan(app): 
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

urls = {}
app = FastAPI(lifespan=lifespan)

templates = Jinja2Templates(directory="templates")

class ShortenFormData(BaseModel):
    url: HttpUrl

@app.exception_handler(status.HTTP_404_NOT_FOUND)
def http_not_found_exception_handler(request, exc):
    return templates.TemplateResponse(request=request, name="404_global.html",
                                      status_code=status.HTTP_404_NOT_FOUND)

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.post("/", response_class=HTMLResponse)
def shorten_url(request: Request, url: Annotated[str, Form()]):
    try:
        data = ShortenFormData(url=HttpUrl(url))
        code_id = len(urls) + 1
        urls[code_id] = data.url
        return templates.TemplateResponse(request=request, name="code.html",
                                          context={"code_id": code_id},
                                          status_code=status.HTTP_201_CREATED)
    except ValidationError:
        return templates.TemplateResponse(request=request, name="index.html",
                                          context={"error": "Invalid URL. Please enter a valid URL."},
                                          status_code=status.HTTP_422_UNPROCESSABLE_CONTENT)

@app.get("/{code_id:int}", response_class=RedirectResponse, status_code=status.HTTP_301_MOVED_PERMANENTLY)
def redirect_code(request: Request, code_id: int):
    if code_id not in urls:
        return templates.TemplateResponse(request=request, name="404.html",
                                          status_code=status.HTTP_404_NOT_FOUND)

    return urls[code_id]


