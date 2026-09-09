#!/usr/bin/env bash
# Native scientific behavior only; task-runner tests own publication and recovery.
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
SCRIPT="$repo_root/src/emrys/stages/split_n_cigar/step_05_split_n_cigar_reads.sh"
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
java_log="$tmp_dir/java.log"
cat >"$fake_bin/java" <<EOF_JAVA
#!/usr/bin/env bash
set -euo pipefail

printf 'java invoked\\n' >> "$java_log"
printf '%s\\n' "\$@" >> "$java_log"

major="\${FAKE_JAVA_MAJOR:-17}"
printf 'openjdk version "%s.0.14" 2026-01-01\\n' "\$major" >&2
EOF_JAVA
chmod +x "$fake_bin/java"

gatk_log="$tmp_dir/gatk.log"
cat >"$fake_bin/gatk" <<EOF_GATK
#!/usr/bin/env bash
set -euo pipefail

printf 'gatk invoked\\n' >> "$gatk_log"
printf '%s\\n' "\$@" >> "$gatk_log"
printf 'gatk JAVA_HOME=%s\\n' "\${JAVA_HOME:-<unset>}" >> "$gatk_log"
printf 'gatk java on PATH=%s\\n' "\$(command -v java)" >> "$gatk_log"
java -version >/dev/null 2>&1

java_options=""
while [[ \$# -gt 0 ]]; do
    case "\$1" in
        --java-options)
            java_options="\${2:-}"
            shift 2
            ;;
        *)
            break
            ;;
    esac
done

subcommand="\${1:-}"
shift || true

case "\$subcommand" in
    --version)
        printf '4.6.1.0\\n'
        ;;
    SplitNCigarReads)
        reference=""
        input=""
        output=""
        tmp_dir=""
        while [[ \$# -gt 0 ]]; do
            case "\$1" in
                --tmp-dir)
                    tmp_dir="\${2:-}"
                    mkdir -p "\$tmp_dir"
                    shift 2
                    ;;
                -R)
                    reference="\${2:-}"
                    shift 2
                    ;;
                -I)
                    input="\${2:-}"
                    shift 2
                    ;;
                -O)
                    output="\${2:-}"
                    shift 2
                    ;;
                *)
                    printf 'fake gatk unknown argument: %s\\n' "\$1" >&2
                    exit 64
                    ;;
            esac
        done
        if [[ "\${FAKE_GATK_FAIL:-0}" == "1" ]]; then
            printf 'fake gatk forced failure\\n' >&2
            exit 65
        fi
        if [[ -z "\$reference" || -z "\$input" || -z "\$output" ]]; then
            printf 'fake gatk missing -R, -I, or -O\\n' >&2
            exit 64
        fi
        if [[ -z "\$tmp_dir" ]]; then
            printf 'fake gatk missing --tmp-dir\\n' >&2
            exit 64
        fi
        if [[ "\$java_options" != -Djava.io.tmpdir=* ]]; then
            printf 'fake gatk missing java.io.tmpdir option\\n' >&2
            exit 64
        fi
        if [[ "\${TMPDIR:-}" != "\$tmp_dir" ]]; then
            printf 'fake gatk TMPDIR did not match --tmp-dir\\n' >&2
            exit 64
        fi
        {
            printf '@HD\\tVN:1.6\\tSO:%s\\n' "\${FAKE_SORT_ORDER:-coordinate}"
            printf '@RG\\tID:%s\\tSM:%s\\tLB:%s\\tPL:ILLUMINA\\n' "\${FAKE_SAMPLE_ID:-sample_execute}" "\${FAKE_SAMPLE_ID:-sample_execute}" "\${FAKE_SAMPLE_ID:-sample_execute}"
            printf 'TOTAL:10\\n'
            printf 'TAGGED:10\\n'
            printf 'fake split-n-cigar bam from %s with %s\\n' "\$input" "\$reference"
        } > "\$output"
        ;;
    *)
        printf 'fake gatk unknown subcommand: %s\\n' "\$subcommand" >&2
        exit 64
        ;;
esac
EOF_GATK
chmod +x "$fake_bin/gatk"

samtools_log="$tmp_dir/samtools.log"
cat >"$fake_bin/samtools" <<EOF_SAMTOOLS
#!/usr/bin/env bash
set -euo pipefail

printf 'samtools invoked\\n' >> "$samtools_log"
printf '%s\\n' "\$@" >> "$samtools_log"

subcommand="\${1:-}"
shift || true

