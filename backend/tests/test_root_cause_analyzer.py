"""Tests for the root-cause analysis service."""

from collections.abc import Sequence
from pathlib import Path

import pytest
from langchain_core.messages import AIMessage, BaseMessage

from backend.app.core.config import Settings
from backend.app.schemas import (
    AnalyzedFile,
    IssueContext,
    RepositoryAnalysis,
)
from backend.app.services.root_cause_analyzer import (
    RootCauseAnalysisError,
    RootCauseAnalyzer,
)


class FakeGateway:
    """Fake LLM gateway for deterministic offline tests."""

    def __init__(
        self,
        content: str = "",
        error: Exception | None = None,
    ) -> None:
        self.content = content
        self.error = error
        self.received_messages: Sequence[BaseMessage] | None = None

    def invoke(self, messages: Sequence[BaseMessage]) -> AIMessage:
        """Return a controlled response or simulate a provider failure."""

        self.received_messages = messages

        if self.error is not None:
            raise self.error

        return AIMessage(content=self.content)


def create_issue() -> IssueContext:
    """Create a representative GitHub issue."""

    return IssueContext(
        repository_full_name="octocat/hello-world",
        number=42,
        title="Application crashes during startup",
        body="The application raises an error during initialization.",
        state="open",
        html_url="https://github.com/octocat/hello-world/issues/42",
        labels=["bug"],
    )


def create_repository_analysis() -> RepositoryAnalysis:
    """Create a ranked candidate list for the issue."""

    return RepositoryAnalysis(
        repository_full_name="octocat/hello-world",
        issue_number=42,
        issue_title="Application crashes during startup",
        files_scanned=2,
        candidates=[
            AnalyzedFile(
                path="startup.py",
                score=10,
                reasons=["Path matches issue terms: startup"],
                definitions=["initialize_application"],
                imports=["logging"],
                syntax_valid=True,
            ),
            AnalyzedFile(
                path="helpers.py",
                score=2,
                reasons=["Code identifiers match issue terms"],
                definitions=["format_value"],
                imports=[],
                syntax_valid=True,
            ),
        ],
    )


def valid_response() -> str:
    """Return a representative structured diagnosis."""

    return (
        "{"
        '"root_cause": "Initialization fails when startup configuration '
        'is processed.", '
        '"confidence": 0.78, '
        '"summary": "The startup initialization path is the strongest '
        'candidate based on the available source.", '
        '"evidence": ['
        "{"
        '"file_path": "startup.py", '
        '"observation": "The file contains the application initialization '
        'function.", '
        '"code_reference": "initialize_application"'
        "}"
        "], "
        '"recommended_files": ["startup.py"]'
        "}"
    )


def create_analyzer(
    workspace: Path,
    gateway: FakeGateway,
) -> RootCauseAnalyzer:
    """Create an analyzer using a temporary local workspace."""

    settings = Settings(
        repository_workspace_root=str(workspace),
        max_inspected_file_bytes=1_000_000,
    )

    return RootCauseAnalyzer(
        settings=settings,
        gateway=gateway,
    )


def test_analyze_returns_structured_diagnosis(tmp_path: Path) -> None:
    """Test successful diagnosis with a fake model response."""

    (tmp_path / "startup.py").write_text(
        "import logging\n\n"
        "def initialize_application():\n"
        "    logging.info('starting')\n",
        encoding="utf-8",
    )

    gateway = FakeGateway(content=valid_response())
    analyzer = create_analyzer(tmp_path, gateway)

    result = analyzer.analyze(
        create_issue(),
        create_repository_analysis(),
    )

    assert result.repository_full_name == "octocat/hello-world"
    assert result.issue_number == 42
    assert result.root_cause.startswith("Initialization fails")
    assert result.confidence == 0.78
    assert result.evidence[0].file_path == "startup.py"
    assert result.recommended_files == ["startup.py"]
    assert gateway.received_messages is not None


def test_analyze_accepts_json_in_markdown_fence(tmp_path: Path) -> None:
    """Test parsing a JSON response wrapped in a Markdown code fence."""

    (tmp_path / "startup.py").write_text(
        "def initialize_application():\n    pass\n",
        encoding="utf-8",
    )

    response = f"```json\n{valid_response()}\n```"
    analyzer = create_analyzer(
        tmp_path,
        FakeGateway(content=response),
    )

    result = analyzer.analyze(
        create_issue(),
        create_repository_analysis(),
    )

    assert result.recommended_files == ["startup.py"]


