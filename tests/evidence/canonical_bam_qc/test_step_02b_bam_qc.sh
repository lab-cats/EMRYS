#!/usr/bin/env bash
# Native scientific behavior only; task-runner tests own publication and recovery.
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
SCRIPT="$repo_root/src/emrys/evidence/canonical_bam_qc/step_02b_bam_qc.sh"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT
fake_bin="$tmp_dir/bin"
mkdir -p "$fake_bin" "$tmp_dir/inputs" "$tmp_dir/staged" "$tmp_dir/work"
export EMRYS_SHA256_PYTHON="$repo_root/.venv/bin/python"
export EMRYS_TASK_WORK_DIR="$tmp_dir/work" TMPDIR="$tmp_dir/work"
export PATH="$fake_bin:$PATH"
fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }
assert_contains() { grep -Fq -- "$2" "$1" || fail "missing $2 in $1: $(cat "$1")"; }
assert_fails() {
    local pattern="$1"; shift
    if "$@" >"$tmp_dir/failure.out" 2>&1; then fail "unexpected success: $*"; fi
    assert_contains "$tmp_dir/failure.out" "$pattern"
}
samtools_log="$tmp_dir/samtools.log"
cat >"$fake_bin/samtools" <<EOF_SAMTOOLS
#!/usr/bin/env bash
set -euo pipefail

printf 'samtools invoked\n' >> "$samtools_log"
printf '%s\n' "\$@" >> "$samtools_log"

subcommand="\${1:-}"
shift || true

case "\$subcommand" in
    quickcheck)
        mode="\${FAKE_QUICKCHECK_MODE:-empty_success}"
        case "\$mode" in
            empty_success)
                exit 0
                ;;
            output_success)
                printf 'quickcheck success output\\n'
                exit 0
                ;;
            fail)
                printf 'quickcheck failure output\\n' >&2
                exit 42
                ;;
            *)
                printf 'unknown FAKE_QUICKCHECK_MODE: %s\\n' "\$mode" >&2
                exit 64
                ;;
        esac
        ;;
    flagstat)
        mode="\${FAKE_FLAGSTAT_MODE:-success}"
        case "\$mode" in
            success)
                printf '10 + 0 in total (QC-passed reads + QC-failed reads)\\n'
                printf '8 + 0 mapped (80.00%% : N/A)\\n'
                ;;
            partial_fail)
                printf 'partial flagstat output\\n'
                printf 'flagstat failure diagnostic\\n' >&2
                exit 43
                ;;
            *)
                printf 'unknown FAKE_FLAGSTAT_MODE: %s\\n' "\$mode" >&2
                exit 64
                ;;
        esac
        ;;
    *)
        printf 'fake samtools unknown subcommand: %s\\n' "\$subcommand" >&2
        exit 64
        ;;
esac
EOF_SAMTOOLS
chmod +x "$fake_bin/samtools"

bam="$tmp_dir/inputs/sample.bam"
printf 'BAM\n' >"$bam"
printf 'BAI\n' >"${bam%.bam}.bai"
command=(bash "$SCRIPT" --sample-id sample --bam "$bam" --output-dir "$tmp_dir/staged" --samtools-bin "$fake_bin/samtools")
"${command[@]}"
assert_contains "$tmp_dir/staged/sample.quickcheck.txt" 'PASS: samtools quickcheck completed with no errors.'
assert_contains "$tmp_dir/staged/sample.flagstat.txt" '8 + 0 mapped'
FAKE_QUICKCHECK_MODE=output_success "${command[@]}"
assert_contains "$tmp_dir/staged/sample.quickcheck.txt" 'quickcheck success output'
assert_fails 'samtools quickcheck failed' env FAKE_QUICKCHECK_MODE=fail "${command[@]}"
assert_contains "$tmp_dir/staged/sample.quickcheck.txt" 'quickcheck failure output'
assert_fails 'flagstat failure diagnostic' env FAKE_FLAGSTAT_MODE=partial_fail "${command[@]}"
assert_fails 'requires EMRYS_TASK_WORK_DIR' env -u EMRYS_TASK_WORK_DIR "${command[@]}"
printf 'Native worker checks passed.\n'
