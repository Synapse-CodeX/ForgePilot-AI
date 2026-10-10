"""Structured results for repository analysis."""

from pydantic import BaseModel, Field


class AnalyzedFile(BaseModel):
    """A repository file ranked for relevance to an issue."""

    path: str
    score: int = Field(ge=0)
    reasons: list[str] = Field(default_factory=list)
    definitions: list[str] = Field(default_factory=list)
    imports: list[str] = Field(default_factory=list)
    syntax_valid: bool = True


class RepositoryAnalysis(BaseModel):
    """Repository analysis results for a GitHub issue."""

    repository_full_name: str = Field(min_length=3)
    issue_number: int = Field(gt=0)
    issue_title: str = Field(min_length=1)
    files_scanned: int = Field(ge=0)
    candidates: list[AnalyzedFile] = Field(default_factory=list)
