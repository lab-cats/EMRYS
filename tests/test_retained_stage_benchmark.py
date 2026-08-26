"""Fast contract tests for the retained Step 07/08 benchmark helper."""

from __future__ import annotations

import argparse
import contextlib
import csv
import hashlib
import importlib.util
import io
import json
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from types import ModuleType
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tests/tools/retained_stage_benchmark.py"


def _load_script() -> ModuleType:
    spec = importlib.util.spec_from_file_location("retained_stage_benchmark", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


BENCHMARK = _load_script()


def _artifact(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {
        "path": str(path),
        "size_bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


class RetainedStageBenchmarkTests(unittest.TestCase):
    def test_manifest_is_one_paired_v2_plan_over_exact_cases(self) -> None:
        document = BENCHMARK._manifest(
            Path("/locked/python"),
            Path("/repo/tests/tools/retained_stage_benchmark.py"),
            Path("/external/context.json"),
        )

        self.assertEqual(document["schema_version"], "emrys.resource-benchmark.v2")
        cases = document["cases"]
        self.assertEqual(
            {case["name"]: case["values"] for case in cases},
            {case.name: list(case.values) for case in BENCHMARK.RETAINED_CASES},
        )
        for case in cases:
            self.assertEqual(case["repetitions"], BENCHMARK.MEASURED_REPETITIONS)
            self.assertEqual(
                case["warmup_repetitions"], BENCHMARK.WARMUP_REPETITIONS
            )
            self.assertEqual(case["baseline_variant"], "master")
            self.assertEqual(
                [variant["name"] for variant in case["variants"]],
                ["master", "head"],
            )
            self.assertEqual(case["artifact_paths"], ["{trial_dir}/parity.bin"])
            prefix = [
                "/locked/python",
                "-X",
                "pycache_prefix=/dev/null",
                "/repo/tests/tools/retained_stage_benchmark.py",
            ]
            self.assertEqual(case["setup_argv"][:5], [*prefix, "_setup"])
            self.assertEqual(case["validator_argv"][:5], [*prefix, "_validate"])
            for variant in case["variants"]:
                self.assertEqual(variant["producer_argv"][:5], [*prefix, "_produce"])

    def test_case_selection_is_closed_deduplicated_and_canonical(self) -> None:
        default = BENCHMARK._select_cases(suite=None, names=None)
        self.assertEqual(default, BENCHMARK.RETAINED_CASES)
        self.assertEqual(
            BENCHMARK._select_cases(
                suite=None, names=("step08-uniform", "step07-partitions")
            ),
            (BENCHMARK.RETAINED_CASES[0], BENCHMARK.RETAINED_CASES[3]),
        )
        with self.assertRaisesRegex(BENCHMARK.BenchmarkSetupError, "selected once"):
            BENCHMARK._select_cases(
                suite=None, names=("step08-uniform", "step08-uniform")
            )
        with self.assertRaisesRegex(BENCHMARK.BenchmarkSetupError, "mutually exclusive"):
            BENCHMARK._select_cases(
                suite="cohort-stages", names=("step08-uniform",)
            )

    def test_partition_sweeps_cover_the_full_5mb_contig_once(self) -> None:
        for count in (1, 5, 25):
            rows = BENCHMARK._partition_rows(count, "synthetic", 5_000_000)
            self.assertEqual(len(rows), count)
            previous_end = 0
            for index, (partition, selector_type, selector) in enumerate(rows, 1):
                self.assertEqual(partition, f"p{index:02d}")
                self.assertEqual(selector_type, "region")
                contig, interval = selector.split(":", 1)
                start, end = map(int, interval.split("-"))
                self.assertEqual(contig, "synthetic")
                self.assertEqual(start, previous_end + 1)
                previous_end = end
            self.assertEqual(previous_end, 5_000_000)

    def test_step08_row_distributions_are_exact_and_scheduler_discriminating(self) -> None:
        self.assertEqual(BENCHMARK._step08_counts("step08-reread", 10_000), (5_000, 5_000))
        self.assertEqual(BENCHMARK._step08_counts("step08-reread", 100_000), (50_000, 50_000))
        uniform = BENCHMARK._step08_counts("step08-uniform", 100_000)
        skew = BENCHMARK._step08_counts("step08-skew", 100_000)
        self.assertEqual(uniform, (6_250,) * 16)
        self.assertEqual(sum(skew), 100_000)
        self.assertEqual(skew[::2], (12_000,) * 8)
        self.assertEqual(skew[1::2], (500,) * 8)
        self.assertEqual(BENCHMARK._case_threads("step08-reread"), 1)
        self.assertEqual(BENCHMARK._case_threads("step08-skew"), 2)

    def test_step07_normalization_is_narrow(self) -> None:
        trial = Path("/trials/round/master")
        source = (
            b"##fileformat=VCFv4.2\n"
            b"##bcftoolsVersion=1.21\n"
            b"##bcftoolsCommand=mpileup /trials/round/master/input; Date=x\n"
            b"##bcftools_filterVersion=1.21\n"
            b"##bcftools_filterCommand=filter -o /trials/round/master/out; Date=x\n"
            b"##bcftools_viewVersion=must-remain\n"
            b"##bcftools_pluginVersion=must-remain\n"
            b"##otherDate=must-remain\n"
            b"path=/trials/round/master/output.vcf\n"
        )

        normalized = BENCHMARK._normalize_step07(source, trial)

        self.assertNotIn(b"##bcftoolsVersion=", normalized)
        self.assertNotIn(b"##bcftoolsCommand=", normalized)
        self.assertNotIn(b"##bcftools_filterVersion=", normalized)
        self.assertNotIn(b"##bcftools_filterCommand=", normalized)
        self.assertIn(b"##bcftools_viewVersion=must-remain", normalized)
        self.assertIn(b"##bcftools_pluginVersion=must-remain", normalized)
        self.assertIn(b"##otherDate=must-remain", normalized)
        self.assertIn(b"path=<TRIAL_ROOT>/output.vcf", normalized)

    def test_realistic_symbolic_vcf_template_and_writer_preserve_number_r_shape(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            retained = Path(directory) / "retained.vcf"
            output = Path(directory) / "fixture.vcf"
            retained.write_bytes(
                b"##fileformat=VCFv4.2\n"
                b"##ALT=<ID=*,Description=\"Represents allele(s) other than observed.\">\n"
                b"##INFO=<ID=AD,Number=R,Type=Integer,Description=\"Allele depths\">\n"
                b"##FORMAT=<ID=AD,Number=R,Type=Integer,Description=\"Allele depths\">\n"
                b"#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tS\n"
                b"x\t1\told\tA\tC,<*>\t.\tPASS\tAD=7,3,0\tDP:AD\t10:7,3,0\n"
            )

            header, template = BENCHMARK._vcf_template(retained)

            BENCHMARK._write_vcf(output, header, template, "synthetic", "ACGTACGT", 3, 3)

            lines = output.read_text(encoding="ascii").splitlines()
            self.assertIn("##INFO=<ID=AD,Number=R", "\n".join(lines))
            rows = [line for line in lines if not line.startswith("#")]
            fields = [row.split("\t") for row in rows]
            self.assertEqual([row[0] for row in fields], ["synthetic"] * 3)
            self.assertEqual([row[1] for row in fields], ["3", "4", "5"])
            self.assertEqual([row[3] for row in fields], ["G", "T", "A"])
            self.assertEqual([row[4] for row in fields], ["A,<*>", "C,<*>", "G,<*>"])
            self.assertEqual([row[2] for row in fields], ["."] * 3)
            self.assertEqual([row[7] for row in fields], ["AD=7,3,0"] * 3)
            self.assertEqual([row[9] for row in fields], ["10:7,3,0"] * 3)

            single_alt = Path(directory) / "single-alt.vcf"
            single_alt.write_bytes(retained.read_bytes().replace(b"C,<*>", b"C"))
            with self.assertRaisesRegex(BENCHMARK.BenchmarkSetupError, "concrete-SNV"):
                BENCHMARK._vcf_template(single_alt)

    def test_fasta_fixture_rejects_non_acgt_reference_bases(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fasta = Path(directory) / "reference.fa"
            with mock.patch.object(BENCHMARK, "EXPECTED_CONTIG_LENGTH", 4):
                fasta.write_text(">synthetic\nACGN\n", encoding="ascii")
                with self.assertRaisesRegex(BENCHMARK.BenchmarkSetupError, "expected 5Mb contig"):
                    BENCHMARK._fasta(fasta)
                fasta.write_text(">synthetic\nACGT\n", encoding="ascii")
                self.assertEqual(BENCHMARK._fasta(fasta), ("synthetic", "ACGT"))

    def test_step08_fixture_is_shared_across_rounds_and_hash_admitted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            warmup = root / "warmups/step08-skew/100000/rep-01/master"
            measured = root / "trials/step08-skew/100000/rep-03/head"
            warmup.mkdir(parents=True)
            measured.mkdir(parents=True)
            samples = root / "samples.tsv"
            samples.write_text("sample_id\tx\nS\t1\n", encoding="utf-8")
            reference = root / "reference.fa"
            reference.write_text(">synthetic\nA\n", encoding="ascii")
            retained = root / "retained"
            retained.mkdir()
            primary_vcf = retained / "primary.vcf"
            primary_vcf.write_text("template\n", encoding="ascii")
            context = {
                "reference_fasta": str(reference),
                "retained_primary_vcf": str(primary_vcf),
                "sample_manifest": str(samples),
                "cohort_id": "cohort",
                "python": sys.executable,
            }
            header = [b"##fileformat=VCFv4.2\n", b"#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tS\n"]
            template = b"x\t1\t.\tA\tG,<*>\t.\tPASS\tAD=7,3,0\tDP:AD\t10:7,3,0".split(b"\t")

            def tiny_vcf(path: Path, *_arguments: object) -> None:
                path.write_bytes(b"fixture\n")

            with (
                mock.patch.object(BENCHMARK, "_fasta", return_value=("synthetic", "A" * 5_000_000)),
                mock.patch.object(BENCHMARK, "_vcf_template", return_value=(header, template)),
                mock.patch.object(BENCHMARK, "_write_vcf", side_effect=tiny_vcf) as writer,
            ):
                BENCHMARK._setup_step08(context, warmup, "step08-skew", 100_000)
                first_count = writer.call_count
                BENCHMARK._setup_step08(context, measured, "step08-skew", 100_000)
                self.assertEqual(writer.call_count, first_count)

            fixture = root / "fixtures/step08-skew/100000"
            self.assertEqual(first_count, 16)
            self.assertFalse((fixture / ".venv").exists())
            self.assertEqual(len((fixture / "partitions.tsv").read_text().splitlines()), 9)
            marker = json.loads((fixture / "fixture.json").read_text())
            self.assertEqual(marker["schema_version"], BENCHMARK.STEP08_FIXTURE_SCHEMA)
            self.assertEqual(marker["expected_vcf_record_count"], 100_000)
            self.assertEqual(marker["expected_supported_candidate_count"], 100_000)
            self.assertEqual(marker["expected_symbolic_alt_count"], 100_000)
            self.assertEqual(set(marker["members"]), set(BENCHMARK._step08_member_roster("cohort", BENCHMARK._step08_counts("step08-skew", 100_000))))
            receipts = sorted((fixture / "step07/cohort").glob("*/*.step07_outputs.tsv"))
            self.assertEqual(len(receipts), 8)
            declared = []
            for receipt in receipts:
                with receipt.open(encoding="utf-8", newline="") as stream:
                    rows = list(csv.DictReader(stream, dialect="excel-tab"))
                self.assertEqual([row["orientation"] for row in rows], ["FWD_like", "REV_like"])
                self.assertTrue(all(not Path(row["vcf_path"]).is_absolute() for row in rows))
                self.assertTrue(all(row["vcf_path"].startswith("step07/") for row in rows))
                declared.extend(int(row["vcf_record_count"]) for row in rows)
            self.assertEqual(declared, list(BENCHMARK._step08_counts("step08-skew", 100_000)))

            first_vcf = next((fixture / "step07/cohort").glob("*/*.vcf"))
            first_vcf.write_bytes(b"tampered\n")
            with self.assertRaisesRegex(BENCHMARK.BenchmarkSetupError, "member differs"):
                BENCHMARK._setup_step08(context, measured, "step08-skew", 100_000)

    def test_step08_validator_runs_owner_then_all_pass_and_bundles_raw_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            repo = root / "repo"
            repo.mkdir()
            trial = root / "benchmark-results/trials/step08-reread/10000/rep-01/master"
            fixture = root / "benchmark-results/fixtures/step08-reread/10000"
            trial.mkdir(parents=True)
            fixture.mkdir(parents=True)
            (fixture / "partitions.tsv").write_text("partition_id\tselector_type\tselector_value\np01\tregion\ts:1-10\n")
            cohort_root = trial / "output/cohort"
            qc = trial / "qc"
            cohort_root.mkdir(parents=True)
            qc.mkdir()
            (cohort_root / "cohort.step08_sites.tsv").write_bytes(b"sites\n")
            (cohort_root / "cohort.step08_inputs.tsv").write_bytes(b"inputs\n")
            (qc / "cohort.step08_summary.tsv").write_bytes(b"summary\n")
            context = {
                "repo_root": str(repo),
                "python": "/locked/python",
                "cohort_id": "cohort",
                "sample_manifest": "/retained/samples.tsv",
                "annotation_gtf": "/retained/genes.gtf",
            }
            calls: list[tuple[str, ...]] = []

            with mock.patch.object(
                BENCHMARK,
                "_run_checked",
                side_effect=lambda argv, **_kwargs: calls.append(tuple(argv)),
            ), mock.patch.object(
                BENCHMARK, "_admit_step08_fixture", return_value=fixture
            ):
                BENCHMARK._validate_step08(
                    context, trial, "step08-reread", 10_000
                )

            self.assertIn("cohort-candidate-preprocessing", calls[0])
            self.assertIn("--execute", calls[0])
            self.assertIn("all-pass", calls[1])
            parity = (trial / "parity.bin").read_bytes()
            self.assertIn(b"sites\n", parity)
            self.assertIn(b"inputs\n", parity)
            self.assertIn(b"summary\n", parity)

    def test_step08_producer_uses_fixture_cwd_and_relative_step07_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            trial = root / "benchmark-results/trials/step08-skew/100000/rep-02/head"
            fixture = root / "benchmark-results/fixtures/step08-skew/100000"
            source = root / "source"
            trial.mkdir(parents=True)
            fixture.mkdir(parents=True)
            source.mkdir()
            captured: dict[str, object] = {}

            def run(argv: object, *, cwd: Path, environment: object) -> None:
                captured.update(argv=tuple(argv), cwd=cwd, environment=environment)

            process_environment = ModuleType("emrys.libraries.process_environment")
            process_environment.guarded_r_environment = (
                lambda *_args, **_kwargs: {"GUARDED": "1"}
            )
            modules = {
                "emrys": ModuleType("emrys"),
                "emrys.libraries": ModuleType("emrys.libraries"),
                "emrys.libraries.process_environment": process_environment,
            }
            context = {
                "renv_library": str(root / "renv"),
                "cohort_id": "cohort",
                "sample_manifest": str(root / "samples.tsv"),
                "annotation_gtf": str(root / "genes.gtf"),
                "rscript": "/runtime/Rscript",
                "python": "/repo/.venv/bin/python",
            }
            with (
                mock.patch.dict(sys.modules, modules),
                mock.patch.object(BENCHMARK, "_run_checked", side_effect=run),
            ):
                BENCHMARK._produce_step08(
                    context, trial, source, "step08-skew", 100_000, 2
                )

            argv = captured["argv"]
            self.assertEqual(captured["cwd"], fixture)
            step07_index = argv.index("--step07-root")
            self.assertEqual(argv[step07_index + 1], "step07")
            self.assertEqual(
                captured["environment"],
                {
                    "GUARDED": "1",
                    "EMRYS_SHA256_PYTHON": "/repo/.venv/bin/python",
                    "EMRYS_REQUIRE_BOUND_SHA256": "1",
                },
            )

    def test_step07_producer_binds_the_absolute_sha256_python(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            repo = root / "repo"
            fixture = root / "trial/fixture"
            source = root / "source"
            runtime = root / "runtime/bin"
            repo.mkdir()
            fixture.mkdir(parents=True)
            source.mkdir()
            runtime.mkdir(parents=True)
            (runtime / "bcftools").write_text("tool")
            (runtime / "bcftools").chmod(0o755)
            (fixture / "partitions.tsv").write_text(
                "partition_id\tselector_type\tselector_value\np01\tregion\ts:1-10\n"
            )
            captured: dict[str, object] = {}

            def run(argv: object, *, cwd: Path, environment: object) -> None:
                captured.update(argv=tuple(argv), cwd=cwd, environment=environment)

            process_environment = ModuleType("emrys.libraries.process_environment")
            process_environment.sanitized_subprocess_environment = (
                lambda _environment: {"SANITIZED": "1"}
            )
            modules = {
                "emrys": ModuleType("emrys"),
                "emrys.libraries": ModuleType("emrys.libraries"),
                "emrys.libraries.process_environment": process_environment,
            }
            context = {
                "repo_root": str(repo),
                "runtime_prefix": str(runtime.parent),
                "python": "/repo/.venv/bin/python",
                "cohort_id": "cohort",
                "sample_manifest": "/retained/samples.tsv",
                "orientation_root": "/retained/orientation",
                "reference_fasta": "/retained/reference.fa",
            }
            with (
                mock.patch.dict(sys.modules, modules),
                mock.patch.object(BENCHMARK, "_run_checked", side_effect=run),
            ):
                BENCHMARK._produce_step07(context, fixture.parent, source)

            self.assertEqual(captured["cwd"], repo)
            self.assertEqual(
                captured["environment"],
                {
                    "SANITIZED": "1",
                    "EMRYS_SHA256_PYTHON": "/repo/.venv/bin/python",
                    "EMRYS_REQUIRE_BOUND_SHA256": "1",
                },
            )

    def test_archive_extractor_rejects_escape_and_links(self) -> None:
        def archive(member: tarfile.TarInfo, data: bytes = b"") -> bytes:
            stream = io.BytesIO()
            with tarfile.open(fileobj=stream, mode="w") as output:
                member.size = len(data)
                output.addfile(member, io.BytesIO(data))
            return stream.getvalue()

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            safe = tarfile.TarInfo("src/example.py")
            BENCHMARK._safe_extract_archive(archive(safe, b"pass\n"), root / "safe")
            self.assertEqual((root / "safe/src/example.py").read_bytes(), b"pass\n")
            with self.assertRaisesRegex(BENCHMARK.BenchmarkSetupError, "unsafe member"):
                BENCHMARK._safe_extract_archive(
                    archive(tarfile.TarInfo("../escape"), b"bad"), root / "escape"
                )
            link = tarfile.TarInfo("link")
            link.type = tarfile.SYMTYPE
            link.linkname = "target"
            with self.assertRaisesRegex(BENCHMARK.BenchmarkSetupError, "unsafe member"):
                BENCHMARK._safe_extract_archive(archive(link), root / "link-root")

    def test_repository_guard_is_clean_ancestral_and_lock_exact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            python = root / ".venv/bin/python"
            python.parent.mkdir(parents=True)
            python.write_text("#!/bin/sh\nexit 0\n")
            python.chmod(0o755)
            baseline = "1" * 40
            head = "2" * 40
            calls: list[tuple[str, ...]] = []

            def git(_root: Path, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
                calls.append(tuple(arguments))
                if arguments[0] == "status":
                    return subprocess.CompletedProcess(arguments, 0, b"", b"")
                if arguments[0] == "rev-parse":
                    value = baseline if arguments[1].startswith("origin/master") else head
                    return subprocess.CompletedProcess(arguments, 0, f"{value}\n".encode(), b"")
                if arguments[0] == "merge-base":
                    return subprocess.CompletedProcess(arguments, 0, b"", b"")
                if arguments[0] == "show":
                    return subprocess.CompletedProcess(arguments, 0, b"same-lock\n", b"")
                raise AssertionError(arguments)

            with mock.patch.object(BENCHMARK, "_git", side_effect=git):
                admitted = BENCHMARK._admit_repository(root)

            self.assertEqual(admitted.baseline_commit, baseline)
            self.assertEqual(admitted.head_commit, head)
            self.assertIn(
                ("status", "--porcelain=v1", "--untracked-files=all"), calls
            )
            show_paths = {call[1].split(":", 1)[1] for call in calls if call[0] == "show"}
            self.assertEqual(
                show_paths,
                {
                    "uv.lock",
                    "renv.lock",
                    ".github/ci/real-tools.conda-lock.yml",
                },
            )

    def test_comparison_summary_requires_exact_complete_four_case_roster(self) -> None:
        manifest = BENCHMARK._manifest(
            Path("/locked/python"),
            Path("/repo/tests/tools/retained_stage_benchmark.py"),
            Path("/external/context.json"),
        )

        def rows() -> list[dict[str, str]]:
            selected = []
            for case in manifest["cases"]:
                for value in case["values"]:
                    for variant in case["variants"]:
                        row = {field: "1" for field in BENCHMARK.COMPARISON_SUMMARY_FIELDS}
                        row.update(
                            {
                                "case": str(case["name"]),
                                "value": str(value),
                                "baseline_variant": str(case["baseline_variant"]),
                                "variant": str(variant["name"]),
                                "required_repetitions": str(case["repetitions"]),
                                "successful_repetitions": str(case["repetitions"]),
                                "paired_repetitions": str(case["repetitions"]),
                                "warmups_valid": "yes",
                                "comparison_valid": "yes",
                                "artifact_parity": "yes",
                            }
                        )
                        selected.append(row)
            return selected

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "summary.tsv"

            def publish(selected: list[dict[str, str]]) -> None:
                with path.open("w", encoding="utf-8", newline="") as stream:
                    writer = csv.DictWriter(
                        stream,
                        fieldnames=BENCHMARK.COMPARISON_SUMMARY_FIELDS,
                        dialect="excel-tab",
                    )
                    writer.writeheader()
                    writer.writerows(selected)

            complete_rows = rows()
            publish(complete_rows)
            self.assertEqual(
                BENCHMARK._comparison_summary_complete(path, manifest),
                (True, "complete"),
            )
            publish(complete_rows[:-1])
            valid, detail = BENCHMARK._comparison_summary_complete(path, manifest)
            self.assertFalse(valid)
            self.assertIn("roster", detail)

            selected_manifest = BENCHMARK._manifest(
                Path("/locked/python"),
                Path("/repo/tests/tools/retained_stage_benchmark.py"),
                Path("/external/context.json"),
                (BENCHMARK.RETAINED_CASES[-1],),
            )
            publish(rows())
            valid, detail = BENCHMARK._comparison_summary_complete(
                path, selected_manifest
            )
            self.assertFalse(valid)
            self.assertIn("roster", detail)

    def test_output_root_must_be_external_to_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory).resolve() / "repo"
            repo.mkdir()
            with self.assertRaisesRegex(BENCHMARK.BenchmarkSetupError, "outside"):
                BENCHMARK._require_external_output(repo / "results/benchmark", repo)
            BENCHMARK._require_external_output(repo.parent / "benchmark", repo)

    def test_execute_context_records_the_exact_retained_primary_vcf(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            repo_root = root / "repo"
            repo_root.mkdir()
            summary = root / "e2e-summary.json"
            summary.write_text("{}\n")
            primary_vcf = root / "retained.primary.FWD_like.mpileup.vcf"
            primary_vcf.write_text("##fileformat=VCFv4.2\n")
            retained = BENCHMARK.AdmittedE2E(
                summary,
                hashlib.sha256(summary.read_bytes()).hexdigest(),
                root / "run",
                "cohort",
                root / "samples.tsv",
                root / "reference.fa",
                root / "genes.gtf",
                root / "orientation",
                primary_vcf,
            )
            repository = BENCHMARK.RepositoryState(
                repo_root,
                Path(sys.executable),
                "1" * 40,
                "2" * 40,
            )
            output = root / "benchmark"

            def extract(_data: bytes, destination: Path) -> None:
                destination.mkdir(parents=True)

            def run(argv: list[str], **_kwargs: object) -> subprocess.CompletedProcess[bytes]:
                results = Path(argv[argv.index("--output") + 1])
                results.mkdir()
                (results / "summary.tsv").write_text("summary\n")
                return subprocess.CompletedProcess(argv, 0, b"", b"")

            with (
                mock.patch.object(
                    BENCHMARK,
                    "_git",
                    return_value=subprocess.CompletedProcess([], 0, b"archive", b""),
                ),
                mock.patch.object(BENCHMARK, "_safe_extract_archive", side_effect=extract),
                mock.patch.object(BENCHMARK, "_comparison_summary_complete", return_value=(True, "complete")),
                mock.patch.object(BENCHMARK.subprocess, "run", side_effect=run),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                self.assertEqual(
                    BENCHMARK._execute(
                        repository,
                        retained,
                        output,
                        root / "runtime",
                        root / "Rscript",
                        root / "renv",
                        (BENCHMARK.RETAINED_CASES[-1],),
                        None,
                    ),
                    0,
                )

            context = json.loads((output / "benchmark-context.json").read_text())
            self.assertEqual(context["retained_primary_vcf"], str(primary_vcf))
            self.assertNotIn("retained_step07_root", context)
            summary_document = json.loads(
                (output / "retained-stage-benchmark-summary.json").read_text()
            )
            self.assertEqual(summary_document["schema_version"], BENCHMARK.SUMMARY_SCHEMA)
            self.assertEqual(
                summary_document["selection"],
                {"suite": None, "cases": {"step08-uniform": [100_000]}},
            )

    def test_admit_e2e_requires_the_exact_retained_100k_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            operator = Path(directory).resolve() / "operator"
            run = operator / "workspace/runs/run-test"
            (run / "contract").mkdir(parents=True)
            (run / "results/orientation").mkdir(parents=True)
            (run / "results/mpileup").mkdir()
            inputs = operator / "synthetic-inputs"
            (inputs / "inputs/reference").mkdir(parents=True)
            samples = inputs / "samples.tsv"
            partitions = inputs / "partitions.tsv"
            fasta = inputs / "inputs/reference/reference.fa"
            gtf = inputs / "inputs/reference/genes.gtf"
            samples.write_text("sample_id\tx\nS\t1\n")
            partitions.write_text("partition_id\tselector_type\tselector_value\nprimary\tregion\ts\n")
            fasta.write_text(">s\nA\n")
            Path(f"{fasta}.fai").write_text("s\t5000000\t0\t1\t2\n")
            gtf.write_text("s\tx\tgene\t1\t1\t.\t+\t.\tgene_id \"g\";\n")
            execution = {
                "analysis": {"cohort_id": "cohort"},
                "samples": {"manifest": {"path": str(samples)}},
                "partitions": {
                    "manifest": {"path": str(partitions)},
                    "rows": [{"partition_id": "primary", "selector_type": "region", "selector_value": "s"}],
                },
                "reference": {"fasta": {"path": str(fasta)}, "gtf": {"path": str(gtf)}},
            }
            (run / "contract/normalized.json").write_text(json.dumps(execution))
            evidence = operator / "evidence"
            evidence.mkdir()
            owners = []
            for index in range(35):
                path = evidence / f"owner-{index}.json"
                path.write_text(str(index))
                owners.append(_artifact(path))
            final = evidence / "attempt.json"
            final.write_text("complete")
            runtime_profile = operator / "runtime.selected.tsv"
            runtime_profile.write_text("tool\tpath\n")
            primary_vcf = run / "results/mpileup/cohort/primary/cohort.primary.FWD_like.mpileup.vcf"
            primary_vcf.parent.mkdir(parents=True)
            primary_vcf.write_text("##fileformat=VCFv4.2\n")
            summary = {
                "schema_version": BENCHMARK.E2E_SCHEMA,
                "status": "passed",
                "profile": "100000",
                "dataset_profile": "production-like-v1",
                "fixture_id": "deterministic-production-like-v1",
                "read_pairs_per_library": 100_000,
                "biological_interpretation_claimed": False,
                "operator_root": str(operator),
                "runtime_profile": _artifact(runtime_profile),
                "completion": {
                    "state": "local_pipeline_complete",
                    "run_id": "run-test",
                    "run_root": str(run),
                    "verified_owner_jobs": 35,
                    "verified_owner_records": owners,
                    "step10_verified": True,
                    "artifacts": {"attempt": _artifact(final)},
                },
            }
            summary_path = operator / "e2e-summary.json"
            summary_path.write_text(json.dumps(summary))

            admitted = BENCHMARK._admit_e2e(summary_path)

            self.assertEqual(admitted.run_root, run)
            self.assertEqual(admitted.cohort_id, "cohort")
            self.assertEqual(admitted.retained_primary_vcf, primary_vcf)
            summary["profile"] = "130"
            summary_path.write_text(json.dumps(summary))
            with self.assertRaisesRegex(BENCHMARK.BenchmarkSetupError, "exact passed retained 100k"):
                BENCHMARK._admit_e2e(summary_path)

    def test_dry_run_default_does_not_create_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            repo = root / "repo"
            repo.mkdir()
            runtime = root / "runtime"
            renv = root / "renv"
            runtime.mkdir()
            renv.mkdir()
            output = root / "absent-output"
            repository = BENCHMARK.RepositoryState(
                repo,
                Path("/locked/python"),
                "1" * 40,
                "2" * 40,
            )
            evidence = mock.Mock()
            arguments = argparse.Namespace(
                repo_root=repo,
                e2e_summary=root / "e2e-summary.json",
                output_root=output,
                runtime_prefix=runtime,
                rscript=root / "Rscript",
                renv_library=renv,
                suite=None,
                case_names=None,
                execute=False,
            )
            with (
                mock.patch.object(BENCHMARK, "_admit_repository", return_value=repository),
                mock.patch.object(BENCHMARK, "_admit_e2e", return_value=evidence),
                mock.patch.object(BENCHMARK, "_real_directory", side_effect=lambda path, _label: Path(path)),
                mock.patch.object(BENCHMARK, "_real_file", side_effect=lambda path, _label, **_kwargs: Path(path)),
            ):
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(BENCHMARK._orchestrate(arguments), 0)
            self.assertFalse(output.exists())

    def test_internal_producer_requires_an_explicit_variant(self) -> None:
        with self.assertRaises(SystemExit):
            with contextlib.redirect_stderr(io.StringIO()):
                BENCHMARK._internal_parser(
                    [
                        "_produce", "--context", "/context", "--case", "step08-reread",
                        "--value", "10000", "--trial-dir", "/trial",
                    ]
                )

    def test_internal_parser_rejects_an_unregistered_case_value(self) -> None:
        with self.assertRaises(SystemExit):
            with contextlib.redirect_stderr(io.StringIO()):
                BENCHMARK._internal_parser(
                    [
                        "_setup", "--context", "/context", "--case",
                        "step08-reread", "--value", "999", "--trial-dir", "/trial",
                    ]
                )


if __name__ == "__main__":
    unittest.main()
