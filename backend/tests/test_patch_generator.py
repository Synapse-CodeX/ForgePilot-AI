"""Tests for safe patch generation."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from langchain_core.messages import AIMessage, BaseMessage

from backend.app.core.config import Settings
from backend.app.schemas.analysis import AnalyzedFile, RepositoryAnalysis
from backend.app.schemas.root_cause import RootCauseAnalysis, RootCauseEvidence
from backend.app.services.patch_generator import (
    PatchGenerationError,
    PatchGenerator,
)

REPOSITORY = "example/project"
ISSUE_NUMBER = 12
SOURCE_PATH = "src/calculator.py"

VALID_DIFF = """--- a/src/calculator.py
+++ b/src/calculator.py
@@ -1,2 +1,2 @@
 def add(a, b):
-    return a - b
+    return a + b
"""


class FakeGateway:
    """Return a fixed response without making a network request."""

    def __init__(
        self,
        content: str = "",
        error: Exception | None = None,
    ) -> None:
        self.content = content
        self.error = error
        self.messages: list[BaseMessage] | None = None

    def invoke(self, messages: list[BaseMessage]) -> AIMessage:
        self.messages = list(messages)
        if self.error is not None:
            raise self.error
        return AIMessage(content=self.content)


def make_issue() -> SimpleNamespace:
    return SimpleNamespace(
        repository_full_name=REPOSITORY,
        issue_number=ISSUE_NUMBER,
        title="Addition returns the wrong result",
        body="The add function subtracts instead of adding.",
    )


def make_analysis() -> RepositoryAnalysis:
    return RepositoryAnalysis(
        repository_full_name=REPOSITORY,
        issue_number=ISSUE_NUMBER,
        issue_title="Addition returns the wrong result",
        files_scanned=1,
        candidates=[
            AnalyzedFile(
                path=SOURCE_PATH,
                score=10,
                reasons=["The path and function match the issue"],
                definitions=["add"],
                imports=[],
                syntax_valid=True,
            )
        ],
    )


def make_root_cause() -> RootCauseAnalysis:
    return RootCauseAnalysis(
        repository_full_name=REPOSITORY,
        issue_number=ISSUE_NUMBER,
        issue_title="Addition returns the wrong result",
        root_cause="The add function uses subtraction.",
        confidence=0.95,
        summary="Replace subtraction with addition.",
        evidence=[
            RootCauseEvidence(
                file_path=SOURCE_PATH,
                observation="The function returns a - b.",
                code_reference="return a - b",
            )
        ],
        recommended_files=[SOURCE_PATH],
    )


def response_payload(
    unified_diff: str = VALID_DIFF,
    files_changed: list[str] | None = None,
) -> str:
    return json.dumps(
        {
            "summary": "Correct the addition operation.",
            "rationale": "The implementation subtracts the operands.",
            "unified_diff": unified_diff,
            "files_changed": files_changed or [SOURCE_PATH],
        }
    )


def make_generator(
    tmp_path: Path,
    gateway: FakeGateway,
) -> PatchGenerator:
    source = tmp_path / SOURCE_PATH
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(
        "def add(a, b):\n    return a - b\n",
        encoding="utf-8",
    )
    return PatchGenerator(
        settings=Settings(),
        workspace_root=str(tmp_path),
        gateway=gateway,
    )


def test_generates_a_valid_patch_without_modifying_source(
    tmp_path: Path,
) -> None:
    source = tmp_path / SOURCE_PATH
    original = "def add(a, b):\n    return a - b\n"
    source.parent.mkdir(parents=True)
    source.write_text(original, encoding="utf-8")
    gateway = FakeGateway(response_payload())
    generator = PatchGenerator(
        settings=Settings(),
        workspace_root=str(tmp_path),
        gateway=gateway,
    )

    proposal = generator.generate(
        make_issue(),
        make_analysis(),
        make_root_cause(),
    )

    assert proposal.repository_full_name == REPOSITORY
    assert proposal.issue_number == ISSUE_NUMBER
    assert proposal.files_changed == [SOURCE_PATH]
    assert "return a + b" in proposal.unified_diff
    assert source.read_text(encoding="utf-8") == original


def test_accepts_fenced_json_response(tmp_path: Path) -> None:
    content = "```json\n" + response_payload() + "\n```"
    generator = make_generator(tmp_path, FakeGateway(content))

    proposal = generator.generate(
        make_issue(),
        make_analysis(),
        make_root_cause(),
    )

    assert proposal.files_changed == [SOURCE_PATH]


def test_rejects_malformed_json(tmp_path: Path) -> None:
    generator = make_generator(tmp_path, FakeGateway("{not valid json"))

    with pytest.raises(PatchGenerationError, match="malformed JSON"):
        generator.generate(make_issue(), make_analysis(), make_root_cause())


def test_rejects_path_traversal_in_diff(tmp_path: Path) -> None:
    malicious_diff = """--- a/../../outside.py
