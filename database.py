from typing import Annotated
from fastapi import Depends
from sqlmodel import SQLModel, Session, create_engine, Field
from settings import settings

class ShortenedURL(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    url: str = Field(max_length=2048)

engine = create_engine(str(settings.postgres_url), echo=True)

# This is a generator which will
# - 1. return new session with first .next()
# - 2. close session with second .next()
def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]
