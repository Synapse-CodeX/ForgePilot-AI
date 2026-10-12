"""Coordinate the services that implement one repository repair attempt."""

import logging
import time
from collections.abc import Callable
from pathlib import Path
from typing import Literal

from backend.app.core.config import Settings, get_settings
from backend.app.schemas.analysis import RepositoryAnalysis
from backend.app.schemas.issue import IssueContext
from backend.app.schemas.patch import PatchApplicationResult, PatchProposal
from backend.app.schemas.repository import RepositoryContext
from backend.app.schemas.root_cause import RootCauseAnalysis
from backend.app.schemas.validation import ValidationReport
from backend.app.schemas.workflow import (
    RepairWorkflowResult,
    WorkflowStageResult,
)
from backend.app.services.github import GitHubService
from backend.app.services.patch_applier import PatchApplier
from backend.app.services.patch_generator import PatchGenerator
from backend.app.services.patch_validator import PatchValidator
from backend.app.services.repository_analyst import RepositoryAnalyst
from backend.app.services.root_cause_analyzer import RootCauseAnalyzer

logger = logging.getLogger("forgepilot.repair_orchestrator")

RepositoryAnalystFactory = Callable[..., RepositoryAnalyst]
RootCauseAnalyzerFactory = Callable[..., RootCauseAnalyzer]
PatchGeneratorFactory = Callable[..., PatchGenerator]
PatchApplierFactory = Callable[..., PatchApplier]
PatchValidatorFactory = Callable[..., PatchValidator]


