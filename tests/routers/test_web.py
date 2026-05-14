from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models import ShortenedURL
from tests.conftest import TEST_URL


def test_redirect_code(session: Session, client: TestClient):
    test_short_url = ShortenedURL(url=TEST_URL)
    session.add(test_short_url)
    session.commit()
    session.refresh(test_short_url)

    response = client.get(f"/{test_short_url.code}", follow_redirects=False)

    assert response.status_code == 301
    assert response.headers["location"] == TEST_URL

def test_redirect_code_expired(session: Session, client: TestClient):
    test_short_url = ShortenedURL(url=TEST_URL, expires_at=datetime.now() - timedelta(1))
    session.add(test_short_url)
    session.commit()
    session.refresh(test_short_url)

    response = client.get(f"/{test_short_url.code}", follow_redirects=False)

    assert response.status_code == 410
    assert "text/html" in response.headers["content-type"]

def test_redirect_code_not_found(client: TestClient):
    response = client.get(f"/1a2b3c4d", follow_redirects=False)

    assert response.status_code == 404
    assert "text/html" in response.headers["content-type"]

def test_read_root(client: TestClient):
    response = client.get("/")

    assert response.status_code == 200 
    assert "text/html" in response.headers["content-type"]

def test_read_register(client: TestClient):
    response = client.get("/register")

    assert response.status_code == 200 
    assert "text/html" in response.headers["content-type"]

def test_read_login(client: TestClient):
    response = client.get("/login")

    assert response.status_code == 200 
    assert "text/html" in response.headers["content-type"]

def test_read_dashboard(client: TestClient, auth: dict):
    response = client.get("/dashboard", headers={"Authorization": f"Bearer {auth['token']}"})

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

def test_read_dashboard_unauthenticated(client: TestClient):
    response = client.get("/dashboard")

    data = response.json()

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert data["detail"] is not None