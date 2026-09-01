#!/usr/bin/env python3
"""Enforce the bounded EMRYS Python source-dependency rules."""

from __future__ import annotations

import argparse
import ast
import subprocess
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from graphlib import CycleError, TopologicalSorter
from pathlib import Path


class DependencyError(RuntimeError):
    """Raised when the dependency gate cannot establish its input safely."""


@dataclass(frozen=True, order=True, slots=True)
class ImportEdge:
    source_path: str
    line: int
    source_module: str
    target_module: str


@dataclass(frozen=True, order=True, slots=True)
class Problem:
    source_path: str
    line: int
    rule_id: str
    detail: str

    def render(self) -> str:
        return f"{self.source_path}:{self.line}: [{self.rule_id}] {self.detail}"


RULE_CONTRACT_NEUTRAL = "AC-DEP-001"
RULE_LIBRARY_NEUTRAL = "AC-DEP-002"
RULE_FUNCTIONAL_OWNER = "AC-DEP-003"
RULE_INGESTION_BOUNDARY = "AC-DEP-004"
RULE_REPORTING_DOWNSTREAM = "AC-DEP-005"
RULE_ORCHESTRATION_BOUNDARY = "AC-DEP-006"
RULE_PRIVATE_OWNER = "AC-DEP-007"
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
_REPORTING_OPERATION = "emrys.orchestration.local_pilot.reporting_operation"
ORCHESTRATION_REPORTING_SEAMS = frozenset(
    {
        (
            "emrys.orchestration.local_pilot.doctor",
            "emrys.reporting",
        ),
        (
            "emrys.orchestration.local_pilot.lifecycle",
            "emrys.reporting.transaction_validation",
        ),
        (
            "emrys.orchestration.local_pilot.reporting_boundary",
            "emrys.reporting.transaction_validation",
        ),
        *(
            (_REPORTING_OPERATION, target)
            for target in (
                "emrys.reporting._artifact_index.context",
                "emrys.reporting._artifact_index.models",
                "emrys.reporting._artifact_index.publication",
                "emrys.reporting._run_summary.builder",
                "emrys.reporting._run_summary.models",
                "emrys.reporting._run_summary.publication",
                "emrys.reporting.report",
                "emrys.reporting._run_report.models",
                "emrys.reporting._run_report.publication",
            )
        ),
    }
)

# (documented ID, exact target); descriptive current behavior, not target APIs.
COMPOSITION_SEAMS: tuple[tuple[str, str], ...] = (
    ("CLI-SEAM-001", "emrys.analyses.paired_cmh_candidate_ranking.validator"),
    (
        "CLI-SEAM-002",
        "emrys.analyses.paired_cmh_candidate_ranking."
        "scientific_context_projection.validator",
    ),
    ("CLI-SEAM-003", "emrys.contracts.artifacts.validator"),
    ("CLI-SEAM-004", "emrys.evidence.canonical_bam_qc.validator"),
    ("CLI-SEAM-005", "emrys.evidence.reference_provenance.reconciler"),
    ("CLI-SEAM-006", "emrys.evidence.rseqc_orientation.validator"),
    ("CLI-SEAM-007", "emrys.evidence.runtime_availability.inspector"),
    ("CLI-SEAM-008", "emrys.evidence.storage_inventory.inspector"),
    ("CLI-SEAM-009", "emrys.evidence.storage_inventory.qualification"),
    ("CLI-SEAM-010", "emrys.ingestion.sample_manifest_admission.validator"),
    ("CLI-SEAM-011", "emrys.libraries.source_authority"),
    ("CLI-SEAM-012", "emrys.orchestration.local_pilot.all_pass"),
    ("CLI-SEAM-013", "emrys.orchestration.local_pilot.doctor"),
    ("CLI-SEAM-014", "emrys.orchestration.local_pilot.control"),
    ("CLI-SEAM-015", "emrys.orchestration.local_pilot.onboarding"),
    ("CLI-SEAM-016", "emrys.orchestration.local_pilot.synthetic_fixture"),
    ("CLI-SEAM-018", "emrys.stages.canonical_bam.validator"),
    ("CLI-SEAM-019", "emrys.stages.cohort_candidate_preprocessing.validator"),
    ("CLI-SEAM-020", "emrys.stages.duplicate_marking.validator"),
    ("CLI-SEAM-021", "emrys.stages.fasta_sidecars.validator"),
    ("CLI-SEAM-022", "emrys.stages.gtf_to_bed12.converter"),
    ("CLI-SEAM-023", "emrys.stages.gtf_to_bed12.validator"),
    ("CLI-SEAM-024", "emrys.stages.mechanical_orientation.validator"),
    ("CLI-SEAM-025", "emrys.stages.partitioned_cohort_mpileup.validator"),
    ("CLI-SEAM-026", "emrys.stages.split_n_cigar.validator"),
    ("CLI-SEAM-027", "emrys.stages.star_alignment.validator"),
    ("CLI-SEAM-028", "emrys.stages.star_index.validator"),
)

