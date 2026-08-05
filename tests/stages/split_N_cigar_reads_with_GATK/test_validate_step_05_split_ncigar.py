import csv
import importlib.util
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest


ROOT = Path(__file__).resolve().parents[3]
ROSTER_ORACLE = ROOT / "tests" / "contract_integration" / "validation_rosters" / "validation_roster_expectations.py"
ROSTER_SPEC = importlib.util.spec_from_file_location(
    "split_n_cigar_reads_with_gatk_validation_roster_oracle",
    ROSTER_ORACLE,
)
assert ROSTER_SPEC is not None and ROSTER_SPEC.loader is not None
ROSTER_MODULE = importlib.util.module_from_spec(ROSTER_SPEC)
ROSTER_SPEC.loader.exec_module(ROSTER_MODULE)
assert_exact_check_roster = ROSTER_MODULE.assert_exact_check_roster
SCRIPT = (
    ROOT
    / "src"
    / "norad"
    / "stages"
    / "split_N_cigar_reads_with_GATK"
    / "validate_step_05_split_ncigar.py"
)
TEST_MODULE_NAME = "_norad_test_validate_step_05_split_ncigar"


def fixture(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    bam = root / "S.split_ncigar.bam"; bam.write_bytes(b"BAM\x01synthetic")
    bai = root / "S.split_ncigar.bam.bai"; bai.write_bytes(b"BAI\x01synthetic")
    fasta = root / "genome.fa"; fasta.write_text(">1\nACGT\n")
    fai = root / "genome.fa.fai"; fai.write_text("1\t4\t3\t4\t5\n")
    dictionary = root / "genome.dict"
    dictionary.write_text("@HD\tVN:1.6\n@SQ\tSN:1\tLN:4\n")
    tool = root / "samtools"
    tool.write_text(
        "#!/usr/bin/env bash\nset -euo pipefail\n"
        "case \"$1 $2\" in\n"
        " 'quickcheck -v') exit \"${QUICKCHECK_EXIT:-0}\" ;;\n"
        " 'view -H')\n"
        "   if [[ \"${HEADER_EXIT:-0}\" != 0 ]]; then\n"
        "     printf 'forced header failure\\n' >&2\n"
        "     exit \"$HEADER_EXIT\"\n"
        "   fi\n"
        "   if [[ -n \"${MUTATE_PATH:-}\" ]]; then\n"
        "     printf 'post-build mutation\\n' >> \"$MUTATE_PATH\"\n"
        "   fi\n"
        "   printf '@HD\\tVN:1.6\\tSO:%s\\n@RG\\tID:%s\\tSM:%s\\n' "
        "\"${SORT_ORDER:-coordinate}\" \"${RG_ID:-S}\" \"${RG_SM:-S}\" ;;\n"
        " *) exit 9 ;;\nesac\n"
    )
    tool.chmod(0o755)
    out = root / "out"; out.mkdir()
    return bam, bai, fasta, fai, dictionary, tool, out / "S.validation.tsv"


def run(values, *extra, cwd=ROOT, environment=None):
    bam, bai, fasta, fai, dictionary, tool, output = values
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--scope-id", "S", "--bam", str(bam),
         "--bai", str(bai), "--reference-fasta", str(fasta),
         "--reference-fai", str(fai), "--reference-dict", str(dictionary),
         "--samtools-bin", str(tool), "--output", str(output), *extra],
        cwd=cwd, env=environment, text=True, capture_output=True,
    )


