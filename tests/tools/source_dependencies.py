#!/usr/bin/env python3
"""Enforce the bounded EMRYS Python source-dependency rules."""

from __future__ import annotations

import argparse
import ast
import subprocess
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path


class DependencyError(RuntimeError):
    """Raised when the dependency gate cannot establish its input safely."""


@dataclass(frozen=True, order=True)
class ImportEdge:
    """One statically declared EMRYS import."""

    source_path: str
    line: int
    source_module: str
    target_module: str


@dataclass(frozen=True)
class Transition:
    """One exact, bounded exception to a durable dependency rule."""

    transition_id: str
    source_path: str
    target_module: str
    rule_id: str
    successors: tuple[str, ...]


@dataclass(frozen=True)
class CompositionSeam:
    """One exact current module exposed to the grouped CLI composition root."""

    seam_id: str
    target_module: str


@dataclass(frozen=True)
class Problem:
    """One actionable dependency-gate failure."""

    source_path: str
    line: int
    rule_id: str
    detail: str

    def render(self) -> str:
        return f"{self.source_path}:{self.line}: [{self.rule_id}] {self.detail}"


@dataclass(frozen=True)
class ValidationResult:
    """One complete read-only dependency inspection."""

    source_count: int
    edge_count: int
    composition_seam_count: int
    transition_count: int
    problems: tuple[Problem, ...]


RULE_CONTRACT_NEUTRAL = "AC-DEP-001"
RULE_LIBRARY_NEUTRAL = "AC-DEP-002"
RULE_FUNCTIONAL_OWNER = "AC-DEP-003"
RULE_INGESTION_BOUNDARY = "AC-DEP-004"
RULE_REPORTING_DOWNSTREAM = "AC-DEP-005"
RULE_ORCHESTRATION_BOUNDARY = "AC-DEP-006"
RULE_COMPOSITION_DIRECTION = RULE_ORCHESTRATION_BOUNDARY
RULE_PRIVATE_OWNER = "AC-DEP-007"
RULE_LIBRARY_ACYCLIC = RULE_LIBRARY_NEUTRAL
RULE_SOURCE_CLASSIFICATION = "AC-DEP-009"

KNOWN_RULE_IDS = frozenset(
    {
        RULE_CONTRACT_NEUTRAL,
        RULE_LIBRARY_NEUTRAL,
        RULE_FUNCTIONAL_OWNER,
        RULE_INGESTION_BOUNDARY,
        RULE_REPORTING_DOWNSTREAM,
        RULE_ORCHESTRATION_BOUNDARY,
        RULE_PRIVATE_OWNER,
        RULE_SOURCE_CLASSIFICATION,
    }
)

PUBLIC_REPORTING_SEAM = "emrys.reporting.transaction_validation"

COMPOSITION_SEAMS: tuple[CompositionSeam, ...] = (
    CompositionSeam(
        "CLI-SEAM-001",
        "emrys.analyses.paired_cmh_candidate_ranking.validator",
    ),
    CompositionSeam(
        "CLI-SEAM-002",
        "emrys.analyses.scientific_context_projection.validator",
    ),
    CompositionSeam("CLI-SEAM-003", "emrys.contracts.artifacts.validator"),
    CompositionSeam("CLI-SEAM-004", "emrys.evidence.canonical_bam_qc.validator"),
    CompositionSeam(
        "CLI-SEAM-005",
        "emrys.evidence.reference_provenance.reconciler",
    ),
    CompositionSeam("CLI-SEAM-006", "emrys.evidence.rseqc_orientation.validator"),
    CompositionSeam(
        "CLI-SEAM-007",
        "emrys.evidence.runtime_availability.inspector",
    ),
    CompositionSeam(
        "CLI-SEAM-008",
        "emrys.evidence.storage_inventory.inspector",
    ),
    CompositionSeam(
        "CLI-SEAM-009",
        "emrys.evidence.storage_inventory.qualification",
    ),
    CompositionSeam(
        "CLI-SEAM-010",
        "emrys.ingestion.sample_manifest_admission.validator",
    ),
    CompositionSeam("CLI-SEAM-011", "emrys.libraries.source_authority"),
    CompositionSeam("CLI-SEAM-012", "emrys.orchestration.local_pilot.all_pass"),
    CompositionSeam("CLI-SEAM-013", "emrys.orchestration.local_pilot.doctor"),
    CompositionSeam("CLI-SEAM-014", "emrys.orchestration.local_pilot.control"),
    CompositionSeam("CLI-SEAM-015", "emrys.orchestration.local_pilot.onboarding"),
    CompositionSeam(
        "CLI-SEAM-016",
        "emrys.orchestration.local_pilot.synthetic_fixture",
    ),
    CompositionSeam("CLI-SEAM-017", "emrys.reporting.report"),
    CompositionSeam("CLI-SEAM-018", "emrys.stages.canonical_bam.validator"),
    CompositionSeam(
        "CLI-SEAM-019",
        "emrys.stages.cohort_candidate_preprocessing.validator",
    ),
    CompositionSeam("CLI-SEAM-020", "emrys.stages.duplicate_marking.validator"),
    CompositionSeam("CLI-SEAM-021", "emrys.stages.fasta_sidecars.validator"),
    CompositionSeam("CLI-SEAM-022", "emrys.stages.gtf_to_bed12.converter"),
    CompositionSeam("CLI-SEAM-023", "emrys.stages.gtf_to_bed12.validator"),
    CompositionSeam(
        "CLI-SEAM-024",
        "emrys.stages.mechanical_orientation.validator",
    ),
    CompositionSeam(
        "CLI-SEAM-025",
        "emrys.stages.partitioned_cohort_mpileup.validator",
    ),
    CompositionSeam("CLI-SEAM-026", "emrys.stages.split_n_cigar.validator"),
    CompositionSeam("CLI-SEAM-027", "emrys.stages.star_alignment.validator"),
    CompositionSeam("CLI-SEAM-028", "emrys.stages.star_index.validator"),
)

