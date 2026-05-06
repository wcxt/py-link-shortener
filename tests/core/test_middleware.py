from fastapi.testclient import TestClient
from httpx import patch


def test_rate_limit_middleware(client: TestClient):
    for _ in range(100):
        response = client.get("/")

    assert response.status_code == 429
    assert response.json() == {"detail": "Too many requests"}