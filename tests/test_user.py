import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.fake_db.database import Database
from importlib import import_module
user_router = import_module("src.routers.user")


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(user_router, "db", Database())
    with TestClient(app) as test_client:
        yield test_client


def test_get_existed_user(client):
    response = client.get(
        "/api/v1/user",
        params={"email": "i.i.ivanov@mail.com"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "name": "Ivan Ivanov",
        "email": "i.i.ivanov@mail.com",
    }


def test_get_unexisted_user(client):
    response = client.get(
        "/api/v1/user",
        params={"email": "missing@example.com"},
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}


def test_create_user_with_valid_email(client):
    data = {"name": "Roman", "email": "roman@example.com"}
    response = client.post("/api/v1/user", json=data)

    assert response.status_code == 201
    user_id = response.json()
    assert isinstance(user_id, int)

    saved = client.get("/api/v1/user", params={"email": data["email"]})
    assert saved.status_code == 200
    assert saved.json() == {"id": user_id, **data}


def test_create_user_with_invalid_email(client):
    response = client.post(
        "/api/v1/user",
        json={"name": "Duplicate", "email": "i.i.ivanov@mail.com"},
    )
    assert response.status_code == 409
    assert response.json() == {
        "detail": "User with this email already exists"
    }

    saved = client.get(
        "/api/v1/user",
        params={"email": "i.i.ivanov@mail.com"},
    )
    assert saved.json()["name"] == "Ivan Ivanov"


def test_delete_user(client):
    email = "i.i.ivanov@mail.com"
    response = client.delete("/api/v1/user", params={"email": email})
    assert response.status_code == 204
    assert response.content == b""

    deleted = client.get("/api/v1/user", params={"email": email})
    assert deleted.status_code == 404
