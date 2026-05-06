import time

from fastapi import Request, status
from fastapi.responses import JSONResponse

RATE_LIMIT = 60
WINDOW_DURATION = 60

clients: dict[str, list] = {}

async def rate_limit_middleware(request: Request, call_next):
        ip = request.client.host
        now = time.time()

        if ip not in clients:
            clients[ip] = []

        clients[ip] = [t for t in clients[ip] if now - t <= WINDOW_DURATION]

        if len(clients[ip]) >= RATE_LIMIT:
            return JSONResponse(status_code=status.HTTP_429_TOO_MANY_REQUESTS, content={"detail": "Too many requests"})

        clients[ip].append(now)
        return await call_next(request)

