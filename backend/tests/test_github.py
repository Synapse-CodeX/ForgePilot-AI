"""Unit tests for the GitHub integration service."""

from typing import Any

import httpx
import pytest

from backend.app.core.config import Settings
from backend.app.schemas import IssueContext, RepositoryContext
from backend.app.services.github import GitHubAPIError, GitHubService


def create_service(
    handler,
    token: str = "",
) -> GitHubService:
    """Create a service backed by a mocked HTTP transport."""

    transport = httpx.MockTransport(handler)
    settings = Settings(
        github_token=token,
        github_api_base_url="https://api.github.test",
    )

    return GitHubService(settings=settings, transport=transport)


def repository_payload() -> dict[str, Any]:
    """Return representative GitHub repository JSON."""

    return {
        "name": "hello-world",
        "full_name": "octocat/hello-world",
        "html_url": "https://github.com/octocat/hello-world",
        "owner": {"login": "octocat"},
        "description": "Example repository",
        "default_branch": "main",
        "private": False,
        "language": "Python",
        "stargazers_count": 12,
        "forks_count": 3,
        "open_issues_count": 2,
    }


def issue_payload() -> dict[str, Any]:
    """Return representative GitHub issue JSON."""

    return {
        "number": 42,
        "title": "Fix crash on startup",
        "body": "The application crashes during initialization.",
        "state": "open",
        "html_url": "https://github.com/octocat/hello-world/issues/42",
        "user": {"login": "octocat"},
        "labels": [{"name": "bug"}, {"name": "priority-high"}],
        "created_at": "2026-10-01T10:00:00Z",
        "updated_at": "2026-10-02T10:00:00Z",
    }


@pytest.mark.asyncio
async def test_get_repository_returns_normalized_context() -> None:
    """Test retrieving normalized repository metadata."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/repos/octocat/hello-world"
        return httpx.Response(200, json=repository_payload())

    service = create_service(handler)

    repository = await service.get_repository("octocat", "hello-world")

    assert isinstance(repository, RepositoryContext)
    assert repository.name == "hello-world"
    assert repository.full_name == "octocat/hello-world"
    assert repository.owner == "octocat"
    assert repository.language == "Python"
    assert repository.stars == 12
    assert repository.forks == 3
    assert repository.open_issues == 2


@pytest.mark.asyncio
async def test_get_issue_returns_normalized_context() -> None:
    """Test retrieving normalized issue information."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/repos/octocat/hello-world/issues/42"
        return httpx.Response(200, json=issue_payload())

    service = create_service(handler)

    issue = await service.get_issue("octocat", "hello-world", 42)

    assert isinstance(issue, IssueContext)
    assert issue.number == 42
    assert issue.title == "Fix crash on startup"
    assert issue.repository_full_name == "octocat/hello-world"
    assert issue.author == "octocat"
    assert issue.labels == ["bug", "priority-high"]
    assert issue.is_pull_request is False


@pytest.mark.asyncio
async def test_pull_request_is_identified() -> None:
    """Test that a GitHub pull request is identified in issue responses."""

    payload = issue_payload()
    payload["pull_request"] = {
        "url": "https://api.github.test/repos/octocat/hello-world/pulls/42"
    }

    service = create_service(lambda request: httpx.Response(200, json=payload))

    issue = await service.get_issue("octocat", "hello-world", 42)

    assert issue.is_pull_request is True


@pytest.mark.asyncio
async def test_github_token_is_sent_when_configured() -> None:
    """Test that a configured token is included in requests."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer test-token"
        return httpx.Response(200, json=repository_payload())

    service = create_service(handler, token="test-token")

    result = await service.get_repository("octocat", "hello-world")

    assert result.name == "hello-world"


@pytest.mark.asyncio
async def test_github_http_error_is_wrapped() -> None:
    """Test consistent handling of HTTP errors."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"message": "Not Found"})

    service = create_service(handler)

    with pytest.raises(GitHubAPIError, match="HTTP 404"):
        await service.get_repository("octocat", "missing-repo")


@pytest.mark.asyncio
async def test_invalid_repository_payload_is_rejected() -> None:
    """Test that malformed repository data raises a clear error."""

    service = create_service(
        lambda request: httpx.Response(200, json={"unexpected": "data"})
    )

    with pytest.raises(
        GitHubAPIError,
        match="missing owner information",
    ):
        await service.get_repository("octocat", "hello-world")


@pytest.mark.asyncio
async def test_empty_repository_owner_is_rejected() -> None:
    """Test validation of repository identifiers."""

    service = create_service(lambda request: httpx.Response(200, json={}))

    with pytest.raises(ValueError, match="owner and name are required"):
        await service.get_repository("", "hello-world")


@pytest.mark.asyncio
async def test_invalid_issue_number_is_rejected() -> None:
    """Test validation of issue numbers."""

    service = create_service(lambda request: httpx.Response(200, json={}))

    with pytest.raises(ValueError, match="positive integer"):
        await service.get_issue("octocat", "hello-world", 0)
