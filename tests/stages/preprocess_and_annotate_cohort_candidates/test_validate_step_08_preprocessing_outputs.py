import csv
import hashlib
import importlib.util
import os
import subprocess
import sys
import textwrap
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[3]
ROSTER_ORACLE = ROOT / "tests" / "validation_roster_expectations.py"
ROSTER_SPEC = importlib.util.spec_from_file_location(
    "preprocess_and_annotate_cohort_candidates_validation_roster_oracle",
    ROSTER_ORACLE,
)
assert ROSTER_SPEC is not None and ROSTER_SPEC.loader is not None
ROSTER_MODULE = importlib.util.module_from_spec(ROSTER_SPEC)
ROSTER_SPEC.loader.exec_module(ROSTER_MODULE)
assert_exact_check_roster = ROSTER_MODULE.assert_exact_check_roster

STEP08_PATH = (
    ROOT
    / "src"
    / "norad"
    / "contracts"
    / "scientific_evidence"
    / "step08.py"
)
STEP08_TEST_MODULE_NAME = "_norad_step08_scientific_evidence_contract"
STEP08_SPEC = importlib.util.spec_from_file_location(
    STEP08_TEST_MODULE_NAME,
    STEP08_PATH,
)
assert STEP08_SPEC is not None and STEP08_SPEC.loader is not None
STEP08_MODULE = sys.modules.get(STEP08_TEST_MODULE_NAME)
if STEP08_MODULE is None:
    STEP08_MODULE = importlib.util.module_from_spec(STEP08_SPEC)
    sys.modules[STEP08_TEST_MODULE_NAME] = STEP08_MODULE
    try:
        STEP08_SPEC.loader.exec_module(STEP08_MODULE)
        setattr(STEP08_MODULE, "_NORAD_STEP08_CONTRACT_READY", True)
    except BaseException:
        if sys.modules.get(STEP08_TEST_MODULE_NAME) is STEP08_MODULE:
            sys.modules.pop(STEP08_TEST_MODULE_NAME, None)
        raise
STEP08_INPUTS_HEADER = STEP08_MODULE.STEP08_INPUTS_HEADER
STEP08_METADATA_HEADER = STEP08_MODULE.STEP08_METADATA_HEADER
STEP08_SUMMARY_HEADER = STEP08_MODULE.STEP08_SUMMARY_HEADER

SCRIPT = (
    ROOT
    / "src"
    / "norad"
    / "stages"
    / "preprocess_and_annotate_cohort_candidates"
    / "validate_step_08_preprocessing_outputs.py"
)


