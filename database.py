from typing import Annotated
from fastapi import Depends
from sqlmodel import SQLModel, Session, create_engine
from settings import settings

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
