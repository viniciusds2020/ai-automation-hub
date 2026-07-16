from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException, status

from automation_hub.database import connection, rows
from automation_hub.executor import execute_workflow
from automation_hub.schemas import ResourceCreate, RunRequest, WorkflowCreate

router = APIRouter(prefix="/api")


@router.get("/dashboard")
def dashboard() -> dict:
    with connection() as db:
        grouped = db.execute("SELECT kind,COUNT(*) count FROM resources GROUP BY kind").fetchall()
        workflows = db.execute("SELECT COUNT(*) FROM workflows").fetchone()[0]
        runs = db.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
        success = db.execute("SELECT COUNT(*) FROM runs WHERE status='completed'").fetchone()[0]
    counts = {item["kind"]: item["count"] for item in grouped}
    return {"skills": counts.get("skill", 0), "mcps": counts.get("mcp", 0),
            "workflows": workflows, "runs": runs,
            "success_rate": round(success / runs * 100, 1) if runs else 0}


@router.get("/resources")
def list_resources() -> list[dict]:
    result = rows("SELECT * FROM resources ORDER BY id DESC")
    for item in result:
        item["config"] = json.loads(item.pop("config_json"))
    return result


@router.post("/resources", status_code=status.HTTP_201_CREATED)
def create_resource(payload: ResourceCreate) -> dict:
    with connection() as db:
        resource_id = db.execute(
            "INSERT INTO resources(kind,name,description,endpoint,config_json) VALUES(?,?,?,?,?)",
            (payload.kind, payload.name, payload.description, payload.endpoint,
             json.dumps(payload.config)),
        ).lastrowid
    return {"id": resource_id, **payload.model_dump()}


@router.get("/workflows")
def list_workflows() -> list[dict]:
    result = rows("SELECT * FROM workflows ORDER BY id DESC")
    for item in result:
        item["steps"] = json.loads(item.pop("steps_json"))
        item["enabled"] = bool(item["enabled"])
    return result


@router.post("/workflows", status_code=status.HTTP_201_CREATED)
def create_workflow(payload: WorkflowCreate) -> dict:
    ids = [step.resource_id for step in payload.steps]
    placeholders = ",".join("?" for _ in ids)
    with connection() as db:
        found = db.execute(
            f"SELECT COUNT(*) FROM resources WHERE id IN ({placeholders})", tuple(set(ids))
        ).fetchone()[0]
        if found != len(set(ids)):
            raise HTTPException(422, "One or more resources do not exist.")
        workflow_id = db.execute(
            "INSERT INTO workflows(name,description,steps_json) VALUES(?,?,?)",
            (payload.name, payload.description,
             json.dumps([step.model_dump() for step in payload.steps])),
        ).lastrowid
    return {"id": workflow_id, **payload.model_dump()}


@router.post("/workflows/{workflow_id}/run")
def run_workflow(workflow_id: int, payload: RunRequest) -> dict:
    try:
        return execute_workflow(workflow_id, payload.input)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/runs")
def list_runs(limit: int = 20) -> list[dict]:
    return rows(
        """SELECT runs.id,runs.workflow_id,runs.status,runs.started_at,runs.finished_at,
        runs.error,workflows.name workflow_name FROM runs JOIN workflows
        ON workflows.id=runs.workflow_id ORDER BY runs.id DESC LIMIT ?""",
        (min(max(limit, 1), 100),),
    )

