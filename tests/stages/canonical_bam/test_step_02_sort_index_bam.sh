#!/usr/bin/env bash
# Native scientific behavior only; task-runner tests own publication and recovery.
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
SCRIPT="$repo_root/src/emrys/stages/canonical_bam/step_02_sort_index_bam.sh"
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

printf 'samtools invoked\\n' >> "$samtools_log"
printf '%s\\n' "\$@" >> "$samtools_log"

write_fake_bam() {
    local path="\$1"
    local rg_mode="\${FAKE_RG_MODE:-valid}"
    local tagged_mode="\${FAKE_TAGGED_MODE:-all}"
    local sort_mode="\${FAKE_SORT_MODE:-coordinate}"
    local sample="\${FAKE_SAMPLE_ID:-sample_execute}"
    local total="\${FAKE_TOTAL_RECORDS:-10}"
    local tagged="\$total"

    if [[ "\$tagged_mode" == "partial" ]]; then
        tagged=5
    fi

    {
        # The wrapper validates @HD SO:coordinate and exactly one strict @RG.
        case "\$sort_mode" in
            coordinate) printf '@HD\\tVN:1.6\\tSO:coordinate\\n' ;;
            unknown) printf '@HD\\tVN:1.6\\tSO:unknown\\n' ;;
        esac

        case "\$rg_mode" in
            valid)
                printf '@RG\\tID:%s\\tSM:%s\\tLB:%s\\tPL:ILLUMINA\\n' "\$sample" "\$sample" "\$sample"
                ;;
            missing)
                ;;
            extra)
                printf '@RG\\tID:%s\\tSM:%s\\tLB:%s\\tPL:ILLUMINA\\n' "\$sample" "\$sample" "\$sample"
                printf '@RG\\tID:extra\\tSM:extra\\tLB:extra\\tPL:ILLUMINA\\n'
                ;;
            malformed)
                printf '@RG\\tID:%s\\tSM:WRONG\\tLB:%s\\tPL:ILLUMINA\\n' "\$sample" "\$sample"
                ;;
        esac

        # TOTAL/TAGGED lines let fake "samtools view -c" behave predictably.
        printf 'TOTAL:%s\\n' "\$total"
        printf 'TAGGED:%s\\n' "\$tagged"
    } > "\$path"
}

subcommand="\${1:-}"
shift || true