# (documented ID, exact source path, exact target, violated durable rule).
# Successors and exit conditions remain authoritative in SOURCE_TOPOLOGY.md.
TRANSITIONS: tuple[tuple[str, str, str, str], ...] = (
    ("SRC-TRANS-001", "src/emrys/contracts/artifacts/_artifact_contracts/schema.py", "emrys.libraries.validation", RULE_CONTRACT_NEUTRAL),
    ("SRC-TRANS-002", "src/emrys/contracts/orchestration/api.py", "emrys.libraries.source_authority", RULE_CONTRACT_NEUTRAL),
    ("SRC-TRANS-003", "src/emrys/contracts/scientific_evidence/step08.py", "emrys.libraries.validation", RULE_CONTRACT_NEUTRAL),
    ("SRC-TRANS-004", "src/emrys/contracts/scientific_evidence/step08.py", "emrys.libraries.validation.tsv", RULE_CONTRACT_NEUTRAL),
    ("SRC-TRANS-005", "src/emrys/contracts/scientific_evidence/step08.py", "emrys.libraries.alignments.orientation", RULE_CONTRACT_NEUTRAL),
    ("SRC-TRANS-006", "src/emrys/contracts/scientific_evidence/step09.py", "emrys.libraries.alignments.orientation", RULE_CONTRACT_NEUTRAL),
    ("SRC-TRANS-007", "src/emrys/orchestration/local_pilot/doctor.py", "emrys.evidence.runtime_availability.inspector", RULE_ORCHESTRATION_BOUNDARY),
    ("SRC-TRANS-008", "src/emrys/orchestration/local_pilot/doctor.py", "emrys.evidence.storage_inventory.qualification", RULE_ORCHESTRATION_BOUNDARY),
    ("SRC-TRANS-009", "src/emrys/orchestration/local_pilot/lifecycle.py", "emrys.evidence.runtime_availability.inspector", RULE_ORCHESTRATION_BOUNDARY),
    ("SRC-TRANS-010", "src/emrys/orchestration/local_pilot/lifecycle.py", "emrys.evidence.storage_inventory.qualification", RULE_ORCHESTRATION_BOUNDARY),
    ("SRC-TRANS-011", "src/emrys/orchestration/local_pilot/onboarding.py", "emrys.stages.gtf_to_bed12.converter", RULE_ORCHESTRATION_BOUNDARY),
    ("SRC-TRANS-012", "src/emrys/orchestration/local_pilot/onboarding.py", "emrys.evidence.runtime_availability.inspector", RULE_ORCHESTRATION_BOUNDARY),
)


def repository_root(value: Path) -> Path:
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


