from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl

urls = {}
app = FastAPI()

class CodeCreate(BaseModel):
    url: HttpUrl

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/{code_id}")
def redirect_code(code_id: int):
    if code_id not in urls:
        raise HTTPException(status_code=404, detail="Code not found")

    return RedirectResponse(urls[code_id], status_code=301)

@app.post("/code")
def shorten_url(body: CodeCreate):
    code_id = len(urls) + 1
    urls[code_id] = body.url
    return {"id": code_id}