class RepairOrchestrator:
    """Run a single repair workflow in a dedicated local Git workspace.

    Validation profiles may execute repository-controlled code. The supplied
    workspace must therefore be disposable and appropriately isolated.
    """

    def __init__(
        self,
        settings: Settings | None = None,
        github_service: GitHubService | None = None,
        repository_analyst_factory: RepositoryAnalystFactory | None = None,
        root_cause_analyzer_factory: RootCauseAnalyzerFactory | None = None,
        patch_generator_factory: PatchGeneratorFactory | None = None,
        patch_applier_factory: PatchApplierFactory | None = None,
        patch_validator_factory: PatchValidatorFactory | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.github_service = github_service or GitHubService(settings=self.settings)
        self._repository_analyst_factory = (
            repository_analyst_factory or RepositoryAnalyst
        )
        self._root_cause_analyzer_factory = (
            root_cause_analyzer_factory or RootCauseAnalyzer
        )
        self._patch_generator_factory = patch_generator_factory or PatchGenerator
        self._patch_applier_factory = patch_applier_factory or PatchApplier
        self._patch_validator_factory = patch_validator_factory or PatchValidator

    @staticmethod
    def _stage_result(
        stage: str,
        started_at: float,
        *,
        status: Literal["succeeded", "failed"],
        message: str,
        error_type: str | None = None,
    ) -> WorkflowStageResult:
        """Build a stage result with a non-negative elapsed duration."""
        return WorkflowStageResult(
            stage=stage,
            status=status,
            message=message,
            duration_seconds=max(0.0, time.monotonic() - started_at),
            error_type=error_type,
        )

    @staticmethod
    def _failure_message(exc: Exception) -> str:
        """Return a useful error message without exposing a traceback."""
        message = str(exc).strip()
        if not message:
            return "The stage failed without additional error details."
        return message[:1000]

    async def run(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        workspace_path: str | Path,
        profiles: list[str] | None = None,
    ) -> RepairWorkflowResult:
        """Run the repair pipeline and return a structured workflow result.

        The caller supplies an existing, dedicated local Git repository
        workspace corresponding to the requested GitHub repository.
        """
        requested_full_name = f"{owner.strip()}/{repo.strip()}"
        stages: list[WorkflowStageResult] = []

        # The result schema requires a positive issue number even when the
        # request is invalid. Keep that schema invariant without attempting
        # to retrieve or process the placeholder issue.
        result_issue_number = issue_number if issue_number > 0 else 1

        def result(
            status: Literal["succeeded", "failed", "validation_failed"],
            summary: str,
            *,
            repository: RepositoryContext | None = None,
            issue: IssueContext | None = None,
            repository_analysis: RepositoryAnalysis | None = None,
            root_cause: RootCauseAnalysis | None = None,
            patch_proposal: PatchProposal | None = None,
            patch_application: PatchApplicationResult | None = None,
            validation_report: ValidationReport | None = None,
        ) -> RepairWorkflowResult:
            return RepairWorkflowResult(
                repository_full_name=requested_full_name,
                issue_number=result_issue_number,
                status=status,
                stages=stages,
                repository=repository,
                issue=issue,
                repository_analysis=repository_analysis,
                root_cause=root_cause,
                patch_proposal=patch_proposal,
                patch_application=patch_application,
                validation_report=validation_report,
                summary=summary,
            )

        if not owner.strip() or not repo.strip():
            started = time.monotonic()
            stages.append(
                self._stage_result(
                    "input_validation",
                    started,
                    status="failed",
                    message="Repository owner and name are required.",
                    error_type="ValueError",
                )
            )
            return result("failed", "Invalid repository input.")

        if issue_number < 1:
            started = time.monotonic()
            stages.append(
                self._stage_result(
                    "input_validation",
                    started,
                    status="failed",
                    message=(
                        f"Issue number must be positive; received {issue_number}."
                    ),
                    error_type="ValueError",
                )
            )
            return result("failed", "Invalid issue number.")

        workspace = Path(workspace_path).resolve()
        if not workspace.is_dir():
            started = time.monotonic()
            stages.append(
                self._stage_result(
                    "workspace_validation",
                    started,
                    status="failed",
                    message="The supplied workspace directory does not exist.",
                    error_type="ValueError",
                )
            )
            return result("failed", "The repair workspace is unavailable.")

        repository: RepositoryContext | None = None
        issue: IssueContext | None = None
        repository_analysis: RepositoryAnalysis | None = None
        root_cause: RootCauseAnalysis | None = None
        patch_proposal: PatchProposal | None = None
        patch_application: PatchApplicationResult | None = None
        validation_report: ValidationReport | None = None

        # Stage 1: retrieve the repository and issue from GitHub.
        started = time.monotonic()
        try:
            repository = await self.github_service.get_repository(
                owner.strip(), repo.strip()
            )
            issue = await self.github_service.get_issue(
                owner.strip(), repo.strip(), issue_number
            )

            if repository.full_name.casefold() != requested_full_name.casefold():
                raise ValueError(
                    "GitHub returned repository metadata that does not match "
                    "the requested repository."
                )

            if issue.repository_full_name.casefold() != requested_full_name.casefold():
                raise ValueError(
                    "The returned issue belongs to a different repository."
                )

            if issue.number != issue_number:
                raise ValueError("GitHub returned a different issue number.")

            if issue.is_pull_request:
                raise ValueError(
                    "The supplied issue number identifies a pull request, "
                    "not a GitHub issue."
                )

            stages.append(
                self._stage_result(
                    "github_context",
                    started,
                    status="succeeded",
                    message="Repository and issue context retrieved successfully.",
                )
            )
        except Exception as exc:
            logger.warning(
                "Repair workflow failed during GitHub context retrieval: %s",
                type(exc).__name__,
            )
            stages.append(
                self._stage_result(
                    "github_context",
                    started,
                    status="failed",
                    message=self._failure_message(exc),
                    error_type=type(exc).__name__,
                )
            )
            return result(
                "failed",
                "Could not retrieve valid GitHub repository and issue context.",
                repository=repository,
                issue=issue,
            )

        # Stage 2: inspect and rank candidate repository files.
        started = time.monotonic()
        try:
            analyst = self._repository_analyst_factory(
                settings=self.settings,
                workspace_root=workspace,
            )
            repository_analysis = analyst.analyze(issue)

            if (
                repository_analysis.repository_full_name.casefold()
                != repository.full_name.casefold()
                or repository_analysis.issue_number != issue.number
            ):
                raise ValueError(
                    "Repository analysis identifiers do not match the issue."
                )

            if not repository_analysis.candidates:
                raise ValueError(
                    "Repository analysis did not find any relevant Python files."
                )

            stages.append(
                self._stage_result(
                    "repository_analysis",
                    started,
                    status="succeeded",
                    message=(
                        f"Scanned {repository_analysis.files_scanned} file(s) "
                        f"and selected {len(repository_analysis.candidates)} "
                        "candidate file(s)."
                    ),
                )
            )
        except Exception as exc:
            logger.warning(
                "Repair workflow failed during repository analysis: %s",
                type(exc).__name__,
            )
            stages.append(
                self._stage_result(
                    "repository_analysis",
                    started,
                    status="failed",
                    message=self._failure_message(exc),
                    error_type=type(exc).__name__,
                )
            )
            return result(
                "failed",
                "Repository analysis failed.",
                repository=repository,
                issue=issue,
            )

        # Stage 3: diagnose the issue using the ranked source files.
        started = time.monotonic()
        try:
            analyzer = self._root_cause_analyzer_factory(
                settings=self.settings,
                workspace_root=str(workspace),
            )
            root_cause = analyzer.analyze(issue, repository_analysis)

            if (
                root_cause.repository_full_name.casefold()
                != repository.full_name.casefold()
                or root_cause.issue_number != issue.number
            ):
                raise ValueError(
                    "Root-cause analysis identifiers do not match the issue."
                )

            stages.append(
                self._stage_result(
                    "root_cause_analysis",
                    started,
                    status="succeeded",
                    message="Root-cause diagnosis produced successfully.",
                )
            )
        except Exception as exc:
            logger.warning(
                "Repair workflow failed during root-cause analysis: %s",
                type(exc).__name__,
            )
            stages.append(
                self._stage_result(
                    "root_cause_analysis",
                    started,
                    status="failed",
                    message=self._failure_message(exc),
                    error_type=type(exc).__name__,
                )
            )
            return result(
                "failed",
                "Root-cause analysis failed.",
                repository=repository,
                issue=issue,
                repository_analysis=repository_analysis,
            )

        # Stage 4: generate a reviewable patch proposal.
        started = time.monotonic()
        try:
            generator = self._patch_generator_factory(
                settings=self.settings,
                workspace_root=str(workspace),
            )
            patch_proposal = generator.generate(
                issue,
                repository_analysis,
                root_cause,
            )

            if (
                patch_proposal.repository_full_name.casefold()
                != repository.full_name.casefold()
                or patch_proposal.issue_number != issue.number
            ):
                raise ValueError("Patch proposal identifiers do not match the issue.")

            stages.append(
                self._stage_result(
                    "patch_generation",
                    started,
                    status="succeeded",
                    message=(
                        "Patch proposal generated for "
                        f"{len(patch_proposal.files_changed)} file(s)."
                    ),
                )
            )
        except Exception as exc:
            logger.warning(
                "Repair workflow failed during patch generation: %s",
                type(exc).__name__,
            )
            stages.append(
                self._stage_result(
                    "patch_generation",
                    started,
                    status="failed",
                    message=self._failure_message(exc),
                    error_type=type(exc).__name__,
                )
            )
            return result(
                "failed",
                "Patch generation failed.",
                repository=repository,
                issue=issue,
                repository_analysis=repository_analysis,
                root_cause=root_cause,
            )

        # Stage 5: apply the proposal using the existing safe Git applier.
        started = time.monotonic()
        try:
            applier = self._patch_applier_factory(repository_path=workspace)
            patch_application = applier.apply(patch_proposal)

            if not patch_application.applied:
                raise RuntimeError(
                    "The patch applier did not confirm successful application."
                )

            stages.append(
                self._stage_result(
                    "patch_application",
                    started,
                    status="succeeded",
                    message=patch_application.message,
                )
            )
        except Exception as exc:
            logger.warning(
                "Repair workflow failed during patch application: %s",
                type(exc).__name__,
            )
            stages.append(
                self._stage_result(
                    "patch_application",
                    started,
                    status="failed",
                    message=self._failure_message(exc),
                    error_type=type(exc).__name__,
                )
            )
            return result(
                "failed",
                "The patch could not be applied.",
                repository=repository,
                issue=issue,
                repository_analysis=repository_analysis,
                root_cause=root_cause,
                patch_proposal=patch_proposal,
            )

        # Stage 6: execute only the validator's predefined profiles.
        started = time.monotonic()
        try:
            validator = self._patch_validator_factory(
                timeout_seconds=self.settings.sandbox_timeout
            )
            validation_report = validator.validate(
                patch_proposal,
                workspace,
                profiles=profiles,
            )

            if (
                validation_report.repository_full_name.casefold()
                != repository.full_name.casefold()
                or validation_report.issue_number != issue.number
            ):
                raise ValueError(
                    "Validation report identifiers do not match the issue."
                )

            validation_status: Literal["succeeded", "failed"] = (
                "succeeded" if validation_report.passed else "failed"
            )
            stages.append(
                self._stage_result(
                    "patch_validation",
                    started,
                    status=validation_status,
                    message=validation_report.summary,
                )
            )
        except Exception as exc:
            logger.warning(
                "Repair workflow failed during patch validation: %s",
                type(exc).__name__,
            )
            stages.append(
                self._stage_result(
                    "patch_validation",
                    started,
                    status="failed",
                    message=self._failure_message(exc),
                    error_type=type(exc).__name__,
                )
            )
            return result(
                "failed",
                "The patch was applied, but validation could not be completed.",
                repository=repository,
                issue=issue,
                repository_analysis=repository_analysis,
                root_cause=root_cause,
                patch_proposal=patch_proposal,
                patch_application=patch_application,
            )

        if not validation_report.passed:
            return result(
                "validation_failed",
                "The patch was applied, but one or more validation profiles failed.",
                repository=repository,
                issue=issue,
                repository_analysis=repository_analysis,
                root_cause=root_cause,
                patch_proposal=patch_proposal,
                patch_application=patch_application,
                validation_report=validation_report,
            )

        return result(
            "succeeded",
            "The patch was applied and all selected validation profiles passed.",
            repository=repository,
            issue=issue,
            repository_analysis=repository_analysis,
            root_cause=root_cause,
            patch_proposal=patch_proposal,
            patch_application=patch_application,
            validation_report=validation_report,
        )