TRANSITIONS: tuple[Transition, ...] = (
    Transition(
        "SRC-TRANS-001",
        "src/emrys/contracts/artifacts/_artifact_contracts/schema.py",
        "emrys.libraries.validation",
        RULE_CONTRACT_NEUTRAL,
        ("AC-SLICE-07",),
    ),
    Transition(
        "SRC-TRANS-002",
        "src/emrys/contracts/orchestration/api.py",
        "emrys.libraries.source_authority",
        RULE_CONTRACT_NEUTRAL,
        ("AC-SLICE-05",),
    ),
    Transition(
        "SRC-TRANS-003",
        "src/emrys/contracts/scientific_evidence/step08.py",
        "emrys.libraries.validation",
        RULE_CONTRACT_NEUTRAL,
        ("AC-SLICE-04", "AC-SLICE-07"),
    ),
    Transition(
        "SRC-TRANS-004",
        "src/emrys/contracts/scientific_evidence/step08.py",
        "emrys.libraries.validation.tsv",
        RULE_CONTRACT_NEUTRAL,
        ("AC-SLICE-04",),
    ),
    Transition(
        "SRC-TRANS-005",
        "src/emrys/contracts/scientific_evidence/step08.py",
        "emrys.libraries.alignments.orientation",
        RULE_CONTRACT_NEUTRAL,
        ("AC-SLICE-04",),
    ),
    Transition(
        "SRC-TRANS-006",
        "src/emrys/contracts/scientific_evidence/step09.py",
        "emrys.libraries.alignments.orientation",
        RULE_CONTRACT_NEUTRAL,
        ("AC-SLICE-04",),
    ),
    Transition(
        "SRC-TRANS-007",
        "src/emrys/orchestration/local_pilot/doctor.py",
        "emrys.evidence.runtime_availability.inspector",
        RULE_ORCHESTRATION_BOUNDARY,
        ("AC-SLICE-03", "AC-SLICE-05", "AC-SLICE-08"),
    ),
    Transition(
        "SRC-TRANS-008",
        "src/emrys/orchestration/local_pilot/doctor.py",
        "emrys.evidence.storage_inventory.qualification",
        RULE_ORCHESTRATION_BOUNDARY,
        ("AC-SLICE-03", "AC-SLICE-05", "AC-SLICE-06"),
    ),
    Transition(
        "SRC-TRANS-009",
        "src/emrys/orchestration/local_pilot/lifecycle.py",
        "emrys.evidence.runtime_availability.inspector",
        RULE_ORCHESTRATION_BOUNDARY,
        ("AC-SLICE-03", "AC-SLICE-05", "AC-SLICE-08"),
    ),
    Transition(
        "SRC-TRANS-010",
        "src/emrys/orchestration/local_pilot/lifecycle.py",
        "emrys.evidence.storage_inventory.qualification",
        RULE_ORCHESTRATION_BOUNDARY,
        ("AC-SLICE-05", "AC-SLICE-06"),
    ),
    Transition(
        "SRC-TRANS-011",
        "src/emrys/orchestration/local_pilot/onboarding.py",
        "emrys.stages.gtf_to_bed12.converter",
        RULE_ORCHESTRATION_BOUNDARY,
        ("AC-SLICE-03", "AC-SLICE-04"),
    ),
    Transition(
        "SRC-TRANS-012",
        "src/emrys/__main__.py",
        "emrys.reporting._artifact_index.builder",
        RULE_PRIVATE_OWNER,
        ("AC-SLICE-03", "AC-SLICE-12"),
    ),
    Transition(
        "SRC-TRANS-013",
        "src/emrys/__main__.py",
        "emrys.reporting._run_summary.builder",
        RULE_PRIVATE_OWNER,
        ("AC-SLICE-03", "AC-SLICE-12"),
    ),
)


