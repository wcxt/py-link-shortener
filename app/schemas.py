from pydantic import BaseModel, EmailStr, Field, FutureDatetime, HttpUrl

class ShortenedURLCreate(BaseModel):
    url: HttpUrl
    expires_at: FutureDatetime | None = None

class ShortenedURLPublic(BaseModel):
    url: HttpUrl
    short_code: str
    expires_at: FutureDatetime | None = None

class UserCreate(BaseModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=6, max_length=64)

class UserPublic(BaseModel):
    id: int
    email: str
    disabled: bool

class AccessTokenPublic(BaseModel):
    access_token: str
    token_type: str