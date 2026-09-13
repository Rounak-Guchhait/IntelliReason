import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["APP_ENV"] = "test"
os.environ["LLM_PROVIDER"] = "groq"
os.environ.pop("GROQ_API_KEY", None)
os.environ.pop("DATABASE_URL", None)

from fastapi.testclient import TestClient

from app.main import app


def test_health():
    with TestClient(app) as client:
        resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["app"] == "IntelliReason"
    assert "model" in data


def test_root():
    with TestClient(app) as client:
        resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["name"] == "IntelliReason"


def test_reason_missing_field():
    with TestClient(app) as client:
        resp = client.post("/api/reason", json={})
    assert resp.status_code == 422