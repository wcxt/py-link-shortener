from re import S

from fastapi.testclient import TestClient
from pytest import Session
from sqlmodel import select

from app.core.security import decode_access_token, get_hashed_password, verify_password
from app.models import ShortenedURL, User
from tests.conftest import TEST_EMAIL, TEST_PASSWORD, TEST_URL


def test_create_short_url(client: TestClient):
    response = client.post(
            "/api/short",
            json={"url": TEST_URL}
    )
    data = response.json()

    assert response.status_code == 201
    assert data["short_code"] is not None
    assert isinstance(data["short_code"], str)
    assert len(data["short_code"]) == 8 
    assert data["url"] == TEST_URL

def test_create_short_url_persists(session: Session, client: TestClient):
    response = client.post(
            "/api/short",
            json={"url": TEST_URL}
    )
    data = response.json()
    statement = select(ShortenedURL).where(ShortenedURL.code == data["short_code"])
    short_url = session.exec(statement).first()

    assert short_url is not None
    assert short_url.url == TEST_URL
    assert short_url.owner_id is None

def test_create_short_url_authenticated(session: Session, client: TestClient):
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

    response = client.post(
            "/api/short",
            json={"url": TEST_URL},
            headers={"Authorization": f"Bearer {access_token}"}
    )
    data = response.json()

    assert response.status_code == 201
    assert data["short_code"] is not None
    assert isinstance(data["short_code"], str)
    assert len(data["short_code"]) == 8 
    assert data["url"] == TEST_URL

def test_create_short_url_authenticated_persists(session: Session, client: TestClient):
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

    response = client.post(
            "/api/short",
            json={"url": TEST_URL},
            headers={"Authorization": f"Bearer {access_token}"}
    )

    data = response.json()
    statement = select(ShortenedURL).where(ShortenedURL.code == data["short_code"])
    short_url = session.exec(statement).first()

    assert short_url is not None
    assert short_url.url == TEST_URL
    assert short_url.owner_id == test_user.id

def test_create_short_url_invalid_input(client: TestClient):
    response = client.post(
            "/api/short",
            json={}
    )
    data = response.json()

    assert response.status_code == 422

def test_create_user(session: Session, client: TestClient):
    response = client.post(
            "/api/users",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    data = response.json()

    assert response.status_code == 201
    assert data["id"] is not None
    assert isinstance(data["id"], int)
    assert data["email"] == TEST_EMAIL
    assert data["disabled"] == False

    statement = select(User).where(User.email == TEST_EMAIL)
    user = session.exec(statement).first()

    assert user is not None
    assert user.password_hash is not None
    assert user.disabled == False
    assert verify_password(TEST_PASSWORD, user.password_hash)

def test_create_user_exists(session: Session, client: TestClient):
    test_user = User(email=TEST_EMAIL, password_hash=get_hashed_password(TEST_PASSWORD))
    session.add(test_user)
    session.commit()
    
    response = client.post(
            "/api/users",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    data = response.json()

    assert response.status_code == 409
    assert data["detail"] is not None
    assert isinstance(data["detail"], str)

    statement = select(User)
    users = session.exec(statement).all()

    assert len(users) == 1

def test_create_user_invalid_input(session: Session, client: TestClient):
    response = client.post(
            "/api/users",
            json={}
    )
    data = response.json()

    assert response.status_code == 422
    
    statement = select(User)
    users = session.exec(statement).all()

    assert len(users) == 0

def test_get_user_links(session: Session, client: TestClient):
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

    test_short_url = ShortenedURL(url=TEST_URL, owner_id=test_user.id)
    test_short_url2 = ShortenedURL(url=TEST_URL + "/2", owner_id=test_user.id)
    session.add(test_short_url)
    session.add(test_short_url2)
    session.commit()
    session.refresh(test_short_url)
    session.refresh(test_short_url2)

    response = client.get(
            "/api/users/me/links",
            headers={"Authorization": f"Bearer {access_token}"}
    )
    data = response.json()

    assert response.status_code == 200
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["url"] == TEST_URL
    assert data[0]["short_code"] == test_short_url.code
    assert data[1]["url"] == TEST_URL + "/2"
    assert data[1]["short_code"] == test_short_url2.code

def test_get_user_links_unauthenticated(client: TestClient):
    response = client.get("/api/users/me/links")
    data = response.json()

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert data["detail"] is not None

def test_create_access_token_from_login(session: Session, client: TestClient):
    test_user = User(email=TEST_EMAIL, password_hash=get_hashed_password(TEST_PASSWORD))
    session.add(test_user)
    session.commit()
    session.refresh(test_user)

    response = client.post(
            "/api/token",
            data={"grant_type": "password", "username": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    data = response.json()

    assert response.status_code == 200
    assert "set-cookie" not in response.headers
    assert data["token_type"] == "Bearer"
    assert data["access_token"] is not None
    assert isinstance(data["access_token"], str)

    decoded = decode_access_token(data["access_token"])

    assert decoded["sub"] == str(test_user.id)
    assert decoded["exp"] is not None
    assert isinstance(decoded["exp"], int)
    assert decoded["exp"] > 0

def test_create_access_token_from_login_with_cookie(session: Session, client: TestClient):
    test_user = User(email=TEST_EMAIL, password_hash=get_hashed_password(TEST_PASSWORD))
    session.add(test_user)
    session.commit()
    session.refresh(test_user)

    response = client.post(
            "/api/token",
            data={"grant_type": "password", "username": TEST_EMAIL, "password": TEST_PASSWORD, "client_type": "web"},
    )
    data = response.json()
    
    assert response.status_code == 200
    assert data["token_type"] == "Bearer"
    assert data["access_token"] is not None
    assert response.cookies.get("access_token") is not None
    assert len(response.cookies.get("access_token")) > 0 

def test_create_access_token_from_login_invalid_input(client: TestClient):
    response = client.post(
            "/api/token",
            data={}
    )
    data = response.json()

    assert response.status_code == 400
    assert data["error"] == "invalid_request"


def test_create_access_token_from_login_incorrect_credentials(client: TestClient):
    response = client.post(
            "/api/token",
            data={"grant_type": "password", "username": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    data = response.json()

    assert response.status_code == 400
    assert data["error"] == "invalid_grant" 
    assert data["error_description"] is not None
    assert isinstance(data["error_description"], str)

def test_delete_access_token_cookie(client: TestClient):
    client.cookies.set("access_token", "test_token")
    response = client.delete("/api/token")

    assert response.status_code == 204
    assert response.cookies.get("access_token") is None
    assert response.content == b""