"""Structured schemas for automated patch validation."""

from pydantic import BaseModel, ConfigDict, Field


class ValidationCommandResult(BaseModel):
    """Result of running one predefined validation profile."""

    model_config = ConfigDict(extra="forbid")

    profile: str = Field(min_length=1)
    command: list[str] = Field(min_length=1)
    passed: bool
    exit_code: int | None
    stdout: str
    stderr: str
    duration_seconds: float = Field(ge=0.0)
    timed_out: bool = False


class ValidationReport(BaseModel):
    """Combined validation outcome for a proposed patch."""

    model_config = ConfigDict(extra="forbid")

    repository_full_name: str = Field(min_length=3)
    issue_number: int = Field(gt=0)
    passed: bool
    results: list[ValidationCommandResult] = Field(min_length=1)
    summary: str = Field(min_length=1)
