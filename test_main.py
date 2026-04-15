from fastapi.testclient import TestClient
from sqlmodel import Session, select

from database import ShortenedURL, User
from security import decode_access_token, get_hashed_password, password_hash, verify_password

def test_create_short_url(client: TestClient):
    test_url = "http://www.google.com/"
    response = client.post(
            "/api/short",
            json={"url": test_url}
    )
    data = response.json()

    assert response.status_code == 201
    assert data["short_code"] is not None
    assert isinstance(data["short_code"], str)
    assert len(data["short_code"]) == 8 
    assert data["url"] == test_url

def test_create_short_url_invalid_input(client: TestClient):
    response = client.post(
            "/api/short",
            json={}
    )
    data = response.json()

    assert response.status_code == 422

def test_create_user(session: Session, client: TestClient):
    test_email = "user@example.com"
    test_password = "password"
    response = client.post(
            "/api/users",
            json={"email": test_email, "password": test_password}
    )
    data = response.json()

    assert response.status_code == 201
    assert data["id"] is not None
    assert isinstance(data["id"], int)
    assert data["email"] == test_email
    assert data["disabled"] == False

    statement = select(User).where(User.email == test_email)
    user = session.exec(statement).first()

    assert user is not None
    assert user.password_hash is not None
    assert user.disabled == False
    assert verify_password(test_password, user.password_hash)

def test_create_user_exists(session: Session, client: TestClient):
    test_email = "user@example.com"
    test_password = "password"

    test_user = User(email=test_email, password_hash=get_hashed_password(test_password))
    session.add(test_user)
    session.commit()
    
    response = client.post(
            "/api/users",
            json={"email": test_email, "password": test_password}
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

def test_create_access_token_from_login(session: Session, client: TestClient):
    test_email = "user@example.com"
    test_password = "password"

    test_user = User(email=test_email, password_hash=get_hashed_password(test_password))
    session.add(test_user)
    session.commit()
    session.refresh(test_user)

    response = client.post(
            "/api/token",
            data={"grant_type": "password", "username": test_email, "password": test_password}
    )
    data = response.json()

    assert response.status_code == 200
    assert data["token_type"] == "Bearer"
    assert data["access_token"] is not None
    assert isinstance(data["access_token"], str)

    decoded = decode_access_token(data["access_token"])

    assert decoded["sub"] == str(test_user.id)
    assert decoded["exp"] is not None
    assert isinstance(decoded["exp"], int)
    assert decoded["exp"] > 0

def test_create_access_token_from_login_invalid_input(client: TestClient):
    response = client.post(
            "/api/token",
            data={}
    )
    data = response.json()

    assert response.status_code == 400
    assert data["error"] == "invalid_request"


def test_create_access_token_from_login_incorrect_credentials(client: TestClient):
    test_email = "user@example.com"
    test_password = "password"

    response = client.post(
            "/api/token",
            data={"grant_type": "password", "username": test_email, "password": test_password}
    )
    data = response.json()

    assert response.status_code == 400
    assert data["error"] == "invalid_grant" 
    assert data["error_description"] is not None
    assert isinstance(data["error_description"], str) 

def test_redirect_code(session: Session, client: TestClient):
    test_url = "http://www.google.com/"

    test_short_url = ShortenedURL(url=test_url)
    session.add(test_short_url)
    session.commit()
    session.refresh(test_short_url)

    response = client.get(f"/{test_short_url.code}", follow_redirects=False)

    assert response.status_code == 301
    assert response.headers["location"] == test_url

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





