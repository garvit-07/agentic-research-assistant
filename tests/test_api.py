import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:  # runs lifespan (SQLite checkpointer + graph)
        yield c


def test_health_and_ready(client):
    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/ready").json() == {"ready": True}


def test_index_served(client):
    assert "Research Assistant" in client.get("/").text


def test_empty_thread_history(client):
    r = client.get("/api/v1/threads/does-not-exist")
    assert r.status_code == 200 and r.json()["messages"] == []


def test_api_key_enforced(client, monkeypatch):
    monkeypatch.setattr(settings, "api_key", "secret")
    assert client.get("/api/v1/threads/x").status_code == 401
    assert client.get("/api/v1/threads/x", headers={"X-API-Key": "secret"}).status_code == 200


def test_upload_rejects_bad_type(client):
    r = client.post("/api/v1/documents", files={"file": ("evil.exe", b"x")})
    assert r.status_code == 415


def test_upload_and_index_text(client):
    r = client.post("/api/v1/documents", files={"file": ("note.txt", b"LangGraph builds stateful agents. " * 20)})
    assert r.status_code == 200 and r.json()["chunks"] >= 1
