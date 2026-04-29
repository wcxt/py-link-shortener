from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.security import get_hashed_password
from app.models import ShortenedURL, User
from tests.conftest import TEST_EMAIL, TEST_PASSWORD, TEST_URL


def test_redirect_code(session: Session, client: TestClient):
    test_short_url = ShortenedURL(url=TEST_URL)
    session.add(test_short_url)
    session.commit()
    session.refresh(test_short_url)

    response = client.get(f"/{test_short_url.code}", follow_redirects=False)

    assert response.status_code == 301
    assert response.headers["location"] == TEST_URL

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

def test_read_dashboard(session: Session, client: TestClient):
    test_user = User(email=TEST_EMAIL, password_hash=get_hashed_password(TEST_PASSWORD))
    session.add(test_user)
    session.commit()
    session.refresh(test_user)

    response = client.post(
            "/api/token",
            data={"grant_type": "password", "username": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    data = response.json()
    access_token = data["access_token"]

    response = client.get("/dashboard", headers={"Authorization": f"Bearer {access_token}"})

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

def test_read_dashboard_unauthenticated(client: TestClient):
    response = client.get("/dashboard")

    data = response.json()

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert data["detail"] is not None