import os
os.environ["AI_ENABLED"] = "false"
os.environ["DATABASE_URL"] = "sqlite:///./data/test_fitbuddy.db"
os.environ["ADMIN_TOKEN"] = "test-token"

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["ai_enabled"] is False


def test_generate_and_feedback():
    payload = {"user_id":"test01","name":"Test User","age":25,"weight":70,"goal":"muscle gain","intensity":"medium"}
    response = client.post("/api/generate-workout", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == "test01"
    assert '"days"' in data["workout_plan"]
    response = client.post("/api/submit-feedback", json={"user_id":"test01","feedback":"Add more cardio"})
    assert response.status_code == 200
    assert response.json()["updated"] is True


def test_admin_list_and_delete():
    response = client.get("/api/users", headers={"X-Admin-Token":"test-token"})
    assert response.status_code == 200
    assert any(item["user_id"] == "test01" for item in response.json())
    response = client.delete("/api/users/test01", headers={"X-Admin-Token":"test-token"})
    assert response.status_code == 204
    response = client.get("/api/users/test01")
    assert response.status_code == 404
