"""GitHub REST API integration for ForgePilot AI."""

from typing import Any
from urllib.parse import quote

import httpx
from pydantic import ValidationError

from backend.app.core.config import Settings, get_settings
from backend.app.schemas import IssueContext, RepositoryContext


class GitHubAPIError(RuntimeError):
    """Raised when a GitHub API request fails."""


class GitHubService:
    """Retrieve normalized repository and issue context from GitHub."""

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
        """Perform a GET request and return a JSON object."""

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
    ) -> RepositoryContext:
        """Retrieve and normalize repository metadata."""

        owner = owner.strip()
        repo = repo.strip()

        if not owner or not repo:
            raise ValueError("Repository owner and name are required.")

        encoded_owner = quote(owner, safe="")
        encoded_repo = quote(repo, safe="")
        data = await self._get(f"/repos/{encoded_owner}/{encoded_repo}")

        repository_owner = data.get("owner")
        if not isinstance(repository_owner, dict):
            raise GitHubAPIError(
                "GitHub repository response is missing owner information."
            )

        try:
            return RepositoryContext(
                owner=repository_owner.get("login"),
                name=data.get("name"),
                full_name=data.get("full_name"),
                html_url=data.get("html_url"),
                description=data.get("description"),
                default_branch=data.get("default_branch"),
                private=data.get("private", False),
                language=data.get("language"),
                stars=data.get("stargazers_count", 0),
                forks=data.get("forks_count", 0),
                open_issues=data.get("open_issues_count", 0),
            )
        except ValidationError as exc:
            raise GitHubAPIError(
                "GitHub returned invalid repository metadata."
            ) from exc

    async def get_issue(
        self,
        owner: str,
        repo: str,
        issue_number: int,
    ) -> IssueContext:
        """Retrieve and normalize a GitHub issue."""

        owner = owner.strip()
        repo = repo.strip()

        if not owner or not repo:
            raise ValueError("Repository owner and name are required.")

        if issue_number < 1:
            raise ValueError("Issue number must be a positive integer.")

        encoded_owner = quote(owner, safe="")
        encoded_repo = quote(repo, safe="")
        path = f"/repos/{encoded_owner}/{encoded_repo}/issues/{issue_number}"
        data = await self._get(path)

        user = data.get("user")
        author = user.get("login") if isinstance(user, dict) else None

        raw_labels = data.get("labels", [])
        if not isinstance(raw_labels, list):
            raise GitHubAPIError("GitHub returned invalid issue labels.")

        labels: list[str] = []
        for label in raw_labels:
            if not isinstance(label, dict) or not isinstance(label.get("name"), str):
                raise GitHubAPIError("GitHub returned an invalid issue label.")
            labels.append(label["name"])

        try:
            return IssueContext(
                repository_full_name=f"{owner}/{repo}",
                number=data.get("number"),
                title=data.get("title"),
                body=data.get("body"),
                state=data.get("state"),
                html_url=data.get("html_url"),
                author=author,
                labels=labels,
                created_at=data.get("created_at"),
                updated_at=data.get("updated_at"),
                is_pull_request="pull_request" in data,
            )
        except ValidationError as exc:
            raise GitHubAPIError("GitHub returned invalid issue metadata.") from exc
