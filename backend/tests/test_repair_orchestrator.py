"""Tests for the repair orchestrator using isolated fake services."""

from pathlib import Path
from typing import Any

import pytest

from backend.app.core.config import Settings
from backend.app.schemas import (
    AnalyzedFile,
    IssueContext,
    PatchApplicationResult,
    PatchProposal,
    RepositoryAnalysis,
    RepositoryContext,
    RootCauseAnalysis,
    RootCauseEvidence,
    ValidationCommandResult,
    ValidationReport,
)
from backend.app.services.repair_orchestrator import RepairOrchestrator

REPOSITORY_NAME = "example/project"
ISSUE_NUMBER = 12


def make_repository() -> RepositoryContext:
    return RepositoryContext(
        owner="example",
        name="project",
        full_name=REPOSITORY_NAME,
        html_url="https://github.com/example/project",
        default_branch="main",
        language="Python",
    )


def make_issue() -> IssueContext:
    return IssueContext(
        repository_full_name=REPOSITORY_NAME,
        number=ISSUE_NUMBER,
        title="Fix the calculation",
        body="The calculation returns the wrong result.",
        state="open",
        html_url="https://github.com/example/project/issues/12",
        labels=["bug"],
    )


def make_analysis() -> RepositoryAnalysis:
    return RepositoryAnalysis(
        repository_full_name=REPOSITORY_NAME,
        issue_number=ISSUE_NUMBER,
        issue_title="Fix the calculation",
        files_scanned=3,
        candidates=[
            AnalyzedFile(
                path="src/calculator.py",
                score=10,
                reasons=["Path matches issue terms: calculation"],
                definitions=["calculate"],
                imports=[],
                syntax_valid=True,
            )
        ],
    )


def make_root_cause() -> RootCauseAnalysis:
    return RootCauseAnalysis(
        repository_full_name=REPOSITORY_NAME,
        issue_number=ISSUE_NUMBER,
        issue_title="Fix the calculation",
        root_cause="The calculation uses the wrong operation.",
        confidence=0.9,
        summary="Correct the arithmetic operation.",
        evidence=[
            RootCauseEvidence(
                file_path="src/calculator.py",
                observation="The operation does not match the expected behavior.",
                code_reference="calculate",
            )
        ],
        recommended_files=["src/calculator.py"],
    )


def make_patch() -> PatchProposal:
    return PatchProposal(
        repository_full_name=REPOSITORY_NAME,
        issue_number=ISSUE_NUMBER,
        summary="Correct the calculation",
        rationale="Use the intended arithmetic operation.",
        unified_diff=(
            "--- a/src/calculator.py\n"
            "+++ b/src/calculator.py\n"
            "@@ -1,2 +1,2 @@\n"
            "-    return left - right\n"
            "+    return left + right\n"
        ),
        files_changed=["src/calculator.py"],
    )


def make_application() -> PatchApplicationResult:
    return PatchApplicationResult(
        repository_full_name=REPOSITORY_NAME,
        issue_number=ISSUE_NUMBER,
        applied=True,
        files_changed=["src/calculator.py"],
        message="Patch applied successfully.",
    )


def make_validation(passed: bool = True) -> ValidationReport:
    return ValidationReport(
        repository_full_name=REPOSITORY_NAME,
        issue_number=ISSUE_NUMBER,
        passed=passed,
        results=[
            ValidationCommandResult(
                profile="python_tests",
                command=["python", "-m", "pytest", "-q"],
                passed=passed,
                exit_code=0 if passed else 1,
                stdout="Tests completed.",
                stderr="" if passed else "One test failed.",
                duration_seconds=0.1,
            )
        ],
        summary=(
            "All 1 validation profile(s) passed."
            if passed
            else "Validation failed for: python_tests"
        ),
    )


class FakeGitHubService:
    """Return predictable GitHub contexts without network access."""

    async def get_repository(self, owner: str, repo: str) -> RepositoryContext:
        return make_repository()

    async def get_issue(self, owner: str, repo: str, issue_number: int) -> IssueContext:
        return make_issue()


class FakeRepositoryAnalyst:
    def __init__(self, **kwargs: Any) -> None:
        pass

    def analyze(self, issue: IssueContext) -> RepositoryAnalysis:
        return make_analysis()


class FakeRootCauseAnalyzer:
    def __init__(self, **kwargs: Any) -> None:
        pass

    def analyze(
        self, issue: IssueContext, repository_analysis: RepositoryAnalysis
    ) -> RootCauseAnalysis:
        return make_root_cause()


class FakePatchGenerator:
    def __init__(self, **kwargs: Any) -> None:
        pass

    def generate(
        self,
        issue: IssueContext,
        repository_analysis: RepositoryAnalysis,
        root_cause: RootCauseAnalysis,
    ) -> PatchProposal:
        return make_patch()