def test_analyze_rejects_invalid_json(tmp_path: Path) -> None:
    """Test handling of malformed LLM output."""

    (tmp_path / "startup.py").write_text(
        "def initialize_application():\n    pass\n",
        encoding="utf-8",
    )

    analyzer = create_analyzer(
        tmp_path,
        FakeGateway(content="This is not JSON."),
    )

    with pytest.raises(
        RootCauseAnalysisError,
        match="did not contain a valid JSON object",
    ):
        analyzer.analyze(create_issue(), create_repository_analysis())


def test_analyze_rejects_invalid_diagnosis_schema(tmp_path: Path) -> None:
    """Test handling of JSON missing required diagnosis fields."""

    (tmp_path / "startup.py").write_text(
        "def initialize_application():\n    pass\n",
        encoding="utf-8",
    )

    analyzer = create_analyzer(
        tmp_path,
        FakeGateway(content='{"root_cause": "Incomplete response"}'),
    )

    with pytest.raises(
        RootCauseAnalysisError,
        match="did not match the diagnosis schema",
    ):
        analyzer.analyze(create_issue(), create_repository_analysis())


def test_analyze_rejects_unprovided_evidence_path(tmp_path: Path) -> None:
    """Test that evidence cannot refer to a file absent from the prompt."""

    (tmp_path / "startup.py").write_text(
        "def initialize_application():\n    pass\n",
        encoding="utf-8",
    )

    response = valid_response().replace(
        '"file_path": "startup.py"',
        '"file_path": "secrets.py"',
    )

    analyzer = create_analyzer(
        tmp_path,
        FakeGateway(content=response),
    )

    with pytest.raises(
        RootCauseAnalysisError,
        match="file that was not supplied",
    ):
        analyzer.analyze(create_issue(), create_repository_analysis())


def test_analyze_rejects_unprovided_recommendation(tmp_path: Path) -> None:
    """Test that recommended paths must belong to supplied source files."""

    (tmp_path / "startup.py").write_text(
        "def initialize_application():\n    pass\n",
        encoding="utf-8",
    )

    response = valid_response().replace(
        '"recommended_files": ["startup.py"]',
        '"recommended_files": ["unknown.py"]',
    )

    analyzer = create_analyzer(
        tmp_path,
        FakeGateway(content=response),
    )

    with pytest.raises(
        RootCauseAnalysisError,
        match="recommended an unavailable source file",
    ):
        analyzer.analyze(create_issue(), create_repository_analysis())


def test_analyze_rejects_mismatched_issue(tmp_path: Path) -> None:
    """Test that issue and repository-analysis identifiers must match."""

    analyzer = create_analyzer(
        tmp_path,
        FakeGateway(content=valid_response()),
    )
    mismatched_issue = create_issue().model_copy(update={"number": 99})

    with pytest.raises(
        RootCauseAnalysisError,
        match="identifiers do not match",
    ):
        analyzer.analyze(mismatched_issue, create_repository_analysis())


def test_analyze_rejects_missing_candidate_sources(tmp_path: Path) -> None:
    """Test that analysis fails when no candidate files can be read."""

    analyzer = create_analyzer(
        tmp_path,
        FakeGateway(content=valid_response()),
    )

    with pytest.raises(
        RootCauseAnalysisError,
        match="No readable candidate source files",
    ):
        analyzer.analyze(create_issue(), create_repository_analysis())


def test_analyze_wraps_gateway_failure(tmp_path: Path) -> None:
    """Test that gateway failures become controlled analysis errors."""

    (tmp_path / "startup.py").write_text(
        "def initialize_application():\n    pass\n",
        encoding="utf-8",
    )

    analyzer = create_analyzer(
        tmp_path,
        FakeGateway(error=RuntimeError("simulated provider failure")),
    )

    with pytest.raises(
        RootCauseAnalysisError,
        match="LLM request failed",
    ):
        analyzer.analyze(create_issue(), create_repository_analysis())


def test_analyzer_rejects_invalid_source_limits(tmp_path: Path) -> None:
    """Test validation of analyzer resource limits."""

    settings = Settings(repository_workspace_root=str(tmp_path))

    with pytest.raises(ValueError, match="max_source_files"):
        RootCauseAnalyzer(
            settings=settings,
            gateway=FakeGateway(content=valid_response()),
            max_source_files=0,
        )

    with pytest.raises(ValueError, match="max_source_chars"):
        RootCauseAnalyzer(
            settings=settings,
            gateway=FakeGateway(content=valid_response()),
            max_source_chars=0,
        )
