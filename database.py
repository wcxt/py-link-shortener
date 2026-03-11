from typing import Annotated
from fastapi import Depends
from sqlmodel import SQLModel, Session, create_engine, Field
from settings import settings
from nanoid import generate

CODE_SIZE=8

def generate_code():
    return generate(size=CODE_SIZE)

class ShortenedURL(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    code: str = Field(default_factory=generate_code, max_length=CODE_SIZE, unique=True, index=True)
    url: str = Field(max_length=2048)

engine = create_engine(str(settings.postgres_url), echo=True)

# This is a generator which will
# - 1. return new session with first .next()
# - 2. close session with second .next()
def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]
