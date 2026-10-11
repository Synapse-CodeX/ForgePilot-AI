"""Tests for safe Git patch application."""

import subprocess
from pathlib import Path

import pytest

from backend.app.schemas.patch import PatchProposal
from backend.app.services.patch_applier import (
    PatchApplicationError,
    PatchApplier,
)

REPOSITORY = "example/project"
ISSUE_NUMBER = 12
SOURCE_PATH = "src/calculator.py"

ORIGINAL_SOURCE = "def add(a, b):\n    return a - b\n"

VALID_DIFF = """--- a/src/calculator.py
+++ b/src/calculator.py
@@ -1,2 +1,2 @@
 def add(a, b):
-    return a - b
+    return a + b
"""


def create_git_repository(tmp_path: Path) -> Path:
    """Create a clean local Git repository with one committed source file."""
    source = tmp_path / SOURCE_PATH
    source.parent.mkdir(parents=True)
    source.write_text(ORIGINAL_SOURCE, encoding="utf-8")

    subprocess.run(
        ["git", "init", "-q"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "ForgePilot Tests"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "forgepilot-tests@example.com"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "add", SOURCE_PATH],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Add calculator"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )

    return tmp_path


def make_proposal(
    unified_diff: str = VALID_DIFF,
    files_changed: list[str] | None = None,
) -> PatchProposal:
    return PatchProposal(
        repository_full_name=REPOSITORY,
        issue_number=ISSUE_NUMBER,
        summary="Correct the addition operation.",
        rationale="The implementation subtracts the operands.",
        unified_diff=unified_diff,
        files_changed=files_changed or [SOURCE_PATH],
    )


def test_applies_valid_patch_to_clean_repository(tmp_path: Path) -> None:
    repository = create_git_repository(tmp_path)
    applier = PatchApplier(repository)

    result = applier.apply(make_proposal())

    source = repository / SOURCE_PATH
    assert result.applied is True
    assert result.repository_full_name == REPOSITORY
    assert result.issue_number == ISSUE_NUMBER
    assert result.files_changed == [SOURCE_PATH]
    assert source.read_text(encoding="utf-8") == ("def add(a, b):\n    return a + b\n")


def test_rejects_non_git_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    applier = PatchApplier(tmp_path)

    def mock_git_failure(
        arguments: list[str],
        *,
        input_text: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=["git", *arguments],
            returncode=128,
            stdout="",
            stderr="fatal: not a git repository",
        )

    monkeypatch.setattr(applier, "_run_git", mock_git_failure)

    with pytest.raises(PatchApplicationError, match="not a Git repository"):
        applier.apply(make_proposal())


def test_rejects_dirty_worktree_without_modifying_source(
    tmp_path: Path,
) -> None:
    repository = create_git_repository(tmp_path)
    source = repository / SOURCE_PATH
    source.write_text("user's uncommitted change\n", encoding="utf-8")
    before = source.read_text(encoding="utf-8")

    with pytest.raises(PatchApplicationError, match="must be clean"):
        PatchApplier(repository).apply(make_proposal())

    assert source.read_text(encoding="utf-8") == before


def test_rejects_path_traversal(tmp_path: Path) -> None:
    repository = create_git_repository(tmp_path)
    malicious_diff = """--- a/../../outside.py
+++ b/../../outside.py
@@ -1 +1 @@
-old
+new
"""
    proposal = make_proposal(
        unified_diff=malicious_diff,
        files_changed=["../../outside.py"],
    )

    with pytest.raises(PatchApplicationError, match="traversal|unsafe"):
        PatchApplier(repository).apply(proposal)


def test_rejects_undeclared_target_path(tmp_path: Path) -> None:
    repository = create_git_repository(tmp_path)
    other_diff = """--- a/src/calculator.py
+++ b/src/calculator.py
@@ -1,2 +1,2 @@
 def add(a, b):
-    return a - b
+    return a + b
"""
    proposal = make_proposal(
        unified_diff=other_diff,
        files_changed=["src/other.py"],
    )

    with pytest.raises(PatchApplicationError, match="undeclared"):
        PatchApplier(repository).apply(proposal)


def test_rejects_patch_that_does_not_apply(tmp_path: Path) -> None:
    repository = create_git_repository(tmp_path)
    invalid_diff = """--- a/src/calculator.py
+++ b/src/calculator.py
@@ -1,2 +1,2 @@
 def add(a, b):
-    return a * b
+    return a + b
"""
    proposal = make_proposal(unified_diff=invalid_diff)
    source = repository / SOURCE_PATH
    before = source.read_text(encoding="utf-8")

    with pytest.raises(PatchApplicationError, match="preflight"):
        PatchApplier(repository).apply(proposal)

    assert source.read_text(encoding="utf-8") == before


def test_rejects_file_rename(tmp_path: Path) -> None:
    repository = create_git_repository(tmp_path)
    rename_diff = """--- a/src/calculator.py
+++ b/src/renamed.py
@@ -1,2 +1,2 @@
 def add(a, b):
-    return a - b
+    return a + b
"""
    proposal = make_proposal(
        unified_diff=rename_diff,
        files_changed=["src/calculator.py"],
    )

    with pytest.raises(PatchApplicationError, match="renaming"):
        PatchApplier(repository).apply(proposal)


def test_rejects_invalid_timeout(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="git_timeout_seconds"):
        PatchApplier(tmp_path, git_timeout_seconds=0)