def rows(path):
    with path.open() as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def load_validator() -> ModuleType:
    sys.modules.pop(TEST_MODULE_NAME, None)
    spec = importlib.util.spec_from_file_location(TEST_MODULE_NAME, SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not exact-load validator: {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[TEST_MODULE_NAME] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        if sys.modules.get(TEST_MODULE_NAME) is module:
            sys.modules.pop(TEST_MODULE_NAME, None)
        raise
    return module


@pytest.fixture
def validator_module():
    module = load_validator()
    try:
        yield module
    finally:
        if sys.modules.get(TEST_MODULE_NAME) is module:
            sys.modules.pop(TEST_MODULE_NAME, None)


def assert_loader_fault_is_residue_free(
    *, before_sys_path, invocation_cwd, report_path
):
    assert sys.path == before_sys_path
    assert not report_path.exists()
    assert not any(invocation_cwd.iterdir())


def test_dry_run_is_side_effect_free(tmp_path):
    values = fixture(tmp_path)
    assert run(values).returncode == 0
    assert not values[-1].exists()


def test_execute_publishes_five_passes(tmp_path):
    values = fixture(tmp_path)
    result = run(values, "--execute")
    assert result.returncode == 0, result.stderr
    assert_exact_check_roster(rows(values[-1]), "05")
    assert {row["status"] for row in rows(values[-1])} == {"pass"}


def test_sidecar_disagreement_is_failed_evidence(tmp_path):
    values = fixture(tmp_path)
    values[3].write_text("1\t5\t3\t5\t6\n")
    assert run(values, "--execute").returncode == 0
    status = {row["check_id"]: row["status"] for row in rows(values[-1])}
    assert status["reference_sidecars"] == "fail"


def test_reference_parsing_short_circuits_on_first_parser_error(tmp_path):
    values = fixture(tmp_path)
    values[2].write_text("sequence-before-header\n")
    values[3].write_text("also-malformed\n")
    values[4].write_text("@SQ\tLN:not-a-number\n")
    result = run(values, "--execute")
    assert result.returncode == 0, result.stderr
    by_check = {row["check_id"]: row for row in rows(values[-1])}
    sidecars = by_check["reference_sidecars"]
    assert sidecars["status"] == "fail"
    assert sidecars["observed"] == "FASTA sequence appears before its header"


def test_missing_input_and_wrong_output_fail_closed(tmp_path):
    values = fixture(tmp_path)
    values[1].unlink()
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


def test_arbitrary_cwd_dry_run_execute_and_repeat_are_byte_identical(tmp_path):
    values = fixture(tmp_path / "fixture")
    other_cwd = tmp_path / "other-cwd"
    other_cwd.mkdir()
    input_paths = values[:-1]
    before = {path: path.read_bytes() for path in input_paths}

    dry_run = run(values, cwd=other_cwd)
    assert dry_run.returncode == 0, dry_run.stderr
    assert not values[-1].exists()

    first = run(values, "--execute", cwd=other_cwd)
    assert first.returncode == 0, first.stderr
    first_report = values[-1].read_bytes()
    assert dry_run.stdout.encode().startswith(first_report)

    second = run(values, "--execute", cwd=other_cwd)
    assert second.returncode == 0, second.stderr
    assert values[-1].read_bytes() == first_report
    assert {path: path.read_bytes() for path in input_paths} == before


def test_quickcheck_failure_is_published_as_failed_evidence(tmp_path):
    values = fixture(tmp_path)
    environment = {**os.environ, "QUICKCHECK_EXIT": "7"}
    result = run(values, "--execute", environment=environment)

    assert result.returncode == 0, result.stderr
    by_check = {row["check_id"]: row for row in rows(values[-1])}
    assert by_check["samtools_quickcheck"]["status"] == "fail"
    assert by_check["samtools_quickcheck"]["observed"] == "exit=7"


def test_header_tool_failure_exits_two_without_publication(tmp_path):
    values = fixture(tmp_path)
    environment = {**os.environ, "HEADER_EXIT": "8"}
    result = run(values, "--execute", environment=environment)

    assert result.returncode == 2
    assert "samtools view -H failed: forced header failure" in result.stderr
    assert not values[-1].exists()


def test_post_build_input_mutation_preserves_valid_predecessor(tmp_path):
    values = fixture(tmp_path)
    initial = run(values, "--execute")
    assert initial.returncode == 0, initial.stderr
    predecessor = values[-1].read_bytes()

    environment = {**os.environ, "MUTATE_PATH": str(values[0])}
    result = run(values, "--execute", environment=environment)

    assert result.returncode == 2
    assert "Input changed after validation" in result.stderr
    assert values[-1].read_bytes() == predecessor
    assert values[0].read_bytes().endswith(b"post-build mutation\n")


def test_reference_loader_reuses_exact_owner_without_sys_path_change(
    validator_module,
):
    before_sys_path = list(sys.path)
    cached = sys.modules[validator_module._REFERENCE_CONTIGS_MODULE_NAME]

    assert validator_module._load_reference_contigs() is cached
    assert Path(cached.__file__).resolve() == Path(
        validator_module._REFERENCE_CONTIGS_MODULE_PATH
    ).resolve()
    assert sys.path == before_sys_path


def test_reference_loader_missing_owner_removes_owned_partial(
    tmp_path, monkeypatch, capsys, validator_module
):
    name = validator_module._REFERENCE_CONTIGS_MODULE_NAME
    missing = tmp_path / "missing_reference_contigs.py"
    invocation_cwd = tmp_path / "invocation"
    invocation_cwd.mkdir()
    report_path = tmp_path / "report.tsv"
    before_sys_path = list(sys.path)
    monkeypatch.delitem(sys.modules, name, raising=False)
    monkeypatch.setattr(validator_module, "_REFERENCE_CONTIGS_MODULE_PATH", missing)
    monkeypatch.chdir(invocation_cwd)

    with pytest.raises(SystemExit) as caught:
        validator_module._load_reference_contigs_or_exit()

    assert caught.value.code == 2
    assert name not in sys.modules
    assert capsys.readouterr().err.startswith(
        f"ERROR: unable to load NORAD reference-contig owner at {missing}: "
        "FileNotFoundError:"
    )
    assert_loader_fault_is_residue_free(
        before_sys_path=before_sys_path,
        invocation_cwd=invocation_cwd,
        report_path=report_path,
    )


def test_reference_loader_rejects_foreign_cache_without_replacing_it(
    tmp_path, monkeypatch, capsys, validator_module
):
    name = validator_module._REFERENCE_CONTIGS_MODULE_NAME
    foreign = ModuleType(name)
    foreign.__file__ = str(tmp_path / "foreign_reference_contigs.py")
    invocation_cwd = tmp_path / "invocation"
    invocation_cwd.mkdir()
    report_path = tmp_path / "report.tsv"
    before_sys_path = list(sys.path)
    monkeypatch.setitem(sys.modules, name, foreign)
    monkeypatch.chdir(invocation_cwd)

    with pytest.raises(SystemExit) as caught:
        validator_module._load_reference_contigs_or_exit()

    assert caught.value.code == 2
    assert sys.modules[name] is foreign
    assert "ImportError: cached reference-contig owner resolves to" in (
        capsys.readouterr().err
    )
    assert_loader_fault_is_residue_free(
        before_sys_path=before_sys_path,
        invocation_cwd=invocation_cwd,
        report_path=report_path,
    )


def test_reference_loader_rejects_correct_path_incomplete_api_in_place(
    tmp_path, monkeypatch, capsys, validator_module
):
    name = validator_module._REFERENCE_CONTIGS_MODULE_NAME
    incomplete = ModuleType(name)
    incomplete.__file__ = str(validator_module._REFERENCE_CONTIGS_MODULE_PATH)
    incomplete._NORAD_REFERENCE_CONTIGS_READY = True
    incomplete.ReferenceContigError = RuntimeError
    incomplete.parse_fasta = lambda path: path
    incomplete.parse_fai = lambda path: path
    incomplete.parse_dict = None
    invocation_cwd = tmp_path / "invocation"
    invocation_cwd.mkdir()
    report_path = tmp_path / "report.tsv"
    before_sys_path = list(sys.path)
    monkeypatch.setitem(sys.modules, name, incomplete)
    monkeypatch.chdir(invocation_cwd)

    with pytest.raises(SystemExit) as caught:
        validator_module._load_reference_contigs_or_exit()

    assert caught.value.code == 2
    assert sys.modules[name] is incomplete
    assert "ImportError: cached reference-contig owner has invalid parse_dict" in (
        capsys.readouterr().err
    )
    assert_loader_fault_is_residue_free(
        before_sys_path=before_sys_path,
        invocation_cwd=invocation_cwd,
        report_path=report_path,
    )


def test_reference_loader_execution_failure_removes_only_owned_partial(
    tmp_path, monkeypatch, capsys, validator_module
):
    name = validator_module._REFERENCE_CONTIGS_MODULE_NAME
    failing_owner = tmp_path / "failing_reference_contigs.py"
    failing_owner.write_text(
        "raise RuntimeError('injected reference-contig execution failure')\n",
        encoding="utf-8",
    )
    invocation_cwd = tmp_path / "invocation"
    invocation_cwd.mkdir()
    report_path = tmp_path / "report.tsv"
    before_sys_path = list(sys.path)
    monkeypatch.delitem(sys.modules, name, raising=False)
    monkeypatch.setattr(
        validator_module, "_REFERENCE_CONTIGS_MODULE_PATH", failing_owner
    )
    monkeypatch.chdir(invocation_cwd)

    with pytest.raises(SystemExit) as caught:
        validator_module._load_reference_contigs_or_exit()

    assert caught.value.code == 2
    assert name not in sys.modules
    assert (
        "RuntimeError: injected reference-contig execution failure"
        in capsys.readouterr().err
    )
    assert_loader_fault_is_residue_free(
        before_sys_path=before_sys_path,
        invocation_cwd=invocation_cwd,
        report_path=report_path,
    )
