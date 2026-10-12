

from typing import Literal

from pydantic import BaseModel, Field


class TaskRequest(BaseModel):
    task_id: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=10, max_length=10_000)
    repository_id: str | None = Field(default=None, max_length=100)


class TaskValidationResponse(BaseModel):
    valid: bool
    task_id: str
    repository_id: str | None = None


class EvidenceItem(BaseModel):
    source_type: Literal[
        "repository",
        "test",
        "static_analysis",
        "documentation",
    ]
    source_path: str | None = None
    claim: str = Field(min_length=1, max_length=2_000)
    excerpt: str | None = Field(default=None, max_length=4_000)


class AgentResult(BaseModel):
    agent_name: Literal["backend", "security"]
    status: Literal["completed", "needs_evidence", "failed"]
    summary: str = Field(min_length=1, max_length=5_000)
    evidence: list[EvidenceItem] = Field(default_factory=list)


class ErrorDetail(BaseModel):
    code: str
    message: str
    request_id: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