case "\$subcommand" in
    --version)
        printf 'samtools 1.19.2\\n'
        ;;
    index)
        input_bam="\${1:-}"
        [[ -n "\$input_bam" ]] || { printf 'fake samtools index missing BAM\\n' >&2; exit 64; }
        if [[ "\${FAKE_INDEX_EMPTY:-0}" == "1" ]]; then
            : > "\$input_bam.bai"
        else
            printf 'fake bam index\\n' > "\$input_bam.bai"
        fi
        ;;
    quickcheck)
        input_bam="\${1:-}"
        [[ -n "\$input_bam" ]] || { printf 'fake samtools quickcheck missing BAM\\n' >&2; exit 64; }
        if [[ "\${FAKE_QUICKCHECK_FAIL:-0}" == "1" ]]; then
            printf 'fake quickcheck forced failure\\n' >&2
            exit 66
        fi
        [[ -s "\$input_bam" ]]
        ;;
    view)
        if [[ "\${1:-}" == "-H" ]]; then
            input_bam="\${2:-}"
            grep -E '^@(HD|RG)' "\$input_bam"
        elif [[ "\${1:-}" == "-c" && "\${2:-}" == "-d" ]]; then
            tag="\${3:-}"
            input_bam="\${4:-}"
            expected_sample="\${tag#RG:}"
            header_sample="\$(grep '^@RG' "\$input_bam" | head -n 1 | sed -n 's/.*ID:\\([^[:space:]]*\\).*/\\1/p')"
            if [[ "\$header_sample" == "\$expected_sample" ]]; then
                grep '^TAGGED:' "\$input_bam" | head -n 1 | cut -d: -f2
            else
                printf '0\\n'
            fi
        elif [[ "\${1:-}" == "-c" ]]; then
            input_bam="\${2:-}"
            grep '^TOTAL:' "\$input_bam" | head -n 1 | cut -d: -f2
        else
            printf 'fake samtools view unsupported arguments\\n' >&2
            exit 64
        fi
        ;;
    *)
        printf 'fake samtools unknown subcommand: %s\\n' "\$subcommand" >&2
        exit 64
        ;;
esac
EOF_SAMTOOLS
chmod +x "$fake_bin/samtools"

write_reference() {
    local fasta="$1"

    mkdir -p "$(dirname "$fasta")"
    {
        printf '>chrA\n'
        printf 'ACGTAC\n'
        printf '>chrB\n'
        printf 'TTAA\n'
    } >"$fasta"
    printf 'chrA\t6\t0\t0\t0\nchrB\t4\t0\t0\t0\n' >"$fasta.fai"
    {
        printf '@HD\tVN:1.6\n'
        printf '@SQ\tSN:chrA\tLN:6\n'
        printf '@SQ\tSN:chrB\tLN:4\n'
    } >"$(dirname "$fasta")/$(basename "${fasta%.*}").dict"
}
write_input_bam_pair() {
    local bam="$1"

    mkdir -p "$(dirname "$bam")"
    printf 'fake step04 markdup bam\n' >"$bam"
    printf 'fake step04 markdup bai\n' >"$bam.bai"
}
input_bam="$tmp_dir/inputs/sample.bam"
reference_fasta="$tmp_dir/inputs/genome.fa"
write_input_bam_pair "$input_bam"
write_reference "$reference_fasta"
export FAKE_SAMPLE_ID=sample
command=(bash "$SCRIPT" --sample-id sample --input-bam "$input_bam" --reference-fasta "$reference_fasta"
    --output-dir "$tmp_dir/staged" --gatk-bin "$fake_bin/gatk" --samtools-bin "$fake_bin/samtools" --java-bin "$fake_bin/java")
"${command[@]}"
assert_contains "$tmp_dir/staged/sample.split_ncigar.bam" $'@HD\tVN:1.6\tSO:coordinate'
[[ -s "$tmp_dir/staged/sample.split_ncigar.bam.bai" ]] || fail 'missing canonical BAI'
assert_contains "$gatk_log" "-Djava.io.tmpdir=$EMRYS_TASK_WORK_DIR"
assert_contains "$gatk_log" "gatk java on PATH=$(cd "$fake_bin" && pwd -P)/java"
assert_fails 'not coordinate sorted' env FAKE_SORT_ORDER=unknown "${command[@]}"
assert_fails 'Java 17' env FAKE_JAVA_MAJOR=11 "${command[@]}"
assert_fails 'BAI is missing or empty' env FAKE_INDEX_EMPTY=1 "${command[@]}"
assert_fails 'requires EMRYS_TASK_WORK_DIR' env -u EMRYS_TASK_WORK_DIR "${command[@]}"
printf 'Native worker checks passed.\n'