def python_sources(root: Path) -> tuple[Path, ...]:
    result = subprocess.run(
        [
            "git", "-C", str(root), "ls-files", "--cached", "--others",
            "--exclude-standard", "--", "src/emrys",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise DependencyError(
            "could not inventory src/emrys: "
            + (result.stderr.strip() or result.stdout.strip() or "no diagnostic")
        )
    paths: list[Path] = []
    for relative in result.stdout.splitlines():
        path = root / relative
        if path.suffix != ".py" or (not path.exists() and not path.is_symlink()):
            continue
        if path.is_symlink() or not path.is_file():
            raise DependencyError(f"Python source must be a regular file: {relative}")
        paths.append(path)
    return tuple(sorted(paths))


def module_identity(root: Path, path: Path) -> tuple[str, bool]:
    parts = list(path.relative_to(root / "src").with_suffix("").parts)
    is_package = parts[-1] == "__init__"
    if is_package:
        parts.pop()
    return ".".join(parts), is_package


def static_targets(
    node: ast.Import | ast.ImportFrom,
    source_module: str,
    source_is_package: bool,
    known_modules: frozenset[str],
) -> tuple[str, ...]:
    if isinstance(node, ast.Import):
        return tuple(alias.name for alias in node.names)
    if node.level:
        package = source_module if source_is_package else source_module.rpartition(".")[0]
        parts = package.split(".") if package else []
        parents = node.level - 1
        if parents > len(parts):
            return ()
        parts = parts[:-parents] if parents else parts
        if node.module:
            parts.extend(node.module.split("."))
        base = ".".join(parts)
    else:
        base = node.module or ""
    if not base:
        return ()
    return tuple(
        candidate if candidate in known_modules else base
        for alias in node.names
        for candidate in (f"{base}.{alias.name}" if alias.name != "*" else base,)
    )


def dynamic_bindings(tree: ast.AST) -> tuple[dict[str, str], dict[str, str]]:
    modules: dict[str, str] = {}
    functions = {"__import__": "builtin"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "importlib":
                    modules[alias.asname or "importlib"] = "importlib"
                elif alias.name.startswith("importlib.") and alias.asname is None:
                    modules["importlib"] = "importlib"
                elif alias.name == "builtins":
                    modules[alias.asname or "builtins"] = "builtins"
        elif isinstance(node, ast.ImportFrom) and node.module in {"importlib", "builtins"}:
            expected = "import_module" if node.module == "importlib" else "__import__"
            kind = "importlib" if node.module == "importlib" else "builtin"
            functions.update(
                (alias.asname or alias.name, kind)
                for alias in node.names
                if alias.name == expected
            )
    return modules, functions


def dynamic_target(
    node: ast.Call,
    modules: dict[str, str],
    functions: dict[str, str],
) -> str | None:
    kind = functions.get(node.func.id) if isinstance(node.func, ast.Name) else None
    if (
        isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and (
            (node.func.attr == "import_module" and modules.get(node.func.value.id) == "importlib")
            or (node.func.attr == "__import__" and modules.get(node.func.value.id) == "builtins")
        )
    ):
        kind = "importlib" if node.func.attr == "import_module" else "builtin"
    if kind is None or not node.args:
        return None
    value = node.args[0]
    if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
        return None
    target = value.value
    if kind != "importlib" or not target.startswith("."):
        return target
    package: ast.expr | None = node.args[1] if len(node.args) > 1 else None
    package = next(
        (keyword.value for keyword in node.keywords if keyword.arg == "package"),
        package,
    )
    if not isinstance(package, ast.Constant) or not isinstance(package.value, str):
        return None
    level = len(target) - len(target.lstrip("."))
    parts = package.value.split(".")
    if level > len(parts):
        return None
    resolved = parts[: len(parts) - level + 1]
    suffix = target[level:]
    if suffix:
        resolved.extend(suffix.split("."))
    return ".".join(resolved)


def collect_edges(root: Path, paths: Sequence[Path]) -> tuple[ImportEdge, ...]:
    identities = {path: module_identity(root, path) for path in paths}
    known_modules = frozenset(module for module, _ in identities.values())
    edges: set[ImportEdge] = set()
    for path, (source_module, source_is_package) in identities.items():
        relative = path.relative_to(root).as_posix()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative)
        except (OSError, UnicodeError, SyntaxError) as exc:
            line = getattr(exc, "lineno", 0) or 0
            raise DependencyError(f"could not parse {relative}:{line}: {exc}") from exc
        modules, functions = dynamic_bindings(tree)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                targets = static_targets(node, source_module, source_is_package, known_modules)
            elif isinstance(node, ast.Call):
                target = dynamic_target(node, modules, functions)
                targets = (target,) if target else ()
            else:
                continue
            edges.update(
                ImportEdge(relative, node.lineno, source_module, target)
                for target in targets
                if target == "emrys" or target.startswith("emrys.")
            )
    return tuple(sorted(edges))


def owner(module: str) -> tuple[str, str]:
    if module == "emrys":
        return "root", "emrys"
    if module == "emrys.__main__" or module.startswith("emrys.__main__."):
        return "composition", "emrys.__main__"
    parts = module.split(".")
    domain = parts[1] if len(parts) > 1 else ""
    if domain in {"stages", "analyses", "evidence"}:
        return "functional", ".".join(parts[:3])
    if domain == "libraries":
        return "libraries", ".".join(parts[:3])
    if domain in {"contracts", "ingestion", "orchestration", "reporting"}:
        return domain, f"emrys.{domain}"
    return "unclassified", f"emrys.{domain}"


def forbidden_rule(
    edge: ImportEdge,
    composition_targets: frozenset[str],
) -> tuple[str, str] | None:
    source_kind, source_owner = owner(edge.source_module)
    target_kind, target_owner = owner(edge.target_module)
    declared_reporting_seam = (
        edge.source_module,
        edge.target_module,
    ) in ORCHESTRATION_REPORTING_SEAMS
    declared_analysis_module_seam = (
        edge.target_module == "emrys.analyses"
        and source_kind in {"functional", "orchestration", "reporting"}
    )
    if target_kind == "unclassified":
        return RULE_SOURCE_CLASSIFICATION, "target belongs to an unclassified domain"
    if source_kind == "root" and target_kind != "root":
        return RULE_SOURCE_CLASSIFICATION, "package metadata cannot compose implementation"
    if target_kind == "composition" and source_kind != "composition":
        return RULE_ORCHESTRATION_BOUNDARY, "lower code cannot import the composition root"
    private = any(
        part.startswith("_") and not part.startswith("__")
        for part in edge.target_module.split(".")[2:]
    )
    if source_owner != target_owner and private and not declared_reporting_seam:
        return RULE_PRIVATE_OWNER, "private modules are owner-local"
    if source_kind == "composition":
        if edge.target_module not in composition_targets:
            return RULE_ORCHESTRATION_BOUNDARY, "target is not a current CLI seam"
        return None
    if source_kind == "contracts" and target_kind not in {"contracts", "root"}:
        return RULE_CONTRACT_NEUTRAL, "contracts cannot import implementation"
    if source_kind == "libraries" and target_kind not in {"contracts", "libraries", "root"}:
        return RULE_LIBRARY_NEUTRAL, "neutral libraries cannot import product owners"
    if source_kind == "functional" and (
        (target_kind == "functional" and source_owner != target_owner)
        or target_kind in {"ingestion", "orchestration", "reporting", "composition"}
    ) and not declared_analysis_module_seam:
        return RULE_FUNCTIONAL_OWNER, "functional owners cannot import peer/product owners"
    blocked = {
        "ingestion": {"functional", "orchestration", "reporting", "composition"},
        "reporting": {"functional", "ingestion", "orchestration", "composition"},
    }
    if target_kind in blocked.get(source_kind, set()):
        if declared_analysis_module_seam:
            return None
        rule = RULE_INGESTION_BOUNDARY if source_kind == "ingestion" else RULE_REPORTING_DOWNSTREAM
        return rule, f"{source_kind} dependency direction is reversed"
    if source_kind == "orchestration" and target_kind in {"functional", "ingestion", "reporting"}:
        if not (declared_reporting_seam or declared_analysis_module_seam):
            return RULE_ORCHESTRATION_BOUNDARY, "target is not a declared public capability"
    return None


def indexed_rosters(
    transitions: Sequence[tuple[str, str, str, str]],
    seams: Sequence[tuple[str, str]],
) -> tuple[dict[tuple[str, str], tuple[str, str]], dict[str, str]]:
    transition_index: dict[tuple[str, str], tuple[str, str]] = {}
    transition_ids: set[str] = set()
    for transition_id, source, target, rule_id in transitions:
        key = (source, target)
        if transition_id in transition_ids or key in transition_index or rule_id not in KNOWN_RULE_IDS:
            raise DependencyError(f"invalid transition roster entry: {transition_id}")
        transition_ids.add(transition_id)
        transition_index[key] = (transition_id, rule_id)
    seam_index: dict[str, str] = {}
    seam_ids: set[str] = set()
    for seam_id, target in seams:
        if seam_id in seam_ids or target in seam_index:
            raise DependencyError(f"invalid composition roster entry: {seam_id}")
        seam_ids.add(seam_id)
        seam_index[target] = seam_id
    return transition_index, seam_index


def library_cycle(edges: Iterable[ImportEdge]) -> Problem | None:
    graph: dict[str, set[str]] = {}
    locations: dict[tuple[str, str], ImportEdge] = {}
    for edge in edges:
        source_kind, source_owner = owner(edge.source_module)
        target_kind, target_owner = owner(edge.target_module)
        if source_kind == target_kind == "libraries" and source_owner != target_owner:
            graph.setdefault(source_owner, set()).add(target_owner)
            locations.setdefault((source_owner, target_owner), edge)
    try:
        TopologicalSorter(
            {owner: tuple(sorted(targets)) for owner, targets in sorted(graph.items())}
        ).prepare()
    except CycleError as exc:
        cycle = tuple(reversed(exc.args[1]))
        edge = next(locations[pair] for pair in zip(cycle, cycle[1:]) if pair in locations)
        return Problem(
            edge.source_path,
            edge.line,
            RULE_LIBRARY_NEUTRAL,
            "neutral library dependency cycle: " + " -> ".join(cycle),
        )
    return None


def inspect_repository(
    value: Path,
    *,
    transitions: Sequence[tuple[str, str, str, str]] = TRANSITIONS,
    composition_seams: Sequence[tuple[str, str]] = COMPOSITION_SEAMS,
) -> tuple[Problem, ...]:
    root = repository_root(value)
    paths = python_sources(root)
    edges = collect_edges(root, paths)
    transition_index, seam_index = indexed_rosters(transitions, composition_seams)
    observed_transitions: set[tuple[str, str]] = set()
    observed_seams: set[str] = set()
    problems: list[Problem] = []

    for path in paths:
        module, _ = module_identity(root, path)
        if owner(module)[0] == "unclassified":
            problems.append(
                Problem(
                    path.relative_to(root).as_posix(), 0, RULE_SOURCE_CLASSIFICATION,
                    f"source belongs to an unclassified domain: {module}",
                )
            )

    composition_targets = frozenset(seam_index)
    for edge in edges:
        if edge.source_module == "emrys.__main__" and edge.target_module in seam_index:
            observed_seams.add(edge.target_module)
        violation = forbidden_rule(edge, composition_targets)
        transition = transition_index.get((edge.source_path, edge.target_module))
        if transition is not None and violation is not None and transition[1] == violation[0]:
            observed_transitions.add((edge.source_path, edge.target_module))
        elif violation is not None:
            rule_id, detail = violation
            problems.append(
                Problem(
                    edge.source_path, edge.line, rule_id,
                    f"{detail}: {edge.source_module} -> {edge.target_module}",
                )
            )

    for key, (transition_id, rule_id) in transition_index.items():
        if key not in observed_transitions:
            problems.append(
                Problem(
                    key[0], 0, rule_id,
                    f"stale transition {transition_id} to {key[1]}; remove or reconcile it in SOURCE_TOPOLOGY.md",
                )
            )
    for target, seam_id in seam_index.items():
        if target not in observed_seams:
            problems.append(
                Problem(
                    "src/emrys/__main__.py", 0, RULE_ORCHESTRATION_BOUNDARY,
                    f"stale current composition seam {seam_id} to {target}",
                )
            )
    cycle = library_cycle(edges)
    if cycle:
        problems.append(cycle)
    return tuple(sorted(problems))


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate bounded EMRYS Python source-dependency rules."
    )
    parser.add_argument("--repo", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    try:
        problems = inspect_repository(args.repo)
    except DependencyError as exc:
        raise SystemExit(f"ERROR: {exc}") from exc
    if problems:
        raise SystemExit(
            "ERROR: Source dependency gate failures:\n"
            + "\n".join(problem.render() for problem in problems)
        )
    print("PASS source dependencies")


if __name__ == "__main__":
    main()
