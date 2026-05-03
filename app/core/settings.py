from fastapi.templating import Jinja2Templates
from pydantic import Field, PostgresDsn, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    jwt_secret: str = Field(min_length=32) 
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=30, ge=0)
    cookie_secure: bool = True

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_db: str = "postgres"

    @property
    def postgres_url(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql+psycopg2",
            host=self.postgres_host,
            port=self.postgres_port,
            username=self.postgres_user,
            password=self.postgres_password,
            path=self.postgres_db
        )

    model_config = SettingsConfigDict(env_file=".env") # pyright: ignore[reportUnannotatedClassAttribute]

settings = Settings() # pyright:ignore[reportCallIssue]

templates = Jinja2Templates(directory="app/templates")


