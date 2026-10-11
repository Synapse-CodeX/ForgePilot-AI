"""Validated root-cause analysis schemas."""

from pydantic import BaseModel, ConfigDict, Field


class RootCauseEvidence(BaseModel):
    """Evidence supporting a proposed root cause."""

    model_config = ConfigDict(extra="forbid")

    file_path: str = Field(min_length=1)
    observation: str = Field(min_length=1)
    code_reference: str | None = None


class RootCauseAnalysis(BaseModel):
    """Structured diagnosis produced by the root-cause analyzer."""

    model_config = ConfigDict(extra="forbid")

    repository_full_name: str = Field(min_length=3)
    issue_number: int = Field(gt=0)
    issue_title: str = Field(min_length=1)

    root_cause: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    summary: str = Field(min_length=1)

    evidence: list[RootCauseEvidence] = Field(min_length=1)
    recommended_files: list[str] = Field(min_length=1)