+++ b/../../outside.py
@@ -1 +1 @@
-old
+new
"""
    generator = make_generator(
        tmp_path,
        FakeGateway(response_payload(malicious_diff, ["../../outside.py"])),
    )

    with pytest.raises(PatchGenerationError, match="unsafe|traversal"):
        generator.generate(make_issue(), make_analysis(), make_root_cause())


def test_rejects_a_file_not_approved_by_the_diagnosis(
    tmp_path: Path,
) -> None:
    other_path = "src/other.py"
    other_diff = """--- a/src/other.py
+++ b/src/other.py
@@ -1 +1 @@
-old
+new
"""
    generator = make_generator(
        tmp_path,
        FakeGateway(response_payload(other_diff, [other_path])),
    )

    with pytest.raises(PatchGenerationError, match="unapproved file"):
        generator.generate(make_issue(), make_analysis(), make_root_cause())


def test_rejects_diff_without_hunks(tmp_path: Path) -> None:
    no_hunk_diff = """--- a/src/calculator.py
+++ b/src/calculator.py
"""
    generator = make_generator(
        tmp_path,
        FakeGateway(response_payload(no_hunk_diff)),
    )

    with pytest.raises(PatchGenerationError, match="no unified-diff hunk"):
        generator.generate(make_issue(), make_analysis(), make_root_cause())


def test_rejects_mismatched_issue_context(tmp_path: Path) -> None:
    generator = make_generator(
        tmp_path,
        FakeGateway(response_payload()),
    )
    wrong_analysis = make_analysis().model_copy(update={"issue_number": 99})

    with pytest.raises(PatchGenerationError, match="Issue contexts do not match"):
        generator.generate(make_issue(), wrong_analysis, make_root_cause())


def test_rejects_files_changed_mismatch(tmp_path: Path) -> None:
    generator = make_generator(
        tmp_path,
        FakeGateway(response_payload(files_changed=["src/other.py"])),
    )

    with pytest.raises(PatchGenerationError, match="does not match"):
        generator.generate(make_issue(), make_analysis(), make_root_cause())


def test_wraps_gateway_failure(tmp_path: Path) -> None:
    generator = make_generator(
        tmp_path,
        FakeGateway(error=RuntimeError("provider unavailable")),
    )

    with pytest.raises(PatchGenerationError, match="could not generate"):
        generator.generate(make_issue(), make_analysis(), make_root_cause())


def test_rejects_invalid_source_file_limits(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="max_source_files"):
        PatchGenerator(
            settings=Settings(),
            workspace_root=str(tmp_path),
            gateway=FakeGateway(response_payload()),
            max_source_files=0,
        )

    with pytest.raises(ValueError, match="max_source_chars"):
        PatchGenerator(
            settings=Settings(),
            workspace_root=str(tmp_path),
            gateway=FakeGateway(response_payload()),
            max_source_chars=0,
        )
