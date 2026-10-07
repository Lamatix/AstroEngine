"""Auth endpoint testleri."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_register_missing_fields():
    response = client.post("/api/v1/auth/register", json={})
    assert response.status_code == 422


def test_protected_endpoint_without_token():
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_protected_endpoint_with_invalid_token():
    response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
    assert response.status_code == 401
