"""GitHub REST API integration for ForgePilot AI."""

from typing import Any
from urllib.parse import quote

import httpx

from backend.app.core.config import Settings, get_settings


class GitHubAPIError(RuntimeError):
    """Raised when a GitHub API request fails."""


class GitHubService:
    """Retrieve repository and issue information from GitHub."""

    def __init__(
        self,
        settings: Settings | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.transport = transport

    def _build_headers(self) -> dict[str, str]:
        """Build headers for GitHub API requests."""

        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        token = self.settings.github_token.strip()
        if token:
            headers["Authorization"] = f"Bearer {token}"

        return headers

    async def _get(self, path: str) -> dict[str, Any]:
        """Perform a GET request and return the decoded JSON object."""

        try:
            async with httpx.AsyncClient(
                base_url=self.settings.github_api_base_url.rstrip("/"),
                headers=self._build_headers(),
                timeout=self.settings.github_timeout_seconds,
                transport=self.transport,
            ) as client:
                response = await client.get(path)
                response.raise_for_status()
                data = response.json()

        except httpx.HTTPStatusError as exc:
            raise GitHubAPIError(
                f"GitHub API returned HTTP {exc.response.status_code}."
            ) from exc
        except httpx.RequestError as exc:
            raise GitHubAPIError("Could not connect to the GitHub API.") from exc
        except ValueError as exc:
            raise GitHubAPIError("GitHub API returned invalid JSON.") from exc

        if not isinstance(data, dict):
            raise GitHubAPIError("GitHub API returned an unexpected response format.")

        return data

    async def get_repository(
        self,
        owner: str,
        repo: str,
    ) -> dict[str, Any]:
        """Retrieve metadata for a repository."""

        owner = owner.strip()
        repo = repo.strip()

        if not owner or not repo:
            raise ValueError("Repository owner and name are required.")

        encoded_owner = quote(owner, safe="")
        encoded_repo = quote(repo, safe="")
        path = f"/repos/{encoded_owner}/{encoded_repo}"

        return await self._get(path)

    async def get_issue(
        self,
        owner: str,
        repo: str,
        issue_number: int,
    ) -> dict[str, Any]:
        """Retrieve a specific issue from a repository."""

        owner = owner.strip()
        repo = repo.strip()

        if not owner or not repo:
            raise ValueError("Repository owner and name are required.")

        if issue_number < 1:
            raise ValueError("Issue number must be a positive integer.")

        encoded_owner = quote(owner, safe="")
        encoded_repo = quote(repo, safe="")
        path = f"/repos/{encoded_owner}/{encoded_repo}/issues/{issue_number}"

        return await self._get(path)
