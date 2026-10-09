"""Validated repository context models."""

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class RepositoryContext(BaseModel):
    """Normalized metadata for a GitHub repository."""

    model_config = ConfigDict(extra="ignore")

    owner: str = Field(min_length=1)
    name: str = Field(min_length=1)
    full_name: str = Field(min_length=3)
    html_url: HttpUrl
    description: str | None = None
    default_branch: str | None = None
    private: bool = False
    language: str | None = None
    stars: int = Field(default=0, ge=0)
    forks: int = Field(default=0, ge=0)
    open_issues: int = Field(default=0, ge=0)
