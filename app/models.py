from datetime import datetime

from nanoid import generate
from sqlalchemy import Column
from sqlmodel import Field, Relationship, SQLModel, DateTime

CODE_SIZE=8

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(max_length=255, unique=True, index=True)
    password_hash: str = Field(max_length=255)
    disabled: bool = Field(default=False)

    shortened_urls: list["ShortenedURL"] = Relationship(back_populates="owner")

def generate_code():
    return generate(size=CODE_SIZE)

class ShortenedURL(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    code: str = Field(default_factory=generate_code, max_length=CODE_SIZE, unique=True, index=True)
    url: str = Field(max_length=2048)
    expires_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))

    owner_id: int | None = Field(default=None, foreign_key="user.id")
    owner: User | None = Relationship(back_populates="shortened_urls")