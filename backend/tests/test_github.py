"""Unit tests for the GitHub integration service."""

import httpx
import pytest

from backend.app.core.config import Settings
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


@pytest.mark.asyncio
async def test_get_repository_returns_metadata() -> None:
    """Test retrieving repository metadata."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/repos/octocat/hello-world"
        return httpx.Response(
            200,
            json={
                "name": "hello-world",
                "full_name": "octocat/hello-world",
                "private": False,
            },
        )

    service = create_service(handler)

    repository = await service.get_repository("octocat", "hello-world")

    assert repository["name"] == "hello-world"
    assert repository["full_name"] == "octocat/hello-world"
    assert repository["private"] is False


@pytest.mark.asyncio
async def test_get_issue_returns_issue_data() -> None:
    """Test retrieving an issue from a repository."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/repos/octocat/hello-world/issues/42"
        return httpx.Response(
            200,
            json={
                "number": 42,
                "title": "Fix crash on startup",
                "body": "The application crashes during initialization.",
                "state": "open",
            },
        )

    service = create_service(handler)

    issue = await service.get_issue("octocat", "hello-world", 42)

    assert issue["number"] == 42
    assert issue["title"] == "Fix crash on startup"
    assert issue["state"] == "open"


@pytest.mark.asyncio
async def test_github_token_is_sent_when_configured() -> None:
    """Test that a configured token is included in the request."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer test-token"
        return httpx.Response(200, json={"name": "hello-world"})

    service = create_service(handler, token="test-token")

    result = await service.get_repository("octocat", "hello-world")

    assert result["name"] == "hello-world"


@pytest.mark.asyncio
async def test_github_http_error_is_wrapped() -> None:
    """Test consistent handling of HTTP errors."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"message": "Not Found"})

    service = create_service(handler)

    with pytest.raises(GitHubAPIError, match="HTTP 404"):
        await service.get_repository("octocat", "missing-repo")


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