def write_tsv(path, header, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def read_tsv(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.reader(stream, delimiter="\t"))


def replace_cell(path, data_row, column, value):
    table = read_tsv(path)
    table[data_row + 1][table[0].index(column)] = value
    write_tsv(path, table[0], table[1:])


def replace_column(path, column, value):
    table = read_tsv(path)
    index = table[0].index(column)
    for row in table[1:]:
        row[index] = value
    write_tsv(path, table[0], table[1:])


def fixture(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    samples = root / "samples.tsv"
    write_tsv(
        samples,
        ("sample_id", "r1_fastq", "r2_fastq", "strandedness", "condition", "replicate"),
        (("S", "/r1", "/r2", "reverse", "control", "1"),),
    )
    partitions = root / "partitions.tsv"
    write_tsv(
        partitions,
        ("partition_id", "selector_type", "selector_value"),
        (("p1", "region", "1"),),
    )
    annotation = root / "annotation.gtf"
    annotation.write_text('1\ts\tgene\t1\t10\t.\t+\t.\tgene_id "g";\n')
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    sites = root / "cohort.step08_sites.tsv"
    write_tsv(
        sites,
        STEP08_METADATA_HEADER + ("DP__S", "AD__S", "AF__S"),
        (
            (
                "p1", "c1", "FWD_like", "1", "2", "1", "A", "G", "A", "G",
                "+", "g", "t", "TRUE", "FALSE", "FALSE", "TRUE", "FALSE", "60",
                "PASS", "4", "legacy_provisional_v1", "10", "2", "0.2",
            ),
            (
                "p1", "c2", "REV_like", "1", "3", "1", "C", "T", "G", "A",
                "-", "g", "t", "TRUE", "FALSE", "FALSE", "TRUE", "FALSE", "50",
                "PASS", "3", "legacy_provisional_v1", "8", "1", "0.125",
            ),
        ),
    )
    inputs = root / "cohort.step08_inputs.tsv"
    common = (
        "cohort", "p1", "region", "1", None, "/step07/receipt.tsv", "1" * 64,
        None, "2" * 64, digest(samples), digest(partitions), str(annotation.resolve()),
        digest(annotation), "1", "1", "1", "1", "1", "0", "0",
    )
    write_tsv(
        inputs,
        STEP08_INPUTS_HEADER,
        (
            (*common[:4], "FWD_like", *common[5:7], "/step07/fwd.vcf",
             *common[8:], "1", "legacy_provisional_v1"),
            (*common[:4], "REV_like", *common[5:7], "/step07/rev.vcf",
             *common[8:], "1", "legacy_provisional_v1"),
        ),
    )
    summary = root / "cohort.step08_summary.tsv"
    write_tsv(
        summary,
        STEP08_SUMMARY_HEADER,
        ((
            "cohort", "1", "1", "2", "1", "2", "2", "2", "0", "0", "2",
            digest(samples), digest(partitions), str(annotation.resolve()),
            digest(annotation), "legacy_provisional_v1",
        ),),
    )
    out = root / "out"; out.mkdir()
    return samples, partitions, annotation, sites, inputs, summary, out / "cohort.validation.tsv"


def arguments(values, *extra):
    samples, partitions, annotation, sites, inputs, summary, output = values
    return [
        "--cohort-id", "cohort",
        "--sample-manifest", str(samples),
        "--partition-manifest", str(partitions),
        "--annotation-gtf", str(annotation),
        "--sites", str(sites),
        "--inputs", str(inputs),
        "--summary", str(summary),
        "--output", str(output),
        *extra,
    ]


def run(values, *extra, cwd=ROOT):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *arguments(values, *extra)],
        cwd=cwd, text=True, capture_output=True,
    )


