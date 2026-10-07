from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    """Health artık gerçek kontroller döndürür: ok (hepsi sağlıklı) veya degraded."""
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in ("ok", "degraded")
    assert set(body["checks"]) == {"database", "redis", "celery", "openai_api", "ephemeris"}
    assert body["checks"]["ephemeris"]["healthy"] is True
