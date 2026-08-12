from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATE_SLURM = REPO_ROOT / "scripts" / "slurm" / "validate.slurm"


def test_step_00b_validates_canonical_bed() -> None:
    source = VALIDATE_SLURM.read_text(encoding="utf-8")

    assert "--bed12 refs/novogene_ref/genome.bed" in source
    assert "refs/novogene_ref/genome.unsorted.bed" not in source
