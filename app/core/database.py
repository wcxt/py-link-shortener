from typing import Annotated
from fastapi import Depends
from sqlmodel import Session, create_engine
from app.core.settings import settings
import app.models

engine = create_engine(str(settings.postgres_url), echo=True)

# This is a generator which will
# - 1. return new session with first .next()
# - 2. close session with second .next()
def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]
