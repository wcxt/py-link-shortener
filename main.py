from typing import Annotated
from fastapi import FastAPI, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, HttpUrl, ValidationError

urls = {}
app = FastAPI()

templates = Jinja2Templates(directory="templates")

class ShortenFormData(BaseModel):
    url: HttpUrl

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.post("/", response_class=HTMLResponse)
def shorten_url(request: Request, url: Annotated[str, Form()]):
    try:
        data = ShortenFormData(url=HttpUrl(url))
        code_id = len(urls) + 1
        urls[code_id] = data.url
        return templates.TemplateResponse(request=request, name="code.html",
                                          context={"code_id": code_id},
                                          status_code=status.HTTP_201_CREATED)
    except ValidationError:
        return templates.TemplateResponse(request=request, name="index.html",
                                          context={"error": "Invalid URL. Please enter a valid URL."},
                                          status_code=status.HTTP_422_UNPROCESSABLE_CONTENT)

@app.get("/{code_id:int}", response_class=RedirectResponse, status_code=status.HTTP_301_MOVED_PERMANENTLY)
def redirect_code(request: Request, code_id: int):
    if code_id not in urls:
        return templates.TemplateResponse(request=request, name="404.html",
                                          status_code=status.HTTP_404_NOT_FOUND)

    return urls[code_id]


