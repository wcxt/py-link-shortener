from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
import pytest
from database import get_session
from main import app

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

    

