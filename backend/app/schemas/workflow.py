"""Structured results for an end-to-end repair workflow."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.app.schemas.analysis import RepositoryAnalysis
from backend.app.schemas.issue import IssueContext
from backend.app.schemas.patch import PatchApplicationResult, PatchProposal
from backend.app.schemas.repository import RepositoryContext
from backend.app.schemas.root_cause import RootCauseAnalysis
from backend.app.schemas.validation import ValidationReport

WorkflowStatus = Literal["succeeded", "failed", "validation_failed"]
StageStatus = Literal["succeeded", "failed"]


class WorkflowStageResult(BaseModel):
    """Outcome and duration of one orchestrator stage."""

    model_config = ConfigDict(extra="forbid")

    stage: str = Field(min_length=1)
    status: StageStatus
    message: str = Field(min_length=1)
    duration_seconds: float = Field(ge=0.0)
    error_type: str | None = None


class RepairWorkflowResult(BaseModel):
    """Complete, machine-readable result of one repair attempt."""

    model_config = ConfigDict(extra="forbid")

    repository_full_name: str = Field(min_length=3)
    issue_number: int = Field(gt=0)
    status: WorkflowStatus
    stages: list[WorkflowStageResult] = Field(min_length=1)

    repository: RepositoryContext | None = None
    issue: IssueContext | None = None
    repository_analysis: RepositoryAnalysis | None = None
    root_cause: RootCauseAnalysis | None = None
    patch_proposal: PatchProposal | None = None
    patch_application: PatchApplicationResult | None = None
    validation_report: ValidationReport | None = None

    summary: str = Field(min_length=1)