def repository_root(value: Path) -> Path:
    """Resolve and admit one exact Git worktree root."""
    try:
        root = value.resolve(strict=True)
    except OSError as exc:
        raise DependencyError(f"repository path is unavailable: {value}: {exc}") from exc
    result = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "no diagnostic"
        raise DependencyError(f"not a Git worktree: {root}: {detail}")
    if Path(result.stdout.strip()).resolve() != root:
        raise DependencyError(f"repository path is not the worktree root: {root}")
    return root


def git_python_sources(root: Path) -> tuple[Path, ...]:
    """Inventory present tracked or untracked, non-ignored EMRYS Python files."""
    result = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "--",
            "src/emrys",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "no diagnostic"
        raise DependencyError(f"could not inventory src/emrys: {detail}")
    paths: list[Path] = []
    for relative in result.stdout.splitlines():
        path = root / relative
        if path.suffix != ".py":
            continue
        if not path.exists() and not path.is_symlink():
            continue
        if path.is_symlink() or not path.is_file():
            raise DependencyError(f"Python source must be a regular file: {relative}")
        paths.append(path)
    return tuple(sorted(paths))


def module_name(root: Path, path: Path) -> tuple[str, bool]:
    """Return the import name and package status for one source path."""
    relative = path.relative_to(root / "src").with_suffix("")
    parts = list(relative.parts)
    is_package = parts[-1] == "__init__"
    if is_package:
        parts.pop()
    return ".".join(parts), is_package


def resolve_from_base(
    source_module: str,
    source_is_package: bool,
    node: ast.ImportFrom,
) -> str:
    """Resolve the base name of one absolute or relative from-import."""
    if node.level == 0:
        return node.module or ""
    package = source_module if source_is_package else source_module.rpartition(".")[0]
    parts = package.split(".") if package else []
    parent_count = node.level - 1
    if parent_count > len(parts):
        return ""
    if parent_count:
        parts = parts[:-parent_count]
    if node.module:
        parts.extend(node.module.split("."))
    return ".".join(parts)


def imported_modules(
    source_module: str,
    source_is_package: bool,
    node: ast.Import | ast.ImportFrom,
    known_modules: frozenset[str],
) -> tuple[str, ...]:
    """Return exact imported module names without importing application code."""
    if isinstance(node, ast.Import):
        return tuple(alias.name for alias in node.names)
    base = resolve_from_base(source_module, source_is_package, node)
    if not base:
        return ()
    modules: list[str] = []
    for alias in node.names:
        candidate = f"{base}.{alias.name}" if alias.name != "*" else base
        modules.append(candidate if candidate in known_modules else base)
    return tuple(modules)


