from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
import pytest
from app.core.database import get_session
from app.core.security import get_hashed_password
from app.core.middleware import clients
from app.main import app
from app.models import User

TEST_EMAIL="user@example.com"
TEST_PASSWORD="password"
TEST_URL="http://www.google.com/"

engine = create_engine("postgresql://postgres:postgres@localhost:5432/link_shortener_test")

@pytest.fixture(scope="session", autouse=True)
def db_fixture():
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(name="session")
def session_fixture():
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():  
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    
    yield client

    app.dependency_overrides.clear()

@pytest.fixture(name="user")
def user_fixture(session: Session):
    test_user = User(email=TEST_EMAIL, password_hash=get_hashed_password(TEST_PASSWORD))
    session.add(test_user)
    session.commit()
    session.refresh(test_user)
    return test_user

@pytest.fixture(name="auth")
def auth_fixture(client: TestClient, user: User):
    response = client.post(
            "/api/token",
            data={"grant_type": "password", "username": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    data = response.json()
    return {"user": user, "token": data["access_token"]}

@pytest.fixture(autouse=True)
def clear_rate_limit_clients():
    clients.clear()

