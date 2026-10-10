"""Tests for issue-driven repository analysis."""

from pathlib import Path

import pytest

from backend.app.core.config import Settings
from backend.app.schemas import IssueContext
from backend.app.services.repository_analyst import RepositoryAnalyst


def create_issue(
    title: str = "Application crashes during startup",
    body: str = "The startup process fails.",
    labels: list[str] | None = None,
) -> IssueContext:
    """Create a representative issue context."""

    return IssueContext(
        repository_full_name="octocat/hello-world",
        number=42,
        title=title,
        body=body,
        state="open",
        html_url="https://github.com/octocat/hello-world/issues/42",
        labels=labels or [],
    )


def create_analyst(workspace: Path) -> RepositoryAnalyst:
    """Create an analyst using a temporary repository workspace."""

    settings = Settings(
        repository_workspace_root=str(workspace),
        max_inspected_file_bytes=1_000_000,
    )
    return RepositoryAnalyst(settings=settings)


def test_analyze_ranks_issue_relevant_file_first(tmp_path: Path) -> None:
    """Test that matching file paths receive higher relevance scores."""

    (tmp_path / "startup_handler.py").write_text(
        "def initialize_application():\n    raise RuntimeError('startup failed')\n",
        encoding="utf-8",
    )
    (tmp_path / "helpers.py").write_text(
        "def format_number(value):\n    return str(value)\n",
        encoding="utf-8",
    )

    analyst = create_analyst(tmp_path)
    result = analyst.analyze(create_issue())

    assert result.files_scanned == 2
    assert result.candidates
    assert result.candidates[0].path == "startup_handler.py"
    assert result.candidates[0].score > 0


def test_analyze_extracts_definitions_and_imports(tmp_path: Path) -> None:
    """Test AST extraction for a relevant Python file."""

    (tmp_path / "startup.py").write_text(
        "import logging\n"
        "from pathlib import Path\n\n"
        "def startup_application():\n"
        "    return Path('.')\n",
        encoding="utf-8",
    )

    analyst = create_analyst(tmp_path)
    result = analyst.analyze(create_issue())

    candidate = next(item for item in result.candidates if item.path == "startup.py")

    assert "startup_application" in candidate.definitions
    assert "logging" in candidate.imports
    assert "pathlib" in candidate.imports
    assert candidate.syntax_valid is True


def test_analyze_excludes_generated_directories(tmp_path: Path) -> None:
    """Test that generated and dependency directories are ignored."""

    source = tmp_path / "startup.py"
    source.write_text("def startup():\n    pass\n", encoding="utf-8")

    excluded_file = tmp_path / ".venv" / "startup.py"
    excluded_file.parent.mkdir()
    excluded_file.write_text("def startup():\n    pass\n", encoding="utf-8")

    node_file = tmp_path / "node_modules" / "startup.py"
    node_file.parent.mkdir()
    node_file.write_text("def startup():\n    pass\n", encoding="utf-8")

    analyst = create_analyst(tmp_path)
    result = analyst.analyze(create_issue())

    paths = [candidate.path for candidate in result.candidates]

    assert result.files_scanned == 1
    assert paths == ["startup.py"]


def test_analyze_reports_invalid_python_syntax(tmp_path: Path) -> None:
    """Test that syntax errors are reported without crashing analysis."""

    (tmp_path / "startup.py").write_text(
        "def startup_application(:\n    pass\n",
        encoding="utf-8",
    )

    analyst = create_analyst(tmp_path)
    result = analyst.analyze(create_issue())

    assert result.files_scanned == 1
    assert len(result.candidates) == 1
    assert result.candidates[0].syntax_valid is False
    assert any(
        "syntax could not be parsed" in reason
        for reason in result.candidates[0].reasons
    )


def test_analyze_returns_empty_candidates_without_matches(
    tmp_path: Path,
) -> None:
    """Test that unrelated files are not presented as relevant candidates."""

    (tmp_path / "formatting.py").write_text(
        "def format_currency(amount):\n    return str(amount)\n",
        encoding="utf-8",
    )

    analyst = create_analyst(tmp_path)
    result = analyst.analyze(
        create_issue(
            title="Database connection timeout",
            body="The connection pool cannot reach the database.",
        )
    )

    assert result.files_scanned == 1
    assert result.candidates == []


def test_analyze_respects_candidate_limit(tmp_path: Path) -> None:
    """Test that the number of returned candidates is bounded."""

    for filename in (
        "startup.py",
        "startup_service.py",
        "startup_handler.py",
    ):
        (tmp_path / filename).write_text(
            "def startup_application():\n    pass\n",
            encoding="utf-8",
        )

    analyst = create_analyst(tmp_path)
    result = analyst.analyze(create_issue(), max_candidates=2)

    assert len(result.candidates) == 2


def test_analyze_rejects_invalid_candidate_limit(tmp_path: Path) -> None:
    """Test that candidate limits must be positive."""

    analyst = create_analyst(tmp_path)

    with pytest.raises(ValueError, match="at least 1"):
        analyst.analyze(create_issue(), max_candidates=0)


def test_analyze_rejects_missing_workspace(tmp_path: Path) -> None:
    """Test that analysis requires an existing workspace."""

    analyst = create_analyst(tmp_path / "missing")

    with pytest.raises(ValueError, match="workspace does not exist"):
        analyst.analyze(create_issue())
