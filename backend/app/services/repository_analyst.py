"""Issue-driven repository analysis and file ranking."""

import ast
import os
import re
from pathlib import Path

from backend.app.core.config import Settings, get_settings
from backend.app.schemas import (
    AnalyzedFile,
    IssueContext,
    RepositoryAnalysis,
)
from backend.app.services.repository_inspector import (
    RepositoryInspectionError,
    RepositoryInspector,
)

_EXCLUDED_DIRECTORIES = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "dist",
    "build",
    "site-packages",
    "sandbox",
}

_STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "can",
    "could",
    "during",
    "for",
    "from",
    "fix",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "please",
    "should",
    "the",
    "this",
    "to",
    "when",
    "with",
}


def _tokens(text: str) -> set[str]:
    """Extract normalized words from text and identifiers."""

    expanded = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9]*", expanded.lower())
    return {word for word in words if len(word) > 1 and word not in _STOP_WORDS}


class RepositoryAnalyst:
    """Rank repository files using issue text and Python AST evidence."""

    def __init__(
        self,
        settings: Settings | None = None,
        workspace_root: str | Path | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        configured_root = (
            workspace_root
            if workspace_root is not None
            else self.settings.repository_workspace_root
        )
        self.workspace_root = Path(configured_root).resolve()
        self.inspector = RepositoryInspector(
            settings=self.settings,
            workspace_root=self.workspace_root,
        )

    def _discover_python_files(self) -> list[str]:
        """Discover Python files while excluding generated directories."""

        discovered: list[str] = []

        for current_root, directories, filenames in os.walk(
            self.workspace_root,
            followlinks=False,
            topdown=True,
        ):
            directories[:] = sorted(
                directory
                for directory in directories
                if directory not in _EXCLUDED_DIRECTORIES
                and not directory.startswith(".")
            )

            for filename in sorted(filenames):
                if filename.endswith(".py") and not filename.startswith("."):
                    path = Path(current_root) / filename

                    try:
                        resolved = path.resolve(strict=True)
                        relative = resolved.relative_to(self.workspace_root)
                    except (OSError, RuntimeError, ValueError):
                        continue

                    if resolved.is_file():
                        discovered.append(relative.as_posix())

        return sorted(set(discovered))

    @staticmethod
    def _extract_ast(
        source: str,
    ) -> tuple[list[str], list[str], set[str], bool]:
        """Extract definitions, imports, and identifiers from Python code."""

        try:
            tree = ast.parse(source)
        except SyntaxError:
            return [], [], set(), False

        definitions: list[str] = []
        imports: list[str] = []
        identifiers: set[str] = set()

        for node in ast.walk(tree):
            if isinstance(
                node,
                (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
            ):
                definitions.append(node.name)
                identifiers.update(_tokens(node.name))

            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
                    identifiers.update(_tokens(alias.name))

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
                    identifiers.update(_tokens(node.module))

                for alias in node.names:
                    identifiers.update(_tokens(alias.name))

            elif isinstance(node, ast.Name):
                identifiers.update(_tokens(node.id))

            elif isinstance(node, ast.Attribute):
                identifiers.update(_tokens(node.attr))

        return (
            sorted(set(definitions)),
            sorted(set(imports)),
            identifiers,
            True,
        )

    def analyze(
        self,
        issue: IssueContext,
        *,
        max_candidates: int = 10,
    ) -> RepositoryAnalysis:
        """Rank local Python files for a given GitHub issue."""

        if max_candidates < 1:
            raise ValueError("max_candidates must be at least 1.")

        if not self.workspace_root.is_dir():
            raise ValueError("Repository workspace does not exist.")

        issue_terms = _tokens(
            f"{issue.title} {issue.body or ''} {' '.join(issue.labels)}"
        )

        ranked: list[AnalyzedFile] = []
        files_scanned = 0

        for relative_path in self._discover_python_files():
            try:
                inspected = self.inspector.read_file(relative_path)
            except RepositoryInspectionError:
                continue

            files_scanned += 1

            definitions, imports, code_terms, syntax_valid = self._extract_ast(
                inspected.content
            )

            path_terms = _tokens(relative_path.replace("/", " ").replace(".", " "))

            path_matches = sorted(issue_terms & path_terms)
            code_matches = sorted(issue_terms & code_terms)

            definition_terms = {
                term for definition in definitions for term in _tokens(definition)
            }
            definition_matches = sorted(issue_terms & definition_terms)

            score = (
                len(path_matches) * 5
                + len(definition_matches) * 3
                + len(code_matches) * 2
            )

            reasons: list[str] = []

            if path_matches:
                reasons.append("Path matches issue terms: " + ", ".join(path_matches))

            if definition_matches:
                reasons.append(
                    "Definitions match issue terms: " + ", ".join(definition_matches)
                )

            if code_matches:
                reasons.append(
                    "Code identifiers match issue terms: " + ", ".join(code_matches)
                )

            if not syntax_valid:
                reasons.append("Python syntax could not be parsed.")

            if score > 0:
                ranked.append(
                    AnalyzedFile(
                        path=relative_path,
                        score=score,
                        reasons=reasons,
                        definitions=definitions,
                        imports=imports,
                        syntax_valid=syntax_valid,
                    )
                )

        ranked.sort(key=lambda candidate: (-candidate.score, candidate.path))

        return RepositoryAnalysis(
            repository_full_name=issue.repository_full_name,
            issue_number=issue.number,
            issue_title=issue.title,
            files_scanned=files_scanned,
            candidates=ranked[:max_candidates],
        )
