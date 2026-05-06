from fastapi.testclient import TestClient
from httpx import patch


def test_rate_limit_middleware(client: TestClient):
    for _ in range(100):
        response = client.get("/")

    assert response.status_code == 429
    assert response.json() == {"detail": "Too many requests"}

def test_rate_limit_middleware_different_paths(client: TestClient):
    for _ in range(10):
        response = client.post("/api/token", data={"grant_type": "password", "username": "test", "password": "test"})
    assert response.status_code == 429
    assert response.json() == {"detail": "Too many requests"}