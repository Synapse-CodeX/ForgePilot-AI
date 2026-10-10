"""Safe local repository file inspection for ForgePilot AI."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict

from backend.app.core.config import Settings, get_settings


class RepositoryInspectionError(RuntimeError):
    """Raised when a repository file cannot be inspected safely."""


class InspectedFile(BaseModel):
    """Structured content and metadata for an inspected file."""

    model_config = ConfigDict(frozen=True)

    path: str
    content: str
    size_bytes: int
    line_count: int


class RepositoryInspector:
    """Read text files confined to a designated workspace."""

    def __init__(
        self,
        settings: Settings | None = None,
        workspace_root: str | Path | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        configured_root = (
            workspace_root
            if workspace_root is not None
            else self.settings.repository_workspace_root
        )
        self.workspace_root = Path(configured_root).resolve()
        self.max_file_size_bytes = self.settings.max_inspected_file_bytes

        if self.max_file_size_bytes < 1:
            raise ValueError("Maximum inspected file size must be positive.")

    def read_file(self, relative_path: str) -> InspectedFile:
        """Read a UTF-8 text file safely within the workspace."""

        if not relative_path or not relative_path.strip():
            raise RepositoryInspectionError("A relative file path is required.")

        requested_path = Path(relative_path)

        if requested_path.is_absolute():
            raise RepositoryInspectionError("Absolute file paths are not allowed.")

        try:
            resolved_path = (self.workspace_root / requested_path).resolve(strict=True)
        except (OSError, RuntimeError, ValueError) as exc:
            raise RepositoryInspectionError(
                "The requested file could not be resolved."
            ) from exc

        try:
            resolved_path.relative_to(self.workspace_root)
        except ValueError as exc:
            raise RepositoryInspectionError(
                "The requested path is outside the repository workspace."
            ) from exc

        if not resolved_path.is_file():
            raise RepositoryInspectionError("The requested path is not a regular file.")

        try:
            size_bytes = resolved_path.stat().st_size
        except OSError as exc:
            raise RepositoryInspectionError(
                "Could not inspect the requested file."
            ) from exc

        if size_bytes > self.max_file_size_bytes:
            raise RepositoryInspectionError(
                "The requested file exceeds the configured size limit."
            )

        try:
            content = resolved_path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise RepositoryInspectionError(
                "The requested file is not valid UTF-8 text."
            ) from exc
        except OSError as exc:
            raise RepositoryInspectionError(
                "Could not read the requested file."
            ) from exc

        return InspectedFile(
            path=resolved_path.relative_to(self.workspace_root).as_posix(),
            content=content,
            size_bytes=size_bytes,
            line_count=len(content.splitlines()),
        )
