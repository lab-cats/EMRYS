import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
MAKEFILE = REPO_ROOT / "Makefile"


def test_make_setup_creates_repository_runtime_directories(tmp_path: Path) -> None:
    result = subprocess.run(
        ["make", "-f", str(MAKEFILE), "setup"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )

    expected_dirs = [
        "logs",
        "results/qc/validation/00a",
        "results/qc/validation/00b",
        "results/qc/validation/00c",
        *(f"results/qc/validation/{step:02d}" for step in range(1, 10)),
    ]

    assert result.returncode == 0, result.stderr

    for relative_path in expected_dirs:
        assert (tmp_path / relative_path).is_dir()