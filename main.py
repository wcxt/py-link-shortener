from typing import Annotated
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, HttpUrl, ValidationError

urls = {}
app = FastAPI()

templates = Jinja2Templates(directory="templates")

class ShortenFormData(BaseModel):
    url: HttpUrl

@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/{code_id}")
def redirect_code(code_id: int):
    if code_id not in urls:
        raise HTTPException(status_code=404, detail="Code not found")

    return RedirectResponse(urls[code_id], status_code=301)

@app.post("/code")
def shorten_url(request: Request, url: Annotated[str, Form()]):
    try:
        data = ShortenFormData(url=HttpUrl(url))
        code_id = len(urls) + 1
        urls[code_id] = data.url
        return templates.TemplateResponse(request=request, name="code.html",
                                          context={"code_id": code_id})
    except ValidationError:
        return templates.TemplateResponse(request=request, name="index.html",
                                          context={"error": "Invalid URL. Please enter a valid URL."})
