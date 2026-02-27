from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

urls = {}
app = FastAPI()

class CodeCreate(BaseModel):
    url: str

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/code")
def shorten_url(body: CodeCreate):
    code_id = len(urls) + 1
    urls[code_id] = body.url
    return {"id": code_id}

@app.get("/code/{code_id}")
def read_code(code_id: int):
    if code_id not in urls:
        raise HTTPException(status_code=404, detail="Code not found")

    return {"url": urls[code_id]}
