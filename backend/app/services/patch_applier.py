"""Safely apply validated patches to an explicitly supplied Git workspace."""

import logging
import re
import subprocess
from pathlib import Path, PurePosixPath

from backend.app.schemas.patch import (
    PatchApplicationResult,
    PatchProposal,
)

logger = logging.getLogger(__name__)

_DIFF_HEADER = re.compile(r"^(---|\+\+\+) (.+?)(?:\t.*)?$")
_HUNK_HEADER = re.compile(r"^@@ .* @@")


class PatchApplicationError(RuntimeError):
    """Raised when a patch cannot be safely applied."""


class PatchApplier:
    """Validate and apply a patch in a clean Git working tree.

    The caller must supply a dedicated repository workspace, not the main
    ForgePilot development repository. This service never executes source code.
    """

    def __init__(
        self,
        repository_path: str | Path,
        git_timeout_seconds: int = 15,
    ) -> None:
        if git_timeout_seconds < 1:
            raise ValueError("git_timeout_seconds must be at least 1")

        self._repository_path = Path(repository_path).resolve()
        self._git_timeout_seconds = git_timeout_seconds

        if not self._repository_path.is_dir():
            raise PatchApplicationError(
                "The supplied repository workspace is not a directory"
            )

    def _run_git(
        self,
        arguments: list[str],
        *,
        input_text: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        """Run a bounded Git command without invoking a shell."""
        try:
            return subprocess.run(
                ["git", *arguments],
                cwd=self._repository_path,
                input=input_text,
                capture_output=True,
                text=True,
                check=False,
                timeout=self._git_timeout_seconds,
            )
        except FileNotFoundError as exc:
            raise PatchApplicationError(
                "Git was not found. Install Git and ensure it is on PATH."
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise PatchApplicationError("The Git command timed out") from exc
        except OSError as exc:
            raise PatchApplicationError("The Git command could not be started") from exc

    def _ensure_repository_root(self) -> None:
        """Require the supplied directory to be the Git repository root."""
        result = self._run_git(["rev-parse", "--show-toplevel"])

        if result.returncode != 0:
            raise PatchApplicationError(
                "The supplied workspace is not a Git repository"
            )

        reported_root = Path(result.stdout.strip()).resolve()
        if reported_root != self._repository_path:
            raise PatchApplicationError(
                "The supplied path must be the Git repository root"
            )

    def _ensure_clean_worktree(self) -> None:
        """Avoid overwriting unrelated staged, unstaged, or untracked changes."""
        result = self._run_git(["status", "--porcelain", "--untracked-files=all"])

        if result.returncode != 0:
            raise PatchApplicationError("Could not inspect the repository working tree")

        if result.stdout.strip():
            raise PatchApplicationError(
                "The repository working tree must be clean before applying a patch"
            )

    @staticmethod
    def _normalize_patch_path(raw_path: str, expected_prefix: str) -> str:
        """Accept only safe, repository-relative a/ or b/ paths."""
        path = raw_path.strip()

        if path == "/dev/null" or not path.startswith(expected_prefix):
            raise PatchApplicationError("Patch contains an unsupported file path")

        relative = path[len(expected_prefix) :]

        if (
            not relative
            or "\\" in relative
            or "\x00" in relative
            or relative.startswith("/")
            or re.match(r"^[A-Za-z]:", relative)
        ):
            raise PatchApplicationError("Patch contains an unsafe file path")

        parts = relative.split("/")
        if any(part in {"", ".", ".."} for part in parts):
            raise PatchApplicationError("Patch contains a path traversal attempt")

        parsed = PurePosixPath(relative)
        if parsed.is_absolute():
            raise PatchApplicationError("Absolute patch paths are not allowed")

        return parsed.as_posix()

    def _validate_patch(
        self,
        proposal: PatchProposal,
    ) -> list[str]:
        """Check patch headers, declared paths, and existing targets."""
        if not proposal.unified_diff.strip():
            raise PatchApplicationError("The patch is empty")

        declared_paths: list[str] = []
        for raw_path in proposal.files_changed:
            if (
                not raw_path
                or "\\" in raw_path
                or "\x00" in raw_path
                or raw_path.startswith("/")
                or re.match(r"^[A-Za-z]:", raw_path)
            ):
                raise PatchApplicationError("files_changed contains an unsafe path")

            parts = raw_path.split("/")
            if any(part in {"", ".", ".."} for part in parts):
                raise PatchApplicationError(
                    "files_changed contains a path traversal attempt"
                )

            normalized = PurePosixPath(raw_path).as_posix()
            if normalized in declared_paths:
                raise PatchApplicationError("files_changed contains duplicate paths")
            declared_paths.append(normalized)

        actual_paths: list[str] = []
        old_path: str | None = None
        new_path: str | None = None
        has_hunk = False
        has_change = False

        for line in proposal.unified_diff.splitlines():
            match = _DIFF_HEADER.match(line)

            if match:
                marker, raw_path = match.groups()

                if marker == "---":
                    if old_path is not None or new_path is not None:
                        raise PatchApplicationError(
                            "Patch contains incomplete or repeated file headers"
                        )
                    old_path = self._normalize_patch_path(raw_path, "a/")
                else:
                    if old_path is None or new_path is not None:
                        raise PatchApplicationError(
                            "Patch contains an unmatched file header"
                        )
                    new_path = self._normalize_patch_path(raw_path, "b/")

                    if old_path != new_path:
                        raise PatchApplicationError(
                            "Adding, deleting, and renaming files is not supported"
                        )

                    if new_path not in declared_paths:
                        raise PatchApplicationError(
                            f"Patch targets an undeclared file: {new_path}"
                        )

                    if new_path not in actual_paths:
                        actual_paths.append(new_path)

                    old_path = None
                    new_path = None
                continue

            if _HUNK_HEADER.match(line):
                has_hunk = True
            elif line.startswith("+") and not line.startswith("+++"):
                has_change = True
            elif line.startswith("-") and not line.startswith("---"):
                has_change = True

        if old_path is not None or new_path is not None:
            raise PatchApplicationError("Patch contains incomplete file headers")

        if not actual_paths:
            raise PatchApplicationError("Patch does not identify any changed files")

        if not has_hunk or not has_change:
            raise PatchApplicationError(
                "Patch must contain a hunk with additions or deletions"
            )

        if set(actual_paths) != set(declared_paths):
            raise PatchApplicationError(
                "files_changed does not match the paths in the patch"
            )

        for relative_path in actual_paths:
            target = self._repository_path.joinpath(*relative_path.split("/"))

            current = self._repository_path
            for part in relative_path.split("/"):
                current = current / part
                if current.is_symlink():
                    raise PatchApplicationError(
                        f"Symbolic-link targets are not allowed: {relative_path}"
                    )

            try:
                resolved_target = target.resolve(strict=True)
                resolved_target.relative_to(self._repository_path)
            except (OSError, ValueError) as exc:
                raise PatchApplicationError(
                    f"Patch target is missing or outside the workspace: {relative_path}"
                ) from exc

            if not resolved_target.is_file():
                raise PatchApplicationError(
                    f"Patch target is not a regular file: {relative_path}"
                )

        return actual_paths

    def apply(self, proposal: PatchProposal) -> PatchApplicationResult:
        """Validate the patch, check applicability, and apply it."""
        self._ensure_repository_root()
        paths = self._validate_patch(proposal)
        self._ensure_clean_worktree()

        check_result = self._run_git(
            ["apply", "--check"],
            input_text=proposal.unified_diff,
        )

        if check_result.returncode != 0:
            detail = check_result.stderr.strip() or "Patch check failed"
            raise PatchApplicationError(
                f"Git rejected the patch during preflight: {detail}"
            )

        apply_result = self._run_git(
            ["apply"],
            input_text=proposal.unified_diff,
        )

        if apply_result.returncode != 0:
            detail = apply_result.stderr.strip() or "Patch application failed"
            logger.error("Git patch application failed: %s", detail)
            raise PatchApplicationError(f"Git could not apply the patch: {detail}")

        return PatchApplicationResult(
            repository_full_name=proposal.repository_full_name,
            issue_number=proposal.issue_number,
            applied=True,
            files_changed=paths,
            message="Patch passed Git preflight and was applied successfully.",
        )