case "\$subcommand" in
    sort)
        output_bam=""
        input_alignment=""
        while [[ \$# -gt 0 ]]; do
            case "\$1" in
                -o)
                    output_bam="\${2:-}"
                    shift 2
                    ;;
                -@)
                    shift 2
                    ;;
                *)
                    input_alignment="\$1"
                    shift
                    ;;
            esac
        done

        [[ -n "\$output_bam" ]] || { printf 'fake samtools sort missing -o output\\n' >&2; exit 64; }
        printf 'fake sorted bam\\n' > "\$output_bam"
        ;;
    addreplacerg)
        output_bam=""
        input_bam=""
        saw_w=false
        saw_id=false
        saw_sm=false
        saw_lb=false
        saw_pl=false

        while [[ \$# -gt 0 ]]; do
            case "\$1" in
                -o)
                    output_bam="\${2:-}"
                    shift 2
                    ;;
                -@|-m)
                    shift 2
                    ;;
                -w)
                    saw_w=true
                    shift
                    ;;
                -r)
                    case "\${2:-}" in
                        ID:*) saw_id=true ;;
                        SM:*) saw_sm=true ;;
                        LB:*) saw_lb=true ;;
                        PL:ILLUMINA) saw_pl=true ;;
                    esac
                    shift 2
                    ;;
                *)
                    input_bam="\$1"
                    shift
                    ;;
            esac
        done

        # Enforce the production contract: repeated -r arguments plus -w.
        [[ "\$saw_w" == true ]] || { printf 'fake samtools addreplacerg missing -w\\n' >&2; exit 64; }
        [[ "\$saw_id" == true && "\$saw_sm" == true && "\$saw_lb" == true && "\$saw_pl" == true ]] || {
            printf 'fake samtools addreplacerg missing repeated -r RG fields\\n' >&2
            exit 64
        }
        [[ -n "\$output_bam" && -n "\$input_bam" ]] || { printf 'fake samtools addreplacerg missing input/output\\n' >&2; exit 64; }
        write_fake_bam "\$output_bam"
        ;;
    quickcheck)
        input_bam="\${1:-}"
        [[ -n "\$input_bam" ]] || { printf 'fake samtools quickcheck missing input BAM\\n' >&2; exit 64; }
        [[ -s "\$input_bam" ]] || exit 1
        if [[ -n "\${FAKE_QUICKCHECK_FAIL_MATCH:-}" && "\$input_bam" == *"\$FAKE_QUICKCHECK_FAIL_MATCH"* ]]; then
            exit 1
        fi
        ;;
    view)
        if [[ "\${1:-}" == "-H" ]]; then
            input_bam="\${2:-}"
            grep '^@' "\$input_bam"
        elif [[ "\${1:-}" == "-c" && "\${2:-}" == "-d" ]]; then
            input_bam="\${4:-}"
            grep '^TAGGED:' "\$input_bam" | cut -d: -f2
        elif [[ "\${1:-}" == "-c" ]]; then
            input_bam="\${2:-}"
            grep '^TOTAL:' "\$input_bam" | cut -d: -f2
        else
            printf 'fake samtools unsupported view args\\n' >&2
            exit 64
        fi
        ;;
    index)
        input_bam="\${1:-}"
        [[ -n "\$input_bam" ]] || { printf 'fake samtools index missing input BAM\\n' >&2; exit 64; }
        printf 'fake bam index\\n' > "\$input_bam.bai"
        ;;
    *)
        printf 'fake samtools unknown subcommand: %s\\n' "\$subcommand" >&2
        exit 64
        ;;
esac
EOF_SAMTOOLS
chmod +x "$fake_bin/samtools"

input="$tmp_dir/inputs/alignment.sam"
printf '@HD\tVN:1.6\tSO:unknown\n' >"$input"
export FAKE_SAMPLE_ID=sample
command=(bash "$SCRIPT" --sample-id sample --input-alignment "$input"
    --output-dir "$tmp_dir/staged" --threads 2 --samtools-bin "$fake_bin/samtools")
"${command[@]}"
assert_contains "$tmp_dir/staged/sample.sorted.bam" $'@RG\tID:sample\tSM:sample\tLB:sample\tPL:ILLUMINA'
[[ -s "$tmp_dir/staged/sample.sorted.bam.bai" ]] || fail 'missing BAM index'
# A canonical input reuses bytes without another sort or RG rewrite.
mkdir "$tmp_dir/reused"
cp "$tmp_dir/staged/sample.sorted.bam" "$tmp_dir/inputs/canonical.bam"
: >"$samtools_log"
"${command[@]}" --input-alignment "$tmp_dir/inputs/canonical.bam" --output-dir "$tmp_dir/reused"
[[ "$tmp_dir/reused/sample.sorted.bam" -ef "$tmp_dir/inputs/canonical.bam" ]] || fail 'canonical bytes were rewritten'
if grep -Eq '^(sort|addreplacerg)$' "$samtools_log"; then fail 'canonical input invoked a rewriting command'; fi
# The existing native checks still reject wrong metadata and partial RG tagging.
assert_fails 'missing SM:sample' env FAKE_RG_MODE=malformed "${command[@]}"
assert_fails 'must contain exactly one @RG' env FAKE_RG_MODE=extra "${command[@]}"
assert_fails 'records tagged RG:sample' env FAKE_TAGGED_MODE=partial "${command[@]}"
assert_fails 'not coordinate sorted' env FAKE_SORT_MODE=unknown "${command[@]}"
assert_fails 'requires EMRYS_TASK_WORK_DIR' env -u EMRYS_TASK_WORK_DIR "${command[@]}"
printf 'Native worker checks passed.\n'
