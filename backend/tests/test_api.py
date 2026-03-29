import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import AsyncMock, patch, MagicMock
import uuid

from app.main import app
from app.database import Base, get_db
from app.models.user import User
from app.services.auth import hash_password

# Use SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db):
    user = User(
        email="test@example.com",
        hashed_password=hash_password("password123"),
        api_key="sk-testkey1234567890",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


class TestHealth:
    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_root(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data


class TestAuth:
    def test_register(self, client):
        response = client.post("/auth/register", json={
            "email": "new@example.com",
            "password": "securepass123",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "new@example.com"
        assert "api_key" in data
        assert data["api_key"].startswith("sk-")

    def test_register_duplicate_email(self, client, test_user):
        response = client.post("/auth/register", json={
            "email": "test@example.com",
            "password": "password123",
        })
        assert response.status_code == 400

    def test_login(self, client, test_user):
        response = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "password123",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, test_user):
        response = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "wrongpassword",
        })
        assert response.status_code == 401

    def test_get_me_with_api_key(self, client, test_user):
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {test_user.api_key}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"

    def test_get_me_unauthenticated(self, client):
        response = client.get("/auth/me")
        assert response.status_code == 401


class TestModels:
    def test_list_models(self, client):
        response = client.get("/v1/models")
        assert response.status_code == 200
        data = response.json()
        assert data["object"] == "list"
        assert len(data["data"]) > 0
        model = data["data"][0]
        assert "id" in model
        assert "owned_by" in model


class TestUsage:
    def test_get_usage_authenticated(self, client, test_user):
        response = client.get(
            "/v1/usage",
            headers={"Authorization": f"Bearer {test_user.api_key}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "records" in data
        assert data["summary"]["total_requests"] == 0

    def test_get_usage_unauthenticated(self, client):
        response = client.get("/v1/usage")
        assert response.status_code == 401


class TestChat:
    @patch("app.routers.chat.route_chat_completion")
    @patch("app.routers.chat.get_cached_response", return_value=None)
    @patch("app.routers.chat.set_cached_response", new_callable=AsyncMock)
    def test_chat_completion(
        self, mock_set_cache, mock_get_cache, mock_route, client, test_user
    ):
        mock_route.return_value = {
            "id": "chatcmpl-test",
            "object": "chat.completion",
            "created": 1704067200,
            "model": "gpt-3.5-turbo",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "Hello!"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15,
            },
        }

        response = client.post(
            "/v1/chat/completions",
            headers={"Authorization": f"Bearer {test_user.api_key}"},
            json={
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": "Hello"}],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["choices"][0]["message"]["content"] == "Hello!"

    def test_chat_unauthenticated(self, client):
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": "Hello"}],
            },
        )
        assert response.status_code == 401
