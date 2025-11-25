import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker
from src.main import app
from src.database import Base, get_db as session_opener
from src.auth.models import User
from jose import jwt
from src.auth.config import PWD_CONTEXT as pwd_context

SECRET_KEY = "1892dhianiandowqd0n"
ALGORITHM = "HS256"
# SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_session_opener():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[session_opener] = override_session_opener

client = TestClient(app)

@pytest.fixture(scope="module")
def clear_users():
    with next(override_session_opener()) as db:
        db.query(User).delete()
        db.commit()

@pytest.fixture(scope="module")
def test_user(clear_users):
    hashed_password = pwd_context.hash("testpassword")

    with next(override_session_opener()) as db:
        user = User(username="testuser", hashed_password=hashed_password)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user


@pytest.fixture(scope="module")
def test_token(test_user):
    access_token = jwt.encode({"sub": test_user.username}, SECRET_KEY, algorithm=ALGORITHM)
    return access_token


def test_register_user():
    response = client.post("/api/v1/users/register", json={
        "username": "newuser",
        "password": "newpassword"
    })

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "newuser"


def test_login_for_access_token(test_user):
    response = client.post("/api/v1/users/login", data={
        "username": "testuser",
        "password": "testpassword"
    })

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_read_users_me(test_token):
    headers = {"Authorization": f"Bearer {test_token}"}
    response = client.get("/api/v1/users/me", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"