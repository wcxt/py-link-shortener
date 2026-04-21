from fastapi import Request, status
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.responses import JSONResponse

from app.settings import templates

class OAuth2PasswordException(Exception):
    def __init__(self, error: str, description: str | None = None) -> None:
        super().__init__(description)
        self.error = error
        self.description = description

def http_not_found_exception_handler(request: Request, exc: HTTPException):
    return templates.TemplateResponse(request=request, name="404_global.html",
                                      status_code=status.HTTP_404_NOT_FOUND)

async def oauth2_password_exception_handler(_request: Request, exc: OAuth2PasswordException):
    status_code = status.HTTP_400_BAD_REQUEST
    headers = {}
    body = {"error": exc.error}

    if exc.error == "invalid_token":
        status_code = status.HTTP_401_UNAUTHORIZED
        headers = {"WWW-Authenticate": f'Bearer error="{exc.error}"'}
        if exc.description:
            headers["WWW-Authenticate"] += f', error_description="{exc.description}"'

    if exc.description:
        body["error_description"] = exc.description

    return JSONResponse(
        content=body,
        status_code=status_code,
        headers=headers
    )

async def custom_request_validation_error_handler(request: Request, exc: RequestValidationError):
    print(exc)
    if request.url.path == "/api/token":
        return await oauth2_password_exception_handler(request, OAuth2PasswordException("invalid_request"))
    return await request_validation_exception_handler(request, exc)