class FakePatchApplier:
    def __init__(self, **kwargs: Any) -> None:
        pass

    def apply(self, proposal: PatchProposal) -> PatchApplicationResult:
        return make_application()


class FakePatchValidator:
    def __init__(self, **kwargs: Any) -> None:
        pass

    def validate(
        self,
        proposal: PatchProposal,
        workspace_path: str | Path,
        profiles: list[str] | None = None,
    ) -> ValidationReport:
        return make_validation()


def make_orchestrator(
    *,
    validator_factory: Any = FakePatchValidator,
    root_cause_factory: Any = FakeRootCauseAnalyzer,
) -> RepairOrchestrator:
    return RepairOrchestrator(
        settings=Settings(sandbox_timeout=5),
        github_service=FakeGitHubService(),  # type: ignore[arg-type]
        repository_analyst_factory=FakeRepositoryAnalyst,
        root_cause_analyzer_factory=root_cause_factory,
        patch_generator_factory=FakePatchGenerator,
        patch_applier_factory=FakePatchApplier,
        patch_validator_factory=validator_factory,
    )


@pytest.mark.asyncio
async def test_complete_workflow_succeeds(tmp_path: Path) -> None:
    orchestrator = make_orchestrator()

    result = await orchestrator.run(
        "example",
        "project",
        ISSUE_NUMBER,
        tmp_path,
    )

    assert result.status == "succeeded"
    assert result.repository == make_repository()
    assert result.issue == make_issue()
    assert result.repository_analysis == make_analysis()
    assert result.root_cause == make_root_cause()
    assert result.patch_proposal == make_patch()
    assert result.patch_application == make_application()
    assert result.validation_report == make_validation()
    assert [stage.stage for stage in result.stages] == [
        "github_context",
        "repository_analysis",
        "root_cause_analysis",
        "patch_generation",
        "patch_application",
        "patch_validation",
    ]
    assert all(stage.status == "succeeded" for stage in result.stages)


@pytest.mark.asyncio
async def test_validation_failure_is_not_reported_as_success(
    tmp_path: Path,
) -> None:
    class FailingValidator(FakePatchValidator):
        def validate(
            self,
            proposal: PatchProposal,
            workspace_path: str | Path,
            profiles: list[str] | None = None,
        ) -> ValidationReport:
            return make_validation(passed=False)

    orchestrator = make_orchestrator(validator_factory=FailingValidator)

    result = await orchestrator.run(
        "example",
        "project",
        ISSUE_NUMBER,
        tmp_path,
    )

    assert result.status == "validation_failed"
    assert result.patch_application is not None
    assert result.patch_application.applied is True
    assert result.validation_report is not None
    assert result.validation_report.passed is False
    assert result.stages[-1].status == "failed"


@pytest.mark.asyncio
async def test_root_cause_failure_stops_before_patch_generation(
    tmp_path: Path,
) -> None:
    class FailingRootCauseAnalyzer:
        def __init__(self, **kwargs: Any) -> None:
            pass

        def analyze(
            self,
            issue: IssueContext,
            repository_analysis: RepositoryAnalysis,
        ) -> RootCauseAnalysis:
            raise RuntimeError("Diagnosis unavailable")

    orchestrator = make_orchestrator(root_cause_factory=FailingRootCauseAnalyzer)

    result = await orchestrator.run(
        "example",
        "project",
        ISSUE_NUMBER,
        tmp_path,
    )

    assert result.status == "failed"
    assert result.repository_analysis is not None
    assert result.root_cause is None
    assert result.patch_proposal is None
    assert result.patch_application is None
    assert result.validation_report is None
    assert result.stages[-1].stage == "root_cause_analysis"
    assert result.stages[-1].status == "failed"
    assert result.stages[-1].error_type == "RuntimeError"


@pytest.mark.asyncio
async def test_missing_workspace_stops_before_github_calls(
    tmp_path: Path,
) -> None:
    orchestrator = make_orchestrator()

    result = await orchestrator.run(
        "example",
        "project",
        ISSUE_NUMBER,
        tmp_path / "does-not-exist",
    )

    assert result.status == "failed"
    assert result.stages[-1].stage == "workspace_validation"
    assert result.repository is None
    assert result.issue is None


@pytest.mark.asyncio
async def test_invalid_issue_number_is_rejected(tmp_path: Path) -> None:
    orchestrator = make_orchestrator()

    result = await orchestrator.run(
        "example",
        "project",
        0,
        tmp_path,
    )

    assert result.status == "failed"
    assert result.stages[-1].stage == "input_validation"
    assert result.stages[-1].error_type == "ValueError"
