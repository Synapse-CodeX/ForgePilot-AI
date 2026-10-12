"""Tests for automated patch validation."""

import subprocess
from pathlib import Path

import pytest

from backend.app.schemas.patch import PatchProposal
from backend.app.services.patch_validator import PatchValidator


def make_proposal() -> PatchProposal:
    return PatchProposal(
        repository_full_name="example/project",
        issue_number=12,
        summary="Fix the calculation.",
        rationale="The operation was incorrect.",
        unified_diff=(
            "--- a/src/calculator.py\n"
            "+++ b/src/calculator.py\n"
            "@@ -1 +1 @@\n"
            "-return a - b\n"
            "+return a + b\n"
        ),
        files_changed=["src/calculator.py"],
    )


def successful_runner(
    command: list[str],
    workspace: Path,
    timeout_seconds: int,
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=command,
        returncode=0,
        stdout="All checks passed",
        stderr="",
    )


def test_all_selected_profiles_pass(tmp_path: Path) -> None:
    commands_seen: list[list[str]] = []

    def runner(
        command: list[str],
        workspace: Path,
        timeout_seconds: int,
    ) -> subprocess.CompletedProcess[str]:
        commands_seen.append(command)
        assert workspace == tmp_path.resolve()
        assert timeout_seconds == 30
        return successful_runner(command, workspace, timeout_seconds)

    validator = PatchValidator(
        timeout_seconds=30,
        command_runner=runner,
    )

    report = validator.validate(
        make_proposal(),
        tmp_path,
        profiles=["python_tests", "python_lint"],
    )

    assert report.passed is True
    assert len(report.results) == 2
    assert all(result.passed for result in report.results)
    assert report.repository_full_name == "example/project"
    assert report.issue_number == 12
    assert "All 2 validation profile(s) passed" in report.summary
    assert len(commands_seen) == 2


def test_failed_command_produces_failed_report(tmp_path: Path) -> None:
    def runner(
        command: list[str],
        workspace: Path,
        timeout_seconds: int,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=command,
            returncode=1,
            stdout="2 tests collected",
            stderr="1 test failed",
        )

    validator = PatchValidator(command_runner=runner)
    report = validator.validate(
        make_proposal(),
        tmp_path,
        profiles=["python_tests"],
    )

    assert report.passed is False
    assert report.results[0].passed is False
    assert report.results[0].exit_code == 1
    assert report.results[0].stdout == "2 tests collected"
    assert report.results[0].stderr == "1 test failed"
    assert "python_tests" in report.summary


def test_timeout_is_reported(tmp_path: Path) -> None:
    def runner(
        command: list[str],
        workspace: Path,
        timeout_seconds: int,
    ) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(
            cmd=command,
            timeout=timeout_seconds,
            output="Partial output",
            stderr="Still running",
        )

    validator = PatchValidator(
        timeout_seconds=2,
        command_runner=runner,
    )
    report = validator.validate(
        make_proposal(),
        tmp_path,
        profiles=["python_tests"],
    )

    result = report.results[0]
    assert report.passed is False
    assert result.timed_out is True
    assert result.exit_code is None
    assert result.stdout == "Partial output"
    assert "timeout" in result.stderr.lower()


def test_missing_command_is_reported(tmp_path: Path) -> None:
    def runner(
        command: list[str],
        workspace: Path,
        timeout_seconds: int,
    ) -> subprocess.CompletedProcess[str]:
        raise FileNotFoundError("ruff executable not found")

    validator = PatchValidator(command_runner=runner)
    report = validator.validate(
        make_proposal(),
        tmp_path,
        profiles=["python_lint"],
    )

    assert report.passed is False
    assert report.results[0].exit_code is None
    assert "Could not start" in report.results[0].stderr


def test_rejects_unknown_profile(tmp_path: Path) -> None:
    validator = PatchValidator(command_runner=successful_runner)

    with pytest.raises(ValueError, match="Unsupported validation profile"):
        validator.validate(
            make_proposal(),
            tmp_path,
            profiles=["run-arbitrary-command"],
        )


def test_rejects_empty_profile_list(tmp_path: Path) -> None:
    validator = PatchValidator(command_runner=successful_runner)

    with pytest.raises(ValueError, match="At least one"):
        validator.validate(
            make_proposal(),
            tmp_path,
            profiles=[],
        )


def test_rejects_invalid_timeout() -> None:
    with pytest.raises(ValueError, match="timeout_seconds"):
        PatchValidator(timeout_seconds=0)


def test_rejects_nonexistent_workspace(tmp_path: Path) -> None:
    validator = PatchValidator(command_runner=successful_runner)

    with pytest.raises(ValueError, match="existing directory"):
        validator.validate(
            make_proposal(),
            tmp_path / "does-not-exist",
        )
