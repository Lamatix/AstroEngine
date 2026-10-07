"""Automation endpoint testleri."""
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_execute_task_ephemeris():
    with patch("app.services.model_router_service.AutonomousModelRouter.route_task") as mock_route, \
         patch("app.api.routers.automation.trigger_n8n_workflow"):
        mock_route.return_value = {"engine": "Swiss Ephemeris", "status": "success"}
        response = client.post("/api/v1/automation/execute-task",
                               json={"task_type": "ephemeris", "payload": {"date": "2026-01-01"}})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["task_type"] == "ephemeris"


def test_execute_task_unknown_type():
    response = client.post("/api/v1/automation/execute-task",
                           json={"task_type": "unknown_type_xyz", "payload": {}})
    assert response.status_code == 400


def test_n8n_callback_received():
    response = client.post("/api/v1/automation/n8n-callback",
                           json={"job_id": "test-job-123", "success": True, "result": {"data": "ok"}})
    assert response.status_code == 200
    assert response.json() == {"status": "received", "job_id": "test-job-123"}


def test_model_router_ephemeris_real():
    from app.services.model_router_service import model_router_instance
    out = model_router_instance.route_task("ephemeris", {"date": "2026-01-01"})
    assert out["status"] == "success" and "2026-01-01" in out["computed_data"]
