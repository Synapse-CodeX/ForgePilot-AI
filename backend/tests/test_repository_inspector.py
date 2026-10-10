"""Tests for safe repository file inspection."""

from pathlib import Path

import pytest

from backend.app.core.config import Settings
from backend.app.services.repository_inspector import (
    InspectedFile,
    RepositoryInspectionError,
    RepositoryInspector,
)


def create_inspector(
    workspace: Path,
    max_file_size_bytes: int = 1_000_000,
) -> RepositoryInspector:
    """Create an inspector configured for a temporary workspace."""

    settings = Settings(
        repository_workspace_root=str(workspace),
        max_inspected_file_bytes=max_file_size_bytes,
    )
    return RepositoryInspector(settings=settings)


def test_read_file_returns_content_and_metadata(tmp_path: Path) -> None:
    """Test reading a UTF-8 source file."""

    source_file = tmp_path / "example.py"
    source_file.write_text("def answer():\n    return 42\n", encoding="utf-8")
    inspector = create_inspector(tmp_path)

    result = inspector.read_file("example.py")

    assert isinstance(result, InspectedFile)
    assert result.path == "example.py"
    assert result.content == "def answer():\n    return 42\n"
    assert result.size_bytes == source_file.stat().st_size
    assert result.line_count == 2


def test_read_file_supports_nested_paths(tmp_path: Path) -> None:
    """Test reading a file in a nested directory."""

    source_file = tmp_path / "src" / "utils.py"
    source_file.parent.mkdir()
    source_file.write_text("VALUE = 7\n", encoding="utf-8")
    inspector = create_inspector(tmp_path)

    result = inspector.read_file("src/utils.py")

    assert result.path == "src/utils.py"
    assert result.content == "VALUE = 7\n"


def test_missing_file_is_rejected(tmp_path: Path) -> None:
    """Test that a missing file produces a controlled error."""

    inspector = create_inspector(tmp_path)

    with pytest.raises(
        RepositoryInspectionError,
        match="could not be resolved",
    ):
        inspector.read_file("missing.py")


def test_path_traversal_is_rejected(tmp_path: Path) -> None:
    """Test that paths escaping the workspace are rejected."""

    outside_file = tmp_path.parent / "outside.py"
    outside_file.write_text("SECRET = True\n", encoding="utf-8")
    inspector = create_inspector(tmp_path)

    try:
        with pytest.raises(
            RepositoryInspectionError,
            match="outside the repository workspace",
        ):
            inspector.read_file("../outside.py")
    finally:
        outside_file.unlink(missing_ok=True)


def test_absolute_path_is_rejected(tmp_path: Path) -> None:
    """Test that absolute paths are not accepted."""

    source_file = tmp_path / "example.py"
    source_file.write_text("VALUE = 1\n", encoding="utf-8")
    inspector = create_inspector(tmp_path)

    with pytest.raises(
        RepositoryInspectionError,
        match="Absolute file paths",
    ):
        inspector.read_file(str(source_file))


def test_directory_is_rejected(tmp_path: Path) -> None:
    """Test that a directory cannot be read as a source file."""

    (tmp_path / "src").mkdir()
    inspector = create_inspector(tmp_path)

    with pytest.raises(
        RepositoryInspectionError,
        match="not a regular file",
    ):
        inspector.read_file("src")


def test_oversized_file_is_rejected(tmp_path: Path) -> None:
    """Test enforcement of the configured file-size limit."""

    source_file = tmp_path / "large.py"
    source_file.write_text("X" * 20, encoding="utf-8")
    inspector = create_inspector(tmp_path, max_file_size_bytes=10)

    with pytest.raises(
        RepositoryInspectionError,
        match="exceeds the configured size limit",
    ):
        inspector.read_file("large.py")


def test_non_utf8_file_is_rejected(tmp_path: Path) -> None:
    """Test that binary or non-UTF-8 content is rejected."""

    source_file = tmp_path / "binary.dat"
    source_file.write_bytes(b"\xff\xfe\xfa")
    inspector = create_inspector(tmp_path)

    with pytest.raises(
        RepositoryInspectionError,
        match="not valid UTF-8 text",
    ):
        inspector.read_file("binary.dat")
