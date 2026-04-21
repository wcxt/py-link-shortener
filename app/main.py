from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles

from app.core.exceptions import OAuth2PasswordException, custom_request_validation_error_handler, http_not_found_exception_handler, oauth2_password_exception_handler
from app.routers import api, web

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.add_exception_handler(status.HTTP_404_NOT_FOUND, http_not_found_exception_handler)
app.add_exception_handler(OAuth2PasswordException, oauth2_password_exception_handler)
app.add_exception_handler(RequestValidationError, custom_request_validation_error_handler)

app.include_router(web.router)
app.include_router(api.router)




