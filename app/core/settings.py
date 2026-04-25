from fastapi.templating import Jinja2Templates
from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    jwt_secret: str = Field(min_length=32) 
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=30, ge=0)
    cookie_secure: bool = True

    postgres_url: PostgresDsn

    @field_validator("postgres_url", mode='after')
    @classmethod
    def is_db(cls, postgres_url: PostgresDsn):
        path = postgres_url.path or ""
        db_name = path.lstrip("/")
        if not db_name:
            raise ValueError("Postgres URL must include a database name")
        return postgres_url

    model_config = SettingsConfigDict(env_file=".env") # pyright: ignore[reportUnannotatedClassAttribute]

settings = Settings() # pyright:ignore[reportCallIssue]

templates = Jinja2Templates(directory="app/templates")


