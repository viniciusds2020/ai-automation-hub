from fastapi.testclient import TestClient

from automation_hub.database import initialize
from automation_hub.main import app


def test_create_and_execute_workflow(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "test.db"))
    initialize()
    with TestClient(app) as client:
        resource = client.post(
            "/api/resources",
            json={"kind": "skill", "name": "Classificador", "description": "Classifica."},
        )
        assert resource.status_code == 201
        workflow = client.post(
            "/api/workflows",
            json={"name": "Triagem", "steps": [
                {"resource_id": resource.json()["id"], "action": "classify"}
            ]},
        )
        assert workflow.status_code == 201
        run = client.post(
            f"/api/workflows/{workflow.json()['id']}/run",
            json={"input": {"text": "teste"}},
        )
        assert run.status_code == 200
        assert run.json()["steps"][0]["mode"] == "simulation"


def test_health(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "health.db"))
    with TestClient(app) as client:
        assert client.get("/health").json()["status"] == "ok"

