#!/usr/bin/env bash
# Native scientific behavior only; task-runner tests own publication and recovery.
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
SCRIPT="$repo_root/src/emrys/stages/fasta_sidecars/step_00c_prepare_gatk_reference.sh"
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

subcommand="\${1:-}"
shift || true

case "\$subcommand" in
    --version)
        printf '4.6.1.0\\n'
        ;;
    CreateSequenceDictionary)
        fasta=""
        output=""
        while [[ \$# -gt 0 ]]; do
            case "\$1" in
                -R)
                    fasta="\${2:-}"
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
        if [[ -z "\$fasta" || -z "\$output" ]]; then
            printf 'fake gatk missing -R or -O\\n' >&2
            exit 64
        fi
        {
            printf '@HD\\tVN:1.6\\n'
            awk '
                /^>/ {
                    if (name != "") {
                        print "@SQ\tSN:" name "\tLN:" length_sum
                    }
                    name = substr(\$0, 2)
                    sub(/[[:space:]].*/, "", name)
                    length_sum = 0
                    next
                }
                {
                    gsub(/[[:space:]]/, "")
                    length_sum += length(\$0)
                }
                END {
                    if (name != "") {
                        print "@SQ\tSN:" name "\tLN:" length_sum
                    }
                }
            ' "\$fasta"
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
    faidx)
        fasta="\${1:-}"
        if [[ -z "\$fasta" ]]; then
            printf 'fake samtools faidx expected FASTA\\n' >&2
            exit 64
        fi
        output="\$fasta.fai"
        awk '
            /^>/ {
                if (name != "") {
                    print name "\t" length_sum "\t0\t0\t0"
                }
                name = substr(\$0, 2)
                sub(/[[:space:]].*/, "", name)
                length_sum = 0
                next
            }
            {
                gsub(/[[:space:]]/, "")
                length_sum += length(\$0)
            }
            END {
                if (name != "") {
                    print name "\t" length_sum "\t0\t0\t0"
                }
            }
        ' "\$fasta" > "\$output"
        ;;
    *)
        printf 'fake samtools unknown subcommand: %s\\n' "\$subcommand" >&2
        exit 64
        ;;
esac
EOF_SAMTOOLS
chmod +x "$fake_bin/samtools"

write_fasta() {
    local fasta="$1"

    mkdir -p "$(dirname "$fasta")"
    {
        printf '>chrA\n'
        printf 'ACGTAC\n'
        printf '>chrB description\n'
        printf 'TTAA\n'
    } >"$fasta"
}
reference_fasta="$tmp_dir/inputs/genome.fa"
write_fasta "$reference_fasta"
command=(bash "$SCRIPT" --reference-fasta "$reference_fasta"
    --reference-fai-output "$tmp_dir/staged/genome.fa.fai"
    --reference-dict-output "$tmp_dir/staged/genome.dict"
    --samtools-bin "$fake_bin/samtools" --gatk-bin "$fake_bin/gatk" --java-bin "$fake_bin/java")
"${command[@]}"
assert_contains "$tmp_dir/staged/genome.fa.fai" $'chrA\t6'
assert_contains "$tmp_dir/staged/genome.dict" $'@SQ\tSN:chrB\tLN:4'
[[ ! -e "$reference_fasta.fai" && ! -e "$tmp_dir/inputs/genome.dict" ]] || fail "worker wrote final sidecars"
assert_contains "$gatk_log" "gatk java on PATH=$(cd "$fake_bin" && pwd -P)/java"
assert_fails "Java 17" env FAKE_JAVA_MAJOR=11 "${command[@]}"
assert_fails 'requires EMRYS_TASK_WORK_DIR' env -u EMRYS_TASK_WORK_DIR "${command[@]}"
printf 'Native worker checks passed.\n'
