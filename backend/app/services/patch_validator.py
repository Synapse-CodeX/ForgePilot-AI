"""Run predefined validation profiles against a patched repository workspace."""

import logging
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path

from backend.app.schemas.patch import PatchProposal
from backend.app.schemas.validation import (
    ValidationCommandResult,
    ValidationReport,
)

logger = logging.getLogger(__name__)

CommandRunner = Callable[
    [list[str], Path, int],
    subprocess.CompletedProcess[str],
]

DEFAULT_TIMEOUT_SECONDS = 120


# Commands are selected by profile. Callers cannot provide arbitrary shell text.
def _default_command_runner(
    command: list[str],
    workspace: Path,
    timeout_seconds: int,
) -> subprocess.CompletedProcess[str]:
    """Run one command without a shell and with a timeout."""
    return subprocess.run(
        command,
        cwd=workspace,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout_seconds,
        shell=False,
    )


class PatchValidator:
    """Execute predefined validation profiles and aggregate their results.

    Use only with a dedicated, disposable repository workspace. Test and build
    commands may execute code from that workspace.
    """

    def __init__(
        self,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
        command_runner: CommandRunner | None = None,
    ) -> None:
        if timeout_seconds < 1:
            raise ValueError("timeout_seconds must be at least 1")

        self._timeout_seconds = timeout_seconds
        self._command_runner = command_runner or _default_command_runner

    @staticmethod
    def _available_profiles() -> dict[str, list[str]]:
        """Return the predefined commands supported on this machine."""
        return {
            "python_tests": [sys.executable, "-m", "pytest", "-q"],
            "python_lint": ["ruff", "check", "."],
            "frontend_build": [
                "npm",
                "--prefix",
                "frontend",
                "run",
                "build",
            ],
        }

    def _run_profile(
        self,
        profile: str,
        command: list[str],
        workspace: Path,
    ) -> ValidationCommandResult:
        """Execute one profile and convert errors into structured results."""
        started = time.monotonic()

        try:
            completed = self._command_runner(
                command,
                workspace,
                self._timeout_seconds,
            )
            duration = max(0.0, time.monotonic() - started)
            passed = completed.returncode == 0

            return ValidationCommandResult(
                profile=profile,
                command=command,
                passed=passed,
                exit_code=completed.returncode,
                stdout=completed.stdout or "",
                stderr=completed.stderr or "",
                duration_seconds=duration,
                timed_out=False,
            )

        except subprocess.TimeoutExpired as exc:
            duration = max(0.0, time.monotonic() - started)
            stdout = exc.stdout or ""
            stderr = exc.stderr or ""

            if isinstance(stdout, bytes):
                stdout = stdout.decode("utf-8", errors="replace")
            if isinstance(stderr, bytes):
                stderr = stderr.decode("utf-8", errors="replace")

            timeout_message = (
                f"Validation exceeded the {self._timeout_seconds}-second timeout."
            )
            stderr = f"{stderr}\n{timeout_message}".strip()

            logger.warning("Validation profile %s timed out", profile)

            return ValidationCommandResult(
                profile=profile,
                command=command,
                passed=False,
                exit_code=None,
                stdout=stdout,
                stderr=stderr,
                duration_seconds=duration,
                timed_out=True,
            )

        except OSError as exc:
            duration = max(0.0, time.monotonic() - started)
            logger.warning(
                "Could not start validation profile %s: %s",
                profile,
                exc,
            )

            return ValidationCommandResult(
                profile=profile,
                command=command,
                passed=False,
                exit_code=None,
                stdout="",
                stderr=f"Could not start validation command: {exc}",
                duration_seconds=duration,
                timed_out=False,
            )

    def validate(
        self,
        proposal: PatchProposal,
        workspace_path: str | Path,
        profiles: list[str] | None = None,
    ) -> ValidationReport:
        """Run selected validation profiles and return a combined report."""
        workspace = Path(workspace_path).resolve()

        if not workspace.is_dir():
            raise ValueError("workspace_path must point to an existing directory")

        available = self._available_profiles()
        selected_profiles = (
            profiles if profiles is not None else ["python_tests", "python_lint"]
        )

        if not selected_profiles:
            raise ValueError("At least one validation profile is required")

        if len(selected_profiles) != len(set(selected_profiles)):
            raise ValueError("Validation profiles must not contain duplicates")

        unknown = [name for name in selected_profiles if name not in available]
        if unknown:
            raise ValueError(f"Unsupported validation profile(s): {', '.join(unknown)}")

        results = [
            self._run_profile(name, available[name], workspace)
            for name in selected_profiles
        ]

        passed = all(result.passed for result in results)
        failed_profiles = [result.profile for result in results if not result.passed]

        if passed:
            summary = f"All {len(results)} validation profile(s) passed."
        else:
            summary = "Validation failed for: " + ", ".join(failed_profiles)

        return ValidationReport(
            repository_full_name=proposal.repository_full_name,
            issue_number=proposal.issue_number,
            passed=passed,
            results=results,
            summary=summary,
        )