def load_validator():
    spec = importlib.util.spec_from_file_location(
        "_test_step08_preprocessing_validator", SCRIPT
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rows(path):
    with path.open() as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def test_arbitrary_cwd_dry_execute_repeat_byte_parity_has_no_residue(tmp_path):
    values = fixture(tmp_path / "fixture")
    invocation_cwd = tmp_path / "arbitrary-cwd"
    invocation_cwd.mkdir()

    dry = run(values, cwd=invocation_cwd)
    assert dry.returncode == 0, dry.stderr
    assert not values[-1].exists()
    assert list(invocation_cwd.iterdir()) == []

    first = run(values, "--execute", cwd=invocation_cwd)
    assert first.returncode == 0, first.stderr
    first_bytes = values[-1].read_bytes()
    assert first.stdout.startswith(first_bytes.decode())
    assert list(invocation_cwd.iterdir()) == []

    second = run(values, "--execute", cwd=invocation_cwd)
    assert second.returncode == 0, second.stderr
    assert values[-1].read_bytes() == first_bytes
    assert dry.stdout.startswith(first_bytes.decode())
    assert second.stdout.startswith(first_bytes.decode())
    assert {path.name for path in values[-1].parent.iterdir()} == {values[-1].name}


def test_execute_publishes_five_passes(tmp_path):
    values = fixture(tmp_path)
    result = run(values, "--execute")
    assert result.returncode == 0, result.stderr
    assert_exact_check_roster(rows(values[-1]), "08")
    assert {row["status"] for row in rows(values[-1])} == {"pass"}


def test_each_check_id_is_observable_as_exit_zero_failed_evidence(tmp_path):
    check_ids = (
        "output_transaction",
        "manifest_annotation_identity",
        "input_receipt_reconciliation",
        "sites_order_uniqueness",
        "summary_count_reconciliation",
    )
    for check_id in check_ids:
        values = fixture(tmp_path / check_id)
        if check_id == "output_transaction":
            table = read_tsv(values[3])
            table[0][0] = "unexpected_partition_id"
            write_tsv(values[3], table[0], table[1:])
        elif check_id == "manifest_annotation_identity":
            replace_column(values[4], "annotation_gtf", "/different/annotation.gtf")
        elif check_id == "input_receipt_reconciliation":
            replace_cell(values[4], 0, "orientation", "REV_like")
        elif check_id == "sites_order_uniqueness":
            replace_cell(values[3], 1, "candidate_id", "c1")
        else:
            replace_cell(values[5], 0, "observed_vcf_record_count", "9")

        result = run(values, "--execute")
        assert result.returncode == 0, (check_id, result.stderr)
        report_rows = rows(values[-1])
        assert_exact_check_roster(report_rows, "08")
        statuses = {row["check_id"]: row["status"] for row in report_rows}
        assert statuses[check_id] == "fail"


def test_post_build_mutation_of_each_input_preserves_predecessor(tmp_path, capsys):
    validator = load_validator()
    for role_index in range(6):
        values = fixture(tmp_path / f"role-{role_index}")
        baseline = run(values, "--execute")
        assert baseline.returncode == 0, baseline.stderr
        predecessor = values[-1].read_bytes()
        target = values[role_index]
        original_snapshot = validator.report.regular_snapshot
        calls = 0

        def mutate_after_build(path, label):
            nonlocal calls
            calls += 1
            if calls == 7:
                target.write_bytes(target.read_bytes() + b"\n# changed after build\n")
            return original_snapshot(path, label)

        validator.report.regular_snapshot = mutate_after_build
        try:
            status = validator.main(arguments(values, "--execute"))
        finally:
            validator.report.regular_snapshot = original_snapshot
        captured = capsys.readouterr()
        assert status == 2, (role_index, captured.err)
        assert "Input changed after validation" in captured.err
        assert values[-1].read_bytes() == predecessor
        assert {path.name for path in values[-1].parent.iterdir()} == {
            values[-1].name
        }


def test_equivalent_annotation_spelling_is_failed_identity_evidence(tmp_path):
    values = fixture(tmp_path)
    alias = tmp_path / "equivalent"
    alias.mkdir()
    equivalent_annotation = alias / ".." / values[2].name
    replace_column(values[4], "annotation_gtf", str(equivalent_annotation))
    replace_column(values[5], "annotation_gtf", str(equivalent_annotation))
    values = (values[0], values[1], equivalent_annotation, *values[3:])

    result = run(values, "--execute")
    assert result.returncode == 0, result.stderr
    report_rows = rows(values[-1])
    assert_exact_check_roster(report_rows, "08")
    statuses = {row["check_id"]: row["status"] for row in report_rows}
    assert statuses["manifest_annotation_identity"] == "fail"


def test_arbitrary_candidate_ids_and_reversed_rows_are_false_passes(tmp_path):
    values = fixture(tmp_path)
    table = read_tsv(values[3])
    candidate_index = table[0].index("candidate_id")
    table[1][candidate_index] = "arbitrary-unique-beta"
    table[2][candidate_index] = "arbitrary-unique-alpha"
    write_tsv(values[3], table[0], reversed(table[1:]))

    result = run(values, "--execute")
    assert result.returncode == 0, result.stderr
    report_rows = rows(values[-1])
    assert_exact_check_roster(report_rows, "08")
    assert {row["status"] for row in report_rows} == {"pass"}


def test_summary_disagreement_is_failed_evidence(tmp_path):
    values = fixture(tmp_path)
    text = values[5].read_text()
    values[5].write_text(text.replace("\t2\t2\t2\t0\t0\t2\t", "\t9\t2\t2\t0\t0\t2\t"))
    assert run(values, "--execute").returncode == 0
    status = {row["check_id"]: row["status"] for row in rows(values[-1])}
    assert status["summary_count_reconciliation"] == "fail"


def test_missing_input_and_wrong_output_fail_closed(tmp_path):
    values = fixture(tmp_path)
    values[3].unlink()
    assert run(values, "--execute").returncode == 2
    values = fixture(tmp_path / "second")
    bad = (*values[:-1], values[-1].parent / "wrong.tsv")
    assert run(bad, "--execute").returncode == 2


def test_foreign_lock_is_preserved(tmp_path):
    values = fixture(tmp_path)
    lock = values[-1].parent / f".{values[-1].name}.lock"
    lock.write_text("foreign\n")
    assert run(values, "--execute").returncode == 2
    assert lock.read_text() == "foreign\n"


def test_step08_loader_reuses_exact_owner_without_sys_path_change():
    validator = load_validator()
    before_sys_path = list(sys.path)
    cached = sys.modules[validator._STEP08_MODULE_NAME]

    assert validator._load_step08_contract() is cached
    assert Path(cached.__file__).resolve() == STEP08_PATH.resolve()
    assert getattr(cached, validator._STEP08_READY_ATTRIBUTE) is True
    assert sys.path == before_sys_path


def test_step08_loader_rejects_and_preserves_foreign_cache(
    tmp_path, monkeypatch
):
    validator = load_validator()
    name = validator._STEP08_MODULE_NAME
    foreign = ModuleType(name)
    foreign.__file__ = str(tmp_path / "foreign_step08.py")
    setattr(foreign, validator._STEP08_READY_ATTRIBUTE, True)
    before_sys_path = list(sys.path)
    monkeypatch.setitem(sys.modules, name, foreign)

    with pytest.raises(ImportError, match="resolves to"):
        validator._load_step08_contract()

    assert sys.modules[name] is foreign
    assert sys.path == before_sys_path


def test_step08_loader_rejects_and_preserves_partial_exact_cache(monkeypatch):
    validator = load_validator()
    name = validator._STEP08_MODULE_NAME
    partial = ModuleType(name)
    partial.__file__ = str(STEP08_PATH)
    before_sys_path = list(sys.path)
    monkeypatch.setitem(sys.modules, name, partial)

    with pytest.raises(ImportError, match="partially initialized"):
        validator._load_step08_contract()

    assert sys.modules[name] is partial
    assert sys.path == before_sys_path


@pytest.mark.parametrize(
    "specification",
    (None, SimpleNamespace(loader=None)),
    ids=("missing-spec", "missing-loader"),
)
def test_step08_loader_fails_closed_without_usable_specification(
    specification, monkeypatch
):
    validator = load_validator()
    name = validator._STEP08_MODULE_NAME
    monkeypatch.delitem(sys.modules, name, raising=False)
    monkeypatch.setattr(
        validator.importlib.util,
        "spec_from_file_location",
        lambda *_args, **_kwargs: specification,
    )

    with pytest.raises(ImportError, match="module specification"):
        validator._load_step08_contract()

    assert name not in sys.modules


def test_step08_loader_cleans_up_owned_partial_after_execution_failure(
    tmp_path, monkeypatch
):
    validator = load_validator()
    name = validator._STEP08_MODULE_NAME
    failing_owner = tmp_path / "step08.py"
    failing_owner.write_text(
        "raise RuntimeError('injected Step 08 execution failure')\n",
        encoding="utf-8",
    )
    monkeypatch.delitem(sys.modules, name, raising=False)
    monkeypatch.setattr(validator, "_STEP08_MODULE_PATH", failing_owner)

    with pytest.raises(RuntimeError, match="injected Step 08 execution failure"):
        validator._load_step08_contract()

    assert name not in sys.modules


def test_step08_public_loader_failure_is_sanitized_one_line(tmp_path):
    invocation_cwd = tmp_path / "invocation"
    invocation_cwd.mkdir()
    setup = textwrap.dedent(
        f"""
        import runpy
        import sys
        from types import ModuleType

        class InvalidPath:
            def __fspath__(self):
                raise RuntimeError("injected\\n" + chr(0) + " Step 08 path")

        cached = ModuleType("_norad_step08_scientific_evidence_contract")
        cached.__file__ = InvalidPath()
        sys.modules[cached.__name__] = cached
        runpy.run_path({str(SCRIPT)!r}, run_name="__main__")
        """
    )
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        [sys.executable, "-c", setup],
        cwd=invocation_cwd,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert "\x00" not in result.stderr
    assert result.stderr.splitlines() == [
        "ERROR: unable to load Step 08 scientific-evidence contract at "
        f"{STEP08_PATH}: RuntimeError: injected Step 08 path"
    ]
    assert list(invocation_cwd.iterdir()) == []


def test_step08_exact_initialization_does_not_mutate_sys_path(monkeypatch):
    validator = load_validator()
    name = validator._STEP08_MODULE_NAME
    before_sys_path = list(sys.path)
    monkeypatch.delitem(sys.modules, name, raising=False)

    loaded = validator._load_step08_contract()

    assert Path(loaded.__file__).resolve() == STEP08_PATH.resolve()
    assert getattr(loaded, validator._STEP08_READY_ATTRIBUTE) is True
    assert sys.modules[name] is loaded
    assert sys.path == before_sys_path
