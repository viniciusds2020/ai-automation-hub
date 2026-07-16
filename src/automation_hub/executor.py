from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from automation_hub.database import connection


def execute_workflow(workflow_id: int, payload: dict[str, Any]) -> dict:
    with connection() as db:
        workflow = db.execute(
            "SELECT * FROM workflows WHERE id=? AND enabled=1", (workflow_id,)
        ).fetchone()
        if workflow is None:
            raise ValueError("Workflow not found or disabled.")
        run_id = db.execute(
            "INSERT INTO runs(workflow_id,status) VALUES(?,'running')", (workflow_id,)
        ).lastrowid
    try:
        outputs = []
        current = payload
        for position, step in enumerate(json.loads(workflow["steps_json"]), start=1):
            with connection() as db:
                resource = db.execute(
                    "SELECT * FROM resources WHERE id=? AND status='active'",
                    (step["resource_id"],),
                ).fetchone()
            if resource is None:
                raise ValueError(f"Active resource not found: {step['resource_id']}")
            result = {
                "step": position, "resource": resource["name"], "kind": resource["kind"],
                "action": step["action"], "mode": "simulation", "received": current,
                "message": "Validated. Connect a trusted adapter for real execution.",
            }
            outputs.append(result)
            current = {"previous_step": result}
        finished = datetime.now(timezone.utc).isoformat()
        with connection() as db:
            db.execute(
                "UPDATE runs SET status='completed',finished_at=?,output_json=? WHERE id=?",
                (finished, json.dumps(outputs, ensure_ascii=False), run_id),
            )
        return {"run_id": run_id, "status": "completed", "steps": outputs}
    except Exception as exc:
        with connection() as db:
            db.execute(
                "UPDATE runs SET status='failed',finished_at=?,error=? WHERE id=?",
                (datetime.now(timezone.utc).isoformat(), str(exc), run_id),
            )
        raise

