from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATE_SLURM = REPO_ROOT / "scripts" / "slurm" / "validate.slurm"

def test_step_00a_validates_star_index() -> None:
    source = VALIDATE_SLURM.read_text(encoding="utf-8")

    assert "00a)" in source
    assert "validate star-index" in source
    assert "--scope-id novogene_ref" in source
    assert "--output results/qc/validation/00a/novogene_ref.validation.tsv" in source

def test_step_00b_validates_canonical_bed() -> None:
    source = VALIDATE_SLURM.read_text(encoding="utf-8")

    assert "--bed12 refs/novogene_ref/genome.bed" in source
    assert "refs/novogene_ref/genome.unsorted.bed" not in source

def test_step_00c_validates_reference_sidecars() -> None:
    source = VALIDATE_SLURM.read_text(encoding="utf-8")

    assert "00c)" in source
    assert "mkdir -p results/qc/validation/00c" in source
    assert "validate fasta-sidecars" in source
    assert "--scope-id novogene_ref" in source
    assert "--reference-fasta refs/novogene_ref/genome.fa" in source
    assert "--reference-fai refs/novogene_ref/genome.fa.fai" in source
    assert "--reference-dict refs/novogene_ref/genome.dict" in source
    assert "--output results/qc/validation/00c/novogene_ref.validation.tsv" in source

def test_step_01_validates_star_alignment() -> None:
    source = VALIDATE_SLURM.read_text(encoding="utf-8")

    assert "01)" in source
    assert "validate star-alignment" in source
    assert 'scope_id="${2:-}"' in source
    assert '[[ -n "$scope_id" ]]' in source
    assert '--scope-id "$scope_id"' in source
    assert '--bam "results/star/$scope_id/$scope_id.Aligned.sortedByCoord.out.bam"' in source
    assert '--log-final "results/star/$scope_id/$scope_id.Log.final.out"' in source
    assert '--log-out "results/star/$scope_id/$scope_id.Log.out"' in source
    assert '--log-progress "results/star/$scope_id/$scope_id.Log.progress.out"' in source
    assert '--sj-out "results/star/$scope_id/$scope_id.SJ.out.tab"' in source
    assert '--output "results/qc/validation/01/$scope_id.validation.tsv"' in source
