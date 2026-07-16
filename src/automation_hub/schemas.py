from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ResourceCreate(BaseModel):
    kind: Literal["skill", "mcp"]
    name: str = Field(min_length=2, max_length=80)
    description: str = Field(default="", max_length=500)
    endpoint: str | None = Field(default=None, max_length=300)
    config: dict[str, Any] = Field(default_factory=dict)


class WorkflowStep(BaseModel):
    resource_id: int
    action: str = Field(default="execute", min_length=2, max_length=80)


class WorkflowCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str = Field(default="", max_length=500)
    steps: list[WorkflowStep] = Field(min_length=1, max_length=20)


class RunRequest(BaseModel):
    input: dict[str, Any] = Field(default_factory=dict)

