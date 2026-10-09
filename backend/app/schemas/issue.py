"""Validated issue context models."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class IssueContext(BaseModel):
    """Normalized GitHub issue data for debugging workflows."""

    model_config = ConfigDict(extra="ignore")

    repository_full_name: str = Field(min_length=3)
    number: int = Field(gt=0)
    title: str = Field(min_length=1)
    body: str | None = None
    state: str
    html_url: HttpUrl
    author: str | None = None
    labels: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    is_pull_request: bool = False
