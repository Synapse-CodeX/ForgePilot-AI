"""Tests for repository and issue context schemas."""

import pytest
from pydantic import ValidationError

from backend.app.schemas import IssueContext, RepositoryContext


def test_repository_context_accepts_valid_data() -> None:
    """Test validation of a complete repository context."""

    repository = RepositoryContext(
        owner="octocat",
        name="hello-world",
        full_name="octocat/hello-world",
        html_url="https://github.com/octocat/hello-world",
        description="Example repository",
        default_branch="main",
        private=False,
        language="Python",
        stars=10,
        forks=2,
        open_issues=3,
    )

    assert repository.owner == "octocat"
    assert repository.stars == 10
    assert str(repository.html_url) == ("https://github.com/octocat/hello-world")


def test_repository_context_rejects_negative_stars() -> None:
    """Test that repository statistics cannot be negative."""

    with pytest.raises(ValidationError):
        RepositoryContext(
            owner="octocat",
            name="hello-world",
            full_name="octocat/hello-world",
            html_url="https://github.com/octocat/hello-world",
            stars=-1,
        )


def test_repository_context_requires_identity_fields() -> None:
    """Test that required repository identity fields are enforced."""

    with pytest.raises(ValidationError):
        RepositoryContext(
            owner="octocat",
            name="hello-world",
        )


def test_issue_context_accepts_valid_data() -> None:
    """Test validation of issue context and default values."""

    issue = IssueContext(
        repository_full_name="octocat/hello-world",
        number=42,
        title="Fix crash on startup",
        body="Application crashes during initialization.",
        state="open",
        html_url="https://github.com/octocat/hello-world/issues/42",
        author="octocat",
        labels=["bug"],
    )

    assert issue.number == 42
    assert issue.labels == ["bug"]
    assert issue.is_pull_request is False
    assert issue.created_at is None


def test_issue_context_rejects_invalid_number() -> None:
    """Test that issue numbers must be positive."""

    with pytest.raises(ValidationError):
        IssueContext(
            repository_full_name="octocat/hello-world",
            number=0,
            title="Invalid issue",
            state="open",
            html_url="https://github.com/octocat/hello-world/issues/0",
        )


def test_issue_context_rejects_empty_title() -> None:
    """Test that an issue title cannot be empty."""

    with pytest.raises(ValidationError):
        IssueContext(
            repository_full_name="octocat/hello-world",
            number=42,
            title="",
            state="open",
            html_url="https://github.com/octocat/hello-world/issues/42",
        )
