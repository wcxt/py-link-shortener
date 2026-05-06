from curses import window
import time

from fastapi import Request, status
from fastapi.responses import JSONResponse

def get_rate_limit_parameters(path: str, method: str) -> tuple[int, int]:
    if path == "/api/short" and method == "POST":
        return 10, 60
    elif path == "/api/token" and method == "POST":
        return 5, 60 
    elif path == "/api/users" and method == "POST":
        return 5, 60
    return 60, 60

clients: dict[str, list] = {}

async def rate_limit_middleware(request: Request, call_next):
        ip = request.client.host
        now = time.time()
        print(f"Received request from {ip} to {request.url.path} with method {request.method}")
        rate_limit, window_duration = get_rate_limit_parameters(request.url.path, request.method)

        if ip not in clients:
            clients[ip] = []

        clients[ip] = [t for t in clients[ip] if now - t <= window_duration]

        if len(clients[ip]) >= rate_limit:
            return JSONResponse(status_code=status.HTTP_429_TOO_MANY_REQUESTS, content={"detail": "Too many requests"})

        clients[ip].append(now)
        return await call_next(request)

