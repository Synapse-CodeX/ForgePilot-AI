"""Validated schemas for generated and applied code patches."""

from pydantic import BaseModel, ConfigDict, Field


class PatchProposal(BaseModel):
    """A proposed unified diff awaiting validation and review."""

    model_config = ConfigDict(extra="forbid")

    repository_full_name: str = Field(min_length=3)
    issue_number: int = Field(gt=0)
    summary: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    unified_diff: str = Field(min_length=1)
    files_changed: list[str] = Field(min_length=1)


class PatchApplicationResult(BaseModel):
    """Outcome of applying a validated patch to a repository workspace."""

    model_config = ConfigDict(extra="forbid")

    repository_full_name: str = Field(min_length=3)
    issue_number: int = Field(gt=0)
    applied: bool
    files_changed: list[str] = Field(min_length=1)
    message: str = Field(min_length=1)