def dynamic_import_aliases(
    tree: ast.AST,
) -> tuple[frozenset[str], frozenset[str], frozenset[str]]:
    """Return names bound to standard-library dynamic import entry points."""
    module_aliases: set[str] = set()
    builtin_aliases: set[str] = set()
    function_aliases: set[str] = {"__import__"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "importlib":
                    module_aliases.add(alias.asname or alias.name)
                elif alias.name.startswith("importlib.") and alias.asname is None:
                    module_aliases.add("importlib")
                elif alias.name == "builtins":
                    builtin_aliases.add(alias.asname or alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module == "importlib":
            for alias in node.names:
                if alias.name == "import_module":
                    function_aliases.add(alias.asname or alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module == "builtins":
            for alias in node.names:
                if alias.name == "__import__":
                    function_aliases.add(alias.asname or alias.name)
    return (
        frozenset(module_aliases),
        frozenset(builtin_aliases),
        frozenset(function_aliases),
    )


def resolve_literal_dynamic_name(node: ast.Call) -> str | None:
    """Resolve one literal absolute or package-relative import-module name."""
    if not node.args:
        return None
    value = node.args[0]
    if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
        return None
    target = value.value
    if not target.startswith("."):
        return target
    package_value: ast.expr | None = node.args[1] if len(node.args) >= 2 else None
    for keyword in node.keywords:
        if keyword.arg == "package":
            package_value = keyword.value
    if (
        not isinstance(package_value, ast.Constant)
        or not isinstance(package_value.value, str)
    ):
        return None
    package_parts = package_value.value.split(".")
    level = len(target) - len(target.lstrip("."))
    if level > len(package_parts):
        return None
    suffix = target[level:]
    resolved = package_parts[: len(package_parts) - level + 1]
    if suffix:
        resolved.extend(suffix.split("."))
    return ".".join(resolved)


def literal_dynamic_import(
    node: ast.Call,
    module_aliases: frozenset[str],
    builtin_aliases: frozenset[str],
    function_aliases: frozenset[str],
) -> str | None:
    """Return one literal absolute module loaded through a known import entry."""
    function = node.func
    recognized = isinstance(function, ast.Name) and function.id in function_aliases
    if (
        isinstance(function, ast.Attribute)
        and function.attr == "import_module"
        and isinstance(function.value, ast.Name)
        and function.value.id in module_aliases
    ):
        recognized = True
    if (
        isinstance(function, ast.Attribute)
        and function.attr == "__import__"
        and isinstance(function.value, ast.Name)
        and function.value.id in builtin_aliases
    ):
        recognized = True
    if not recognized:
        return None
    return resolve_literal_dynamic_name(node)


def collect_edges(root: Path, paths: Sequence[Path]) -> tuple[ImportEdge, ...]:
    """Parse declared and literal dynamic EMRYS import edges."""
    identities = {path: module_name(root, path) for path in paths}
    known_modules = frozenset(module for module, _ in identities.values())
    edges: set[ImportEdge] = set()
    for path in paths:
        source_module, source_is_package = identities[path]
        relative = path.relative_to(root).as_posix()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative)
        except (OSError, UnicodeError, SyntaxError) as exc:
            line = getattr(exc, "lineno", 0) or 0
            raise DependencyError(f"could not parse {relative}:{line}: {exc}") from exc
        dynamic_modules, dynamic_builtins, dynamic_functions = dynamic_import_aliases(
            tree
        )
        for node in ast.walk(tree):
            targets: tuple[str, ...]
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                targets = imported_modules(
                    source_module,
                    source_is_package,
                    node,
                    known_modules,
                )
            elif isinstance(node, ast.Call):
                target = literal_dynamic_import(
                    node,
                    dynamic_modules,
                    dynamic_builtins,
                    dynamic_functions,
                )
                targets = (target,) if target is not None else ()
            else:
                targets = ()
            for target in targets:
                if target == "emrys" or target.startswith("emrys."):
                    edges.add(
                        ImportEdge(relative, node.lineno, source_module, target)
                    )
    return tuple(sorted(edges))


def owner(module: str) -> tuple[str, str]:
    """Classify one live source module by its current responsibility owner."""
    if module == "emrys":
        return "root", "emrys"
    if module == "emrys.__main__" or module.startswith("emrys.__main__."):
        return "composition", "emrys.__main__"
    parts = module.split(".")
    if len(parts) < 2:
        return "root", "emrys"
    domain = parts[1]
    if domain in {"stages", "analyses", "evidence"}:
        identity = ".".join(parts[:3]) if len(parts) >= 3 else ".".join(parts[:2])
        return "functional", identity
    if domain == "libraries":
        identity = ".".join(parts[:3]) if len(parts) >= 3 else "emrys.libraries"
        return "libraries", identity
    if domain in {
        "contracts",
        "ingestion",
        "orchestration",
        "reporting",
    }:
        return domain, f"emrys.{domain}"
    return "unclassified", f"emrys.{domain}"


def forbidden_rule(
    edge: ImportEdge,
    composition_targets: frozenset[str],
) -> tuple[str, str] | None:
    """Return the durable negative rule violated by one edge, if any."""
    source_kind, source_owner = owner(edge.source_module)
    target_kind, target_owner = owner(edge.target_module)
    if target_kind == "unclassified":
        return (
            RULE_SOURCE_CLASSIFICATION,
            "new EMRYS source domains require an explicit responsibility classification",
        )
    if source_kind == "root" and target_kind != "root":
        return (
            RULE_SOURCE_CLASSIFICATION,
            "package metadata may not become an undeclared composition root",
        )
    if target_kind == "composition" and source_kind != "composition":
        return (
            RULE_COMPOSITION_DIRECTION,
            "lower source code may not depend on the CLI composition root",
        )
    if (
        source_owner != target_owner
        and any(
            part.startswith("_") and not part.startswith("__")
            for part in edge.target_module.split(".")[2:]
        )
    ):
        return (
            RULE_PRIVATE_OWNER,
            "private modules are local to their declared current owner",
        )
    if source_kind == "composition":
        if edge.target_module not in composition_targets:
            return (
                RULE_ORCHESTRATION_BOUNDARY,
                "CLI composition may import only its exact declared current seams",
            )
        return None
    if source_kind == "contracts" and target_kind not in {"contracts", "root"}:
        return (
            RULE_CONTRACT_NEUTRAL,
            "neutral contracts may not depend on EMRYS implementation owners",
        )
    if source_kind == "libraries" and target_kind not in {
        "contracts",
        "libraries",
        "root",
    }:
        return (
            RULE_LIBRARY_NEUTRAL,
            "neutral libraries may not depend on functional or application owners",
        )
    if source_kind == "functional":
        if target_kind == "functional" and source_owner != target_owner:
            return (
                RULE_FUNCTIONAL_OWNER,
                "functional owners may not import peer-owner implementation",
            )
        if target_kind in {"ingestion", "orchestration", "reporting", "composition"}:
            return (
                RULE_FUNCTIONAL_OWNER,
                "functional owners may not depend on input, application, or reporting owners",
            )
    if source_kind == "ingestion" and target_kind in {
        "functional",
        "orchestration",
        "reporting",
        "composition",
    }:
        return (
            RULE_INGESTION_BOUNDARY,
            "input admission may not depend on computation, application, or reporting owners",
        )
    if source_kind == "reporting" and target_kind in {
        "functional",
        "ingestion",
        "orchestration",
        "composition",
    }:
        return (
            RULE_REPORTING_DOWNSTREAM,
            "reporting must remain downstream of computation, input, and application owners",
        )
    if source_kind == "orchestration" and target_kind in {
        "functional",
        "ingestion",
        "reporting",
    }:
        if edge.target_module == PUBLIC_REPORTING_SEAM:
            return None
        return (
            RULE_ORCHESTRATION_BOUNDARY,
            "orchestration may use only declared public owner seams, not implementation modules",
        )
    return None


def transition_index(
    transitions: Sequence[Transition],
) -> dict[tuple[str, str], Transition]:
    """Validate and index the exact transition roster."""
    indexed: dict[tuple[str, str], Transition] = {}
    ids: set[str] = set()
    for transition in transitions:
        key = (transition.source_path, transition.target_module)
        if transition.rule_id not in KNOWN_RULE_IDS:
            raise DependencyError(
                f"unknown transition rule for {transition.transition_id}: "
                f"{transition.rule_id}"
            )
        if not transition.successors:
            raise DependencyError(
                f"transition has no successor: {transition.transition_id}"
            )
        if transition.transition_id in ids:
            raise DependencyError(
                f"duplicate transition identity: {transition.transition_id}"
            )
        if key in indexed:
            raise DependencyError(
                "duplicate transitional dependency edge: " + " -> ".join(key)
            )
        ids.add(transition.transition_id)
        indexed[key] = transition
    return indexed


def composition_seam_index(
    seams: Sequence[CompositionSeam],
) -> dict[str, CompositionSeam]:
    """Validate and index the exact current CLI composition roster."""
    indexed: dict[str, CompositionSeam] = {}
    ids: set[str] = set()
    for seam in seams:
        if seam.seam_id in ids:
            raise DependencyError(f"duplicate composition seam identity: {seam.seam_id}")
        if seam.target_module in indexed:
            raise DependencyError(
                f"duplicate composition seam target: {seam.target_module}"
            )
        ids.add(seam.seam_id)
        indexed[seam.target_module] = seam
    return indexed


def library_cycle(edges: Iterable[ImportEdge]) -> Problem | None:
    """Return the first deterministic neutral-library cycle, if one exists."""
    graph: dict[str, dict[str, ImportEdge]] = {}
    for edge in edges:
        source_kind, source_owner = owner(edge.source_module)
        target_kind, target_owner = owner(edge.target_module)
        if (
            source_kind == "libraries"
            and target_kind == "libraries"
            and source_owner != target_owner
        ):
            targets = graph.setdefault(source_owner, {})
            current = targets.get(target_owner)
            if current is None or edge < current:
                targets[target_owner] = edge

    state: dict[str, int] = {}
    stack: list[str] = []

    def visit(module: str) -> Problem | None:
        state[module] = 1
        stack.append(module)
        for target in sorted(graph.get(module, {})):
            if state.get(target, 0) == 0:
                problem = visit(target)
                if problem is not None:
                    return problem
            elif state.get(target) == 1:
                start = stack.index(target)
                cycle = stack[start:] + [target]
                edge = graph[module][target]
                return Problem(
                    edge.source_path,
                    edge.line,
                    RULE_LIBRARY_ACYCLIC,
                    "neutral library dependency cycle: " + " -> ".join(cycle),
                )
        stack.pop()
        state[module] = 2
        return None

    for module in sorted(graph):
        if state.get(module, 0) == 0:
            problem = visit(module)
            if problem is not None:
                return problem
    return None


def inspect_repository(
    value: Path,
    *,
    transitions: Sequence[Transition] = TRANSITIONS,
    composition_seams: Sequence[CompositionSeam] = COMPOSITION_SEAMS,
) -> ValidationResult:
    """Inspect one repository without importing or executing its source."""
    root = repository_root(value)
    paths = git_python_sources(root)
    edges = collect_edges(root, paths)
    indexed = transition_index(transitions)
    composition_index = composition_seam_index(composition_seams)
    composition_targets = frozenset(composition_index)
    observed_composition: set[str] = set()
    observed: set[tuple[str, str]] = set()
    problems: list[Problem] = []

    for path in paths:
        source_module, _ = module_name(root, path)
        source_kind, _ = owner(source_module)
        if source_kind == "unclassified":
            problems.append(
                Problem(
                    path.relative_to(root).as_posix(),
                    0,
                    RULE_SOURCE_CLASSIFICATION,
                    "new EMRYS source domains require an explicit responsibility "
                    f"classification: {source_module}",
                )
            )

    for edge in edges:
        if (
            edge.source_module == "emrys.__main__"
            and edge.target_module in composition_targets
        ):
            observed_composition.add(edge.target_module)
        violation = forbidden_rule(edge, composition_targets)
        transition = indexed.get((edge.source_path, edge.target_module))
        if transition is not None and violation is not None:
            rule_id, _ = violation
            if transition.rule_id == rule_id:
                observed.add((transition.source_path, transition.target_module))
                continue
        if violation is not None:
            rule_id, detail = violation
            problems.append(
                Problem(
                    edge.source_path,
                    edge.line,
                    rule_id,
                    f"{detail}: {edge.source_module} -> {edge.target_module}",
                )
            )

    for key, transition in indexed.items():
        if key not in observed:
            problems.append(
                Problem(
                    transition.source_path,
                    0,
                    transition.rule_id,
                    f"stale transition {transition.transition_id} to "
                    f"{transition.target_module}; remove or reconcile it under "
                    f"{', '.join(transition.successors)}",
                )
            )

    for target, seam in composition_index.items():
        if target not in observed_composition:
            problems.append(
                Problem(
                    "src/emrys/__main__.py",
                    0,
                    RULE_ORCHESTRATION_BOUNDARY,
                    f"stale current composition seam {seam.seam_id} to {target}; "
                    "remove it from the executable and documented rosters",
                )
            )

    cycle = library_cycle(edges)
    if cycle is not None:
        problems.append(cycle)
    return ValidationResult(
        len(paths),
        len(edges),
        len(observed_composition),
        len(observed),
        tuple(
            sorted(
                problems,
                key=lambda item: (
                    item.source_path,
                    item.line,
                    item.rule_id,
                    item.detail,
                ),
            )
        ),
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate bounded EMRYS Python source-dependency rules."
    )
    parser.add_argument("--repo", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    try:
        result = inspect_repository(args.repo)
    except DependencyError as exc:
        raise SystemExit(f"ERROR: {exc}") from exc
    if result.problems:
        detail = "\n".join(problem.render() for problem in result.problems)
        raise SystemExit(f"ERROR: Source dependency gate failures:\n{detail}")
    print(
        "PASS source dependencies "
        f"({result.source_count} Python sources, {result.edge_count} EMRYS imports, "
        f"{result.composition_seam_count} current composition seams, "
        f"{result.transition_count} transitional edges)"
    )


if __name__ == "__main__":
    main()
