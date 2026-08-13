#!/usr/bin/env bash
# Smoke tests for Step 05 command construction, side-effect-free dry-runs,
# cleanup, and rollback using fake local GATK/samtools/Java executables.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
SCRIPT="$REPO_ROOT/src/norad/stages/split_n_cigar/step_05_split_n_cigar_reads.sh"
JOB="$REPO_ROOT/src/norad/stages/split_n_cigar/step_05_split_n_cigar_reads.slurm"
unset NORAD_RUN_TOKEN
export NORAD_SHA256_PYTHON="$REPO_ROOT/.venv/bin/python"

fail() {
    printf 'FAIL: %s\n' "$*" >&2
    exit 1
}

assert_contains() {
    local file="$1"
    local expected="$2"

    if ! grep -Fq -- "$expected" "$file"; then
        printf 'Expected to find: %s\n' "$expected" >&2
        printf 'Actual output:\n' >&2
        cat "$file" >&2
        fail "missing expected output"
    fi
}

assert_not_contains() {
    local file="$1"
    local unexpected="$2"

    if grep -Fq -- "$unexpected" "$file"; then
        printf 'Unexpectedly found: %s\n' "$unexpected" >&2
        printf 'Actual output:\n' >&2
        cat "$file" >&2
        fail "unexpected output"
    fi
}

assert_not_exists() {
    local path="$1"

    [[ ! -e "$path" ]] || fail "path should not exist: $path"
}

assert_fails() {
    local output_file="$1"
    shift

    if "$@" >"$output_file" 2>&1; then
        cat "$output_file" >&2
        fail "command unexpectedly succeeded: $*"
    fi
}

assert_exits() {
    local expected_status="$1"
    local output_file="$2"
    local status
    shift 2

    set +e
    "$@" >"$output_file" 2>&1
    status=$?
    set -e
    [[ "$status" -eq "$expected_status" ]] || {
        cat "$output_file" >&2
        fail "expected exit $expected_status, got $status: $*"
    }
}

assert_file_equals() {
    local path="$1"
    local expected="$2"

    [[ -f "$path" ]] || fail "file does not exist: $path"
    printf '%s' "$expected" | cmp -s - "$path" ||
        fail "unexpected contents for $path"
}

assert_no_step05_scratch() {
    local dir="$1"

    if [[ ! -d "$dir" ]]; then
        return
    fi

    if find "$dir" -name '*.step05.*' -print | grep -q .; then
        find "$dir" -name '*.step05.*' -print >&2
        fail "Step 05 scratch files remain in $dir"
    fi
}

assert_no_step05_recovery() {
    local dir="$1"

    if [[ ! -d "$dir" ]]; then
        return
    fi

    if find "$dir" -iname '*recovery*' -print | grep -q .; then
        find "$dir" -iname '*recovery*' -print >&2
        fail "Step 05 recovery evidence remains in $dir"
    fi
}

assert_no_step05_attempt_marker() {
    local dir="$1"

    if [[ ! -d "$dir" ]]; then
        return
    fi

    if find "$dir" \( -iname '*receipt*' -o -iname '*recovery*' \) -print | grep -q .; then
        find "$dir" \( -iname '*receipt*' -o -iname '*recovery*' \) -print >&2
        fail "Step 05 receipt or recovery marker remains in $dir"
    fi
}

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

run_step05() {
    local sample="$1"
    local input_bam="$2"
    local reference_fasta="$3"
    local output_dir="$4"
    shift 4

    bash "$SCRIPT" \
        --sample-id "$sample" \
        --input-bam "$input_bam" \
        --reference-fasta "$reference_fasta" \
        --output-dir "$output_dir" \
        --gatk-bin "$fake_bin/gatk" \
        --samtools-bin "$fake_bin/samtools" \
        --java-bin "$fake_bin/java" \
        "$@"
}

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT
export TMPDIR="$tmp_dir"
unset GATK_BIN_OVERRIDE SAMTOOLS_BIN_OVERRIDE JAVA_BIN_OVERRIDE JAVA_HOME \
    SLURM_JOB_ID \
    FAKE_GATK_FAIL FAKE_GATK_TERM_PARENT FAKE_INDEX_EMPTY FAKE_JAVA_MAJOR \
    FAKE_MUTATE_ADMITTED_INPUTS FAKE_MV_FAIL_ONCE_DEST_MATCH \
    FAKE_MV_FAIL_SOURCE_MATCH FAKE_QUICKCHECK_FAIL \
    FAKE_QUICKCHECK_FAIL_FINAL FAKE_SAMPLE_ID FAKE_SORT_ORDER

fake_bin="$tmp_dir/bin"
mkdir -p "$fake_bin"

gatk_log="$tmp_dir/gatk_invocations.log"
samtools_log="$tmp_dir/samtools_invocations.log"
java_log="$tmp_dir/java_invocations.log"

# Fake tools write text BAM stand-ins with just enough header/count metadata for
# the Step 05 validation paths to behave like real samtools/GATK calls.
cat >"$fake_bin/java" <<EOF_JAVA
#!/usr/bin/env bash
set -euo pipefail

printf 'java invoked\\n' >> "$java_log"
printf '%s\\n' "\$@" >> "$java_log"

major="\${FAKE_JAVA_MAJOR:-17}"
printf 'openjdk version "%s.0.14" 2026-01-01\\n' "\$major" >&2
EOF_JAVA
chmod +x "$fake_bin/java"

cat >"$fake_bin/gatk" <<EOF_GATK
#!/usr/bin/env bash
set -euo pipefail

printf 'gatk invoked\\n' >> "$gatk_log"
printf '%s\\n' "\$@" >> "$gatk_log"

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
        if [[ "\${FAKE_GATK_TERM_PARENT:-0}" == "1" ]]; then
            kill -TERM "\$PPID"
            kill -TERM "\$\$"
        fi
        if [[ "\${FAKE_MUTATE_ADMITTED_INPUTS:-0}" == "1" ]]; then
            printf 'mutated input bam\\n' >> "\$input"
            printf 'mutated input bai\\n' >> "\$input.bai"
            printf 'mutated reference fasta\\n' >> "\$reference"
            printf 'mutated reference fai\\n' >> "\$reference.fai"
            printf 'mutated reference dict\\n' >> "\${reference%.*}.dict"
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
        if [[ "\${FAKE_QUICKCHECK_FAIL_FINAL:-0}" == "1" && "\$input_bam" != *.step05.* ]]; then
            printf 'fake final-path quickcheck forced failure\\n' >&2
            exit 69
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

cat >"$fake_bin/mv" <<EOF_MV
#!/usr/bin/env bash
set -euo pipefail

source=""
dest=""
for arg in "\$@"; do
    if [[ -z "\$source" ]]; then
        source="\$arg"
    fi
    dest="\$arg"
done

# Force a single publish failure without breaking rollback's own restore moves.
fail_marker="$tmp_dir/fake_mv_failed_once"
if [[ -n "\${FAKE_MV_FAIL_ONCE_DEST_MATCH:-}" && "\$dest" == *"\$FAKE_MV_FAIL_ONCE_DEST_MATCH"* && ! -e "\$fail_marker" ]]; then
    : > "\$fail_marker"
    printf 'fake mv forced failure for destination: %s\\n' "\$dest" >&2
    exit 67
fi

if [[ -n "\${FAKE_MV_FAIL_SOURCE_MATCH:-}" && "\$source" == *"\$FAKE_MV_FAIL_SOURCE_MATCH" ]]; then
    printf 'fake mv forced restore failure for source: %s\\n' "\$source" >&2
    exit 68
fi

/bin/mv "\$@"
EOF_MV
chmod +x "$fake_bin/mv"

export PATH="$fake_bin:$PATH"

fixture_dir="$tmp_dir/fixtures"
input_bam="$fixture_dir/markdup/ABE_EV_2/ABE_EV_2.markdup.bam"
reference_fasta="$fixture_dir/ref/genome.fa"
write_input_bam_pair "$input_bam"
write_reference "$reference_fasta"

printf 'Running syntax checks...\n'
bash -n "$SCRIPT"
bash -n "$JOB"

printf 'Running help check...\n'
help_output="$tmp_dir/help.out"
bash "$SCRIPT" --help >"$help_output"
assert_contains "$help_output" "Usage:"
assert_contains "$help_output" "--sample-id"
assert_contains "$help_output" "--input-bam"
assert_contains "$help_output" "--reference-fasta"
assert_contains "$help_output" "--output-dir"
assert_contains "$help_output" "--gatk-bin"
assert_contains "$help_output" "--samtools-bin"
assert_contains "$help_output" "--java-bin"
assert_contains "$help_output" "--execute"

printf 'Running missing required argument failure check...\n'
missing_arg_output="$tmp_dir/missing_arg.out"
assert_fails "$missing_arg_output" bash "$SCRIPT" \
    --input-bam "$input_bam" \
    --reference-fasta "$reference_fasta" \
    --output-dir "$tmp_dir/results/missing_arg" \
    --gatk-bin "$fake_bin/gatk" \
    --samtools-bin "$fake_bin/samtools" \
    --java-bin "$fake_bin/java"
assert_contains "$missing_arg_output" "Missing required argument: --sample-id"

printf 'Running missing input BAM failure check...\n'
missing_bam_output="$tmp_dir/missing_bam.out"
assert_fails "$missing_bam_output" run_step05 ABE_EV_2 "$fixture_dir/missing.markdup.bam" "$reference_fasta" "$tmp_dir/results/missing_bam"
assert_contains "$missing_bam_output" "Input BAM does not exist or is empty"

printf 'Running missing input BAI failure check...\n'
missing_bai_bam="$fixture_dir/markdup/missing_bai/ABE_EV_2.markdup.bam"
mkdir -p "$(dirname "$missing_bai_bam")"
printf 'fake bam\n' >"$missing_bai_bam"
missing_bai_output="$tmp_dir/missing_bai.out"
assert_fails "$missing_bai_output" run_step05 ABE_EV_2 "$missing_bai_bam" "$reference_fasta" "$tmp_dir/results/missing_bai"
assert_contains "$missing_bai_output" "Input BAI does not exist or is empty"

printf 'Running missing reference FASTA failure check...\n'
missing_ref_output="$tmp_dir/missing_ref.out"
assert_fails "$missing_ref_output" run_step05 ABE_EV_2 "$input_bam" "$fixture_dir/ref/missing.fa" "$tmp_dir/results/missing_ref"
assert_contains "$missing_ref_output" "Reference FASTA does not exist or is empty"

printf 'Running missing FAI failure check...\n'
missing_fai_dir="$tmp_dir/missing_fai"
missing_fai_ref="$missing_fai_dir/genome.fa"
write_reference "$missing_fai_ref"
rm -f "$missing_fai_ref.fai"
missing_fai_output="$tmp_dir/missing_fai.out"
assert_fails "$missing_fai_output" run_step05 ABE_EV_2 "$input_bam" "$missing_fai_ref" "$tmp_dir/results/missing_fai"
assert_contains "$missing_fai_output" "Run Step 00c before Step 05"
assert_contains "$missing_fai_output" "does not create reference sidecars"
assert_not_exists "$missing_fai_ref.fai"

printf 'Running missing DICT failure check...\n'
missing_dict_dir="$tmp_dir/missing_dict"
missing_dict_ref="$missing_dict_dir/genome.fa"
write_reference "$missing_dict_ref"
rm -f "$missing_dict_dir/genome.dict"
missing_dict_output="$tmp_dir/missing_dict.out"
assert_fails "$missing_dict_output" run_step05 ABE_EV_2 "$input_bam" "$missing_dict_ref" "$tmp_dir/results/missing_dict"
assert_contains "$missing_dict_output" "Run Step 00c before Step 05"
assert_contains "$missing_dict_output" "does not create reference sidecars"
assert_not_exists "$missing_dict_dir/genome.dict"

printf 'Running missing explicit samtools admission check...\n'
missing_samtools_dir="$tmp_dir/results/missing_samtools"
missing_samtools_output="$tmp_dir/missing_samtools.out"
assert_fails "$missing_samtools_output" bash "$SCRIPT" \
    --sample-id ABE_EV_2 \
    --input-bam "$input_bam" \
    --reference-fasta "$reference_fasta" \
    --output-dir "$missing_samtools_dir" \
    --gatk-bin "$fake_bin/gatk" \
    --samtools-bin "$tmp_dir/missing-explicit-samtools" \
    --java-bin "$fake_bin/java" \
    --execute
assert_contains "$missing_samtools_output" "samtools does not exist"
assert_not_exists "$missing_samtools_dir"
assert_no_step05_attempt_marker "$missing_samtools_dir"

printf 'Running dry-run check...\n'
dry_output="$tmp_dir/dry.out"
dry_output_dir="$tmp_dir/results/dry/split_ncigar/ABE_EV_2"
NORAD_RUN_TOKEN=explicit-owner-05 SLURM_JOB_ID=scheduler-05 \
    run_step05 ABE_EV_2 "$input_bam" "$reference_fasta" "$dry_output_dir" >"$dry_output"
dry_bam="$dry_output_dir/ABE_EV_2.split_ncigar.bam"
assert_not_exists "$dry_output_dir"
[[ ! -e "$gatk_log" ]] || fail "dry-run invoked GATK"
[[ ! -e "$samtools_log" ]] || fail "dry-run invoked samtools"
[[ ! -e "$java_log" ]] || fail "dry-run invoked Java"
assert_contains "$dry_output" "Mode: dry-run"
assert_contains "$dry_output" "Run token: explicit-owner-05"
assert_contains "$dry_output" "Sample ID: ABE_EV_2"
assert_contains "$dry_output" "Input BAM: $input_bam"
assert_contains "$dry_output" "Input BAI: $input_bam.bai"
assert_contains "$dry_output" "Reference FASTA: $reference_fasta"
assert_contains "$dry_output" "Reference FAI: $reference_fasta.fai"
assert_contains "$dry_output" "Reference DICT: $(dirname "$reference_fasta")/genome.dict"
assert_contains "$dry_output" "Output BAM: $dry_bam"
assert_contains "$dry_output" "Output BAI: $dry_bam.bai"
assert_contains "$dry_output" "Lock directory: $dry_output_dir/.step_05_split_n_cigar_reads.lock"
assert_contains "$dry_output" ".ABE_EV_2.step05.explicit-owner-05.split_ncigar.tmp.bam"
assert_contains "$dry_output" "Alternate GATK temporary BAI:"
assert_contains "$dry_output" "GATK temp directory:"
assert_contains "$dry_output" ".ABE_EV_2.step05.explicit-owner-05.gatk_tmp"
assert_contains "$dry_output" "--java-options"
assert_contains "$dry_output" "-Djava.io.tmpdir="
assert_contains "$dry_output" "--tmp-dir"
assert_contains "$dry_output" "GATK temp directory creation action:"
assert_contains "$dry_output" "GATK temp cleanup action:"
assert_contains "$dry_output" "GATK SplitNCigarReads command:"
assert_contains "$dry_output" "SplitNCigarReads"
assert_contains "$dry_output" "-R"
assert_contains "$dry_output" "$reference_fasta"
assert_contains "$dry_output" "-I"
assert_contains "$dry_output" "$input_bam"
assert_contains "$dry_output" "-O"
assert_contains "$dry_output" "samtools index command:"
assert_contains "$dry_output" "Validation plan:"
assert_contains "$dry_output" "Dry-run only"
assert_not_contains "$dry_output" "sorted.md"

printf 'Running successful execute check...\n'
execute_output="$tmp_dir/execute.out"
execute_output_dir="$tmp_dir/results/execute/split_ncigar/ABE_EV_2"
rm -f "$gatk_log" "$samtools_log" "$java_log"
FAKE_SAMPLE_ID=ABE_EV_2 SLURM_JOB_ID=exec001 run_step05 ABE_EV_2 "$input_bam" "$reference_fasta" "$execute_output_dir" --execute >"$execute_output"
execute_bam="$execute_output_dir/ABE_EV_2.split_ncigar.bam"
execute_bai="$execute_bam.bai"
[[ -s "$execute_bam" ]] || fail "execute did not create non-empty split-N-cigar BAM"
[[ -s "$execute_bai" ]] || fail "execute did not create non-empty split-N-cigar BAI"
assert_contains "$execute_bam" $'@HD\tVN:1.6\tSO:coordinate'
assert_contains "$execute_bam" $'@RG\tID:ABE_EV_2\tSM:ABE_EV_2'
assert_contains "$execute_bam" "TOTAL:10"
assert_contains "$execute_bam" "TAGGED:10"
assert_contains "$gatk_log" "SplitNCigarReads"
assert_contains "$gatk_log" "--java-options"
assert_contains "$gatk_log" "-Djava.io.tmpdir="
assert_contains "$gatk_log" "--tmp-dir"
assert_contains "$gatk_log" ".ABE_EV_2.step05.exec001.gatk_tmp"
assert_contains "$gatk_log" "-R"
assert_contains "$gatk_log" "$reference_fasta"
assert_contains "$gatk_log" "-I"
assert_contains "$gatk_log" "$input_bam"
assert_contains "$gatk_log" "-O"
assert_contains "$samtools_log" "index"
assert_contains "$samtools_log" "quickcheck"
assert_contains "$samtools_log" "view"
assert_contains "$java_log" "-version"
assert_contains "$execute_output" "Mode: execute"
assert_contains "$execute_output" "GATK SplitNCigarReads output details:"
assert_not_exists "$execute_output_dir/.step_05_split_n_cigar_reads.lock"
assert_no_step05_scratch "$execute_output_dir"

printf 'Running orchestration-safe no-clobber checks...\n'
residue_output_dir="$tmp_dir/results/residue"
mkdir -p "$residue_output_dir"
residue_path="$residue_output_dir/.ABE_EV_2.step05.older-token.split_ncigar.tmp.bam"
printf 'preserve residue\n' >"$residue_path"
residue_output="$tmp_dir/residue.out"
assert_fails "$residue_output" env FAKE_SAMPLE_ID=ABE_EV_2 SLURM_JOB_ID=newer-token bash "$SCRIPT" \
    --sample-id ABE_EV_2 \
    --input-bam "$input_bam" \
    --reference-fasta "$reference_fasta" \
    --output-dir "$residue_output_dir" \
    --gatk-bin "$fake_bin/gatk" \
    --samtools-bin "$fake_bin/samtools" \
    --java-bin "$fake_bin/java" \
    --no-clobber \
    --execute
assert_contains "$residue_output" "residue requires operator inspection"
assert_file_equals "$residue_path" $'preserve residue\n'
assert_not_exists "$residue_output_dir/.ABE_EV_2.step05.lock"
safe_output="$tmp_dir/safe.out"
safe_output_dir="$tmp_dir/results/safe"
FAKE_SAMPLE_ID=ABE_EV_2 SLURM_JOB_ID=safe001 \
    run_step05 ABE_EV_2 "$input_bam" "$reference_fasta" "$safe_output_dir" --no-clobber --execute >"$safe_output"
assert_contains "$safe_output" "No-clobber transaction: true"
assert_contains "$safe_output" "Lock directory: $safe_output_dir/.ABE_EV_2.step05.lock"
assert_not_exists "$safe_output_dir/.ABE_EV_2.step05.lock"
safe_repeat_output="$tmp_dir/safe_repeat.out"
assert_fails "$safe_repeat_output" env FAKE_SAMPLE_ID=ABE_EV_2 SLURM_JOB_ID=safe002 bash "$SCRIPT" \
    --sample-id ABE_EV_2 \
    --input-bam "$input_bam" \
    --reference-fasta "$reference_fasta" \
    --output-dir "$safe_output_dir" \
    --gatk-bin "$fake_bin/gatk" \
    --samtools-bin "$fake_bin/samtools" \
    --java-bin "$fake_bin/java" \
    --no-clobber \
    --execute
assert_contains "$safe_repeat_output" "--no-clobber requires both final outputs to be absent"

safe_mutation_input_bam="$fixture_dir/safe_mutation/markdup/ABE_EV_2.markdup.bam"
safe_mutation_reference="$fixture_dir/safe_mutation/ref/genome.fa"
safe_mutation_dir="$tmp_dir/results/safe_mutation"
write_input_bam_pair "$safe_mutation_input_bam"
write_reference "$safe_mutation_reference"
safe_mutation_output="$tmp_dir/safe_mutation.out"
assert_fails "$safe_mutation_output" env FAKE_MUTATE_ADMITTED_INPUTS=1 FAKE_SAMPLE_ID=ABE_EV_2 SLURM_JOB_ID=safemutation001 bash "$SCRIPT" \
    --sample-id ABE_EV_2 \
    --input-bam "$safe_mutation_input_bam" \
    --reference-fasta "$safe_mutation_reference" \
    --output-dir "$safe_mutation_dir" \
    --gatk-bin "$fake_bin/gatk" \
    --samtools-bin "$fake_bin/samtools" \
    --java-bin "$fake_bin/java" \
    --no-clobber \
    --execute
assert_contains "$safe_mutation_output" "Input BAM changed during Step 05"
assert_not_exists "$safe_mutation_dir/ABE_EV_2.split_ncigar.bam"
assert_not_exists "$safe_mutation_dir/ABE_EV_2.split_ncigar.bam.bai"
assert_not_exists "$safe_mutation_dir/.ABE_EV_2.step05.lock"
assert_no_step05_scratch "$safe_mutation_dir"

printf 'Running admitted input mutation success check...\n'
mutation_input_bam="$fixture_dir/mutation/markdup/ABE_EV_2.markdup.bam"
mutation_reference_fasta="$fixture_dir/mutation/ref/genome.fa"
mutation_output_dir="$tmp_dir/results/mutation"
write_input_bam_pair "$mutation_input_bam"
write_reference "$mutation_reference_fasta"
mkdir -p "$mutation_output_dir"
printf 'unrelated mutation bytes' >"$mutation_output_dir/unrelated.txt"
mutation_output="$tmp_dir/mutation.out"
FAKE_MUTATE_ADMITTED_INPUTS=1 FAKE_SAMPLE_ID=ABE_EV_2 SLURM_JOB_ID=mutation001 \
    run_step05 ABE_EV_2 "$mutation_input_bam" "$mutation_reference_fasta" "$mutation_output_dir" --execute >"$mutation_output"
assert_file_equals "$mutation_input_bam" $'fake step04 markdup bam\nmutated input bam\n'
assert_file_equals "$mutation_input_bam.bai" $'fake step04 markdup bai\nmutated input bai\n'
assert_file_equals "$mutation_reference_fasta" $'>chrA\nACGTAC\n>chrB\nTTAA\nmutated reference fasta\n'
assert_file_equals "$mutation_reference_fasta.fai" $'chrA\t6\t0\t0\t0\nchrB\t4\t0\t0\t0\nmutated reference fai\n'
assert_file_equals "$(dirname "$mutation_reference_fasta")/genome.dict" $'@HD\tVN:1.6\n@SQ\tSN:chrA\tLN:6\n@SQ\tSN:chrB\tLN:4\nmutated reference dict\n'
[[ -s "$mutation_output_dir/ABE_EV_2.split_ncigar.bam" ]] || fail "input-mutation run did not publish BAM"
[[ -s "$mutation_output_dir/ABE_EV_2.split_ncigar.bam.bai" ]] || fail "input-mutation run did not publish BAI"
assert_file_equals "$mutation_output_dir/unrelated.txt" "unrelated mutation bytes"
assert_contains "$mutation_output" "GATK SplitNCigarReads output details:"
assert_not_exists "$mutation_output_dir/.step_05_split_n_cigar_reads.lock"
assert_no_step05_scratch "$mutation_output_dir"
assert_no_step05_attempt_marker "$mutation_output_dir"

printf 'Running Java version failure check...\n'
java_fail_output="$tmp_dir/java_fail.out"
java_fail_dir="$tmp_dir/results/java_fail"
assert_fails "$java_fail_output" env FAKE_JAVA_MAJOR=11 FAKE_SAMPLE_ID=ABE_EV_2 SLURM_JOB_ID=java001 bash "$SCRIPT" \
    --sample-id ABE_EV_2 \
    --input-bam "$input_bam" \
    --reference-fasta "$reference_fasta" \
    --output-dir "$java_fail_dir" \
    --gatk-bin "$fake_bin/gatk" \
    --samtools-bin "$fake_bin/samtools" \
    --java-bin "$fake_bin/java" \
    --execute
assert_contains "$java_fail_output" "requires Java 17 or newer"
assert_not_exists "$java_fail_dir/ABE_EV_2.split_ncigar.bam"
assert_not_exists "$java_fail_dir/ABE_EV_2.split_ncigar.bam.bai"
assert_not_exists "$java_fail_dir/.step_05_split_n_cigar_reads.lock"
assert_no_step05_scratch "$java_fail_dir"

printf 'Running existing lock failure check...\n'
lock_dir="$tmp_dir/results/locked"
mkdir -p "$lock_dir/.step_05_split_n_cigar_reads.lock"
printf 'run_token=other-job\n' >"$lock_dir/.step_05_split_n_cigar_reads.lock/owner"
lock_output="$tmp_dir/lock.out"
assert_fails "$lock_output" env FAKE_SAMPLE_ID=ABE_EV_2 SLURM_JOB_ID=lock001 bash "$SCRIPT" \
    --sample-id ABE_EV_2 \
    --input-bam "$input_bam" \
    --reference-fasta "$reference_fasta" \
    --output-dir "$lock_dir" \
    --gatk-bin "$fake_bin/gatk" \
    --samtools-bin "$fake_bin/samtools" \
    --java-bin "$fake_bin/java" \
    --execute
assert_contains "$lock_output" "Step 05 lock already exists"
assert_contains "$lock_output" "run_token=other-job"
[[ -d "$lock_dir/.step_05_split_n_cigar_reads.lock" ]] || fail "foreign lock should remain"
assert_not_exists "$lock_dir/ABE_EV_2.split_ncigar.bam"
assert_not_exists "$lock_dir/ABE_EV_2.split_ncigar.bam.bai"
assert_no_step05_scratch "$lock_dir"

printf 'Running controlled TERM cleanup check...\n'
signal_dir="$tmp_dir/results/signal"
mkdir -p "$signal_dir"
printf 'previous signal bam' >"$signal_dir/ABE_EV_2.split_ncigar.bam"
printf 'previous signal bai' >"$signal_dir/ABE_EV_2.split_ncigar.bam.bai"
printf 'unrelated signal bytes' >"$signal_dir/unrelated.txt"
signal_output="$tmp_dir/signal.out"
assert_exits 143 "$signal_output" env \
    FAKE_GATK_TERM_PARENT=1 \
    FAKE_SAMPLE_ID=ABE_EV_2 \
    SLURM_JOB_ID=signal001 \
    bash "$SCRIPT" \
    --sample-id ABE_EV_2 \
    --input-bam "$input_bam" \
    --reference-fasta "$reference_fasta" \
    --output-dir "$signal_dir" \
    --gatk-bin "$fake_bin/gatk" \
    --samtools-bin "$fake_bin/samtools" \
    --java-bin "$fake_bin/java" \
    --execute
assert_file_equals "$signal_dir/ABE_EV_2.split_ncigar.bam" "previous signal bam"
assert_file_equals "$signal_dir/ABE_EV_2.split_ncigar.bam.bai" "previous signal bai"
assert_file_equals "$signal_dir/unrelated.txt" "unrelated signal bytes"
assert_not_exists "$signal_dir/.step_05_split_n_cigar_reads.lock"
assert_no_step05_scratch "$signal_dir"
assert_no_step05_attempt_marker "$signal_dir"

printf 'Running GATK failure cleanup check...\n'
gatk_fail_output="$tmp_dir/gatk_fail.out"
gatk_fail_dir="$tmp_dir/results/gatk_fail"
assert_fails "$gatk_fail_output" env FAKE_GATK_FAIL=1 FAKE_SAMPLE_ID=ABE_EV_2 SLURM_JOB_ID=gatk001 bash "$SCRIPT" \
    --sample-id ABE_EV_2 \
    --input-bam "$input_bam" \
    --reference-fasta "$reference_fasta" \
    --output-dir "$gatk_fail_dir" \
    --gatk-bin "$fake_bin/gatk" \
    --samtools-bin "$fake_bin/samtools" \
    --java-bin "$fake_bin/java" \
    --execute
assert_contains "$gatk_fail_output" "fake gatk forced failure"
assert_not_exists "$gatk_fail_dir/ABE_EV_2.split_ncigar.bam"
assert_not_exists "$gatk_fail_dir/ABE_EV_2.split_ncigar.bam.bai"
assert_not_exists "$gatk_fail_dir/.step_05_split_n_cigar_reads.lock"
assert_no_step05_scratch "$gatk_fail_dir"

printf 'Running quickcheck validation failure cleanup check...\n'
quickcheck_fail_output="$tmp_dir/quickcheck_fail.out"
quickcheck_fail_dir="$tmp_dir/results/quickcheck_fail"
assert_fails "$quickcheck_fail_output" env FAKE_QUICKCHECK_FAIL=1 FAKE_SAMPLE_ID=ABE_EV_2 SLURM_JOB_ID=quick001 bash "$SCRIPT" \
    --sample-id ABE_EV_2 \
    --input-bam "$input_bam" \
    --reference-fasta "$reference_fasta" \
    --output-dir "$quickcheck_fail_dir" \
    --gatk-bin "$fake_bin/gatk" \
    --samtools-bin "$fake_bin/samtools" \
    --java-bin "$fake_bin/java" \
    --execute
assert_contains "$quickcheck_fail_output" "failed samtools quickcheck"
assert_not_exists "$quickcheck_fail_dir/ABE_EV_2.split_ncigar.bam"
assert_not_exists "$quickcheck_fail_dir/ABE_EV_2.split_ncigar.bam.bai"
assert_not_exists "$quickcheck_fail_dir/.step_05_split_n_cigar_reads.lock"
assert_no_step05_scratch "$quickcheck_fail_dir"

printf 'Running header validation failure cleanup check...\n'
header_fail_output="$tmp_dir/header_fail.out"
header_fail_dir="$tmp_dir/results/header_fail"
assert_fails "$header_fail_output" env FAKE_SORT_ORDER=unknown FAKE_SAMPLE_ID=ABE_EV_2 SLURM_JOB_ID=header001 bash "$SCRIPT" \
    --sample-id ABE_EV_2 \
    --input-bam "$input_bam" \
    --reference-fasta "$reference_fasta" \
    --output-dir "$header_fail_dir" \
    --gatk-bin "$fake_bin/gatk" \
    --samtools-bin "$fake_bin/samtools" \
    --java-bin "$fake_bin/java" \
    --execute
assert_contains "$header_fail_output" "header is not coordinate sorted"
assert_not_exists "$header_fail_dir/ABE_EV_2.split_ncigar.bam"
assert_not_exists "$header_fail_dir/ABE_EV_2.split_ncigar.bam.bai"
assert_not_exists "$header_fail_dir/.step_05_split_n_cigar_reads.lock"
assert_no_step05_scratch "$header_fail_dir"

printf 'Running validation failure preserves existing final pair check...\n'
rollback_dir="$tmp_dir/results/rollback"
mkdir -p "$rollback_dir"
printf 'previous bam' >"$rollback_dir/ABE_EV_2.split_ncigar.bam"
printf 'previous bai' >"$rollback_dir/ABE_EV_2.split_ncigar.bam.bai"
rollback_output="$tmp_dir/rollback.out"
assert_fails "$rollback_output" env FAKE_INDEX_EMPTY=1 FAKE_SAMPLE_ID=ABE_EV_2 SLURM_JOB_ID=rollback001 bash "$SCRIPT" \
    --sample-id ABE_EV_2 \
    --input-bam "$input_bam" \
    --reference-fasta "$reference_fasta" \
    --output-dir "$rollback_dir" \
    --gatk-bin "$fake_bin/gatk" \
    --samtools-bin "$fake_bin/samtools" \
    --java-bin "$fake_bin/java" \
    --execute
assert_contains "$rollback_output" "BAI is missing or empty"
assert_file_equals "$rollback_dir/ABE_EV_2.split_ncigar.bam" "previous bam"
assert_file_equals "$rollback_dir/ABE_EV_2.split_ncigar.bam.bai" "previous bai"
assert_not_exists "$rollback_dir/.step_05_split_n_cigar_reads.lock"
assert_no_step05_scratch "$rollback_dir"

printf 'Running lone-final rejection preservation check...\n'
lone_final_dir="$tmp_dir/results/lone_final"
mkdir -p "$lone_final_dir"
printf 'lone final bam bytes' >"$lone_final_dir/ABE_EV_2.split_ncigar.bam"
printf 'unrelated lone-final bytes' >"$lone_final_dir/unrelated.txt"
lone_final_output="$tmp_dir/lone_final.out"
assert_fails "$lone_final_output" env FAKE_SAMPLE_ID=ABE_EV_2 SLURM_JOB_ID=lone001 bash "$SCRIPT" \
    --sample-id ABE_EV_2 \
    --input-bam "$input_bam" \
    --reference-fasta "$reference_fasta" \
    --output-dir "$lone_final_dir" \
    --gatk-bin "$fake_bin/gatk" \
    --samtools-bin "$fake_bin/samtools" \
    --java-bin "$fake_bin/java" \
    --execute
assert_contains "$lone_final_output" "Step 05 final outputs are inconsistent"
assert_file_equals "$lone_final_dir/ABE_EV_2.split_ncigar.bam" "lone final bam bytes"
assert_not_exists "$lone_final_dir/ABE_EV_2.split_ncigar.bam.bai"
assert_file_equals "$lone_final_dir/unrelated.txt" "unrelated lone-final bytes"
assert_not_exists "$lone_final_dir/.step_05_split_n_cigar_reads.lock"
assert_no_step05_scratch "$lone_final_dir"
assert_no_step05_recovery "$lone_final_dir"

printf 'Running final-path revalidation rollback check...\n'
final_revalidation_dir="$tmp_dir/results/final_revalidation"
mkdir -p "$final_revalidation_dir"
printf 'previous final-revalidation bam' >"$final_revalidation_dir/ABE_EV_2.split_ncigar.bam"
printf 'previous final-revalidation bai' >"$final_revalidation_dir/ABE_EV_2.split_ncigar.bam.bai"
printf 'unrelated final-revalidation bytes' >"$final_revalidation_dir/unrelated.txt"
final_revalidation_output="$tmp_dir/final_revalidation.out"
assert_fails "$final_revalidation_output" env FAKE_QUICKCHECK_FAIL_FINAL=1 FAKE_SAMPLE_ID=ABE_EV_2 SLURM_JOB_ID=finalcheck001 bash "$SCRIPT" \
    --sample-id ABE_EV_2 \
    --input-bam "$input_bam" \
    --reference-fasta "$reference_fasta" \
    --output-dir "$final_revalidation_dir" \
    --gatk-bin "$fake_bin/gatk" \
    --samtools-bin "$fake_bin/samtools" \
    --java-bin "$fake_bin/java" \
    --execute
assert_contains "$final_revalidation_output" "Published BAM failed samtools quickcheck"
assert_contains "$final_revalidation_output" "Rolling back Step 05"
assert_file_equals "$final_revalidation_dir/ABE_EV_2.split_ncigar.bam" "previous final-revalidation bam"
assert_file_equals "$final_revalidation_dir/ABE_EV_2.split_ncigar.bam.bai" "previous final-revalidation bai"
assert_file_equals "$final_revalidation_dir/unrelated.txt" "unrelated final-revalidation bytes"
assert_not_exists "$final_revalidation_dir/.step_05_split_n_cigar_reads.lock"
assert_no_step05_scratch "$final_revalidation_dir"
assert_no_step05_recovery "$final_revalidation_dir"

printf 'Running post-backup rollback check...\n'
post_backup_dir="$tmp_dir/results/post_backup"
mkdir -p "$post_backup_dir"
printf 'previous post-backup bam' >"$post_backup_dir/ABE_EV_2.split_ncigar.bam"
printf 'previous post-backup bai' >"$post_backup_dir/ABE_EV_2.split_ncigar.bam.bai"
post_backup_output="$tmp_dir/post_backup.out"
assert_fails "$post_backup_output" env FAKE_SAMPLE_ID=ABE_EV_2 FAKE_MV_FAIL_ONCE_DEST_MATCH="ABE_EV_2.split_ncigar.bam.bai" SLURM_JOB_ID=postbackup001 bash "$SCRIPT" \
    --sample-id ABE_EV_2 \
    --input-bam "$input_bam" \
    --reference-fasta "$reference_fasta" \
    --output-dir "$post_backup_dir" \
    --gatk-bin "$fake_bin/gatk" \
    --samtools-bin "$fake_bin/samtools" \
    --java-bin "$fake_bin/java" \
    --execute
assert_contains "$post_backup_output" "fake mv forced failure"
assert_contains "$post_backup_output" "Rolling back Step 05"
assert_file_equals "$post_backup_dir/ABE_EV_2.split_ncigar.bam" "previous post-backup bam"
assert_file_equals "$post_backup_dir/ABE_EV_2.split_ncigar.bam.bai" "previous post-backup bai"
assert_not_exists "$post_backup_dir/.step_05_split_n_cigar_reads.lock"
assert_no_step05_scratch "$post_backup_dir"

printf 'Running failure-inside-rollback residue check...\n'
restore_failure_dir="$tmp_dir/results/restore_failure"
mkdir -p "$restore_failure_dir"
printf 'previous restore-failure bam' >"$restore_failure_dir/ABE_EV_2.split_ncigar.bam"
printf 'previous restore-failure bai' >"$restore_failure_dir/ABE_EV_2.split_ncigar.bam.bai"
printf 'unrelated restore-failure bytes' >"$restore_failure_dir/unrelated.txt"
restore_failure_output="$tmp_dir/restore_failure.out"
rm -f "$tmp_dir/fake_mv_failed_once"
assert_exits 67 "$restore_failure_output" env \
    FAKE_SAMPLE_ID=ABE_EV_2 \
    FAKE_MV_FAIL_ONCE_DEST_MATCH="ABE_EV_2.split_ncigar.bam.bai" \
    FAKE_MV_FAIL_SOURCE_MATCH=".previous.bam" \
    SLURM_JOB_ID=restorefail001 \
    bash "$SCRIPT" \
    --sample-id ABE_EV_2 \
    --input-bam "$input_bam" \
    --reference-fasta "$reference_fasta" \
    --output-dir "$restore_failure_dir" \
    --gatk-bin "$fake_bin/gatk" \
    --samtools-bin "$fake_bin/samtools" \
    --java-bin "$fake_bin/java" \
    --execute
assert_contains "$restore_failure_output" "fake mv forced failure"
assert_contains "$restore_failure_output" "Rolling back Step 05"
assert_contains "$restore_failure_output" "fake mv forced restore failure"
assert_not_exists "$restore_failure_dir/ABE_EV_2.split_ncigar.bam"
assert_file_equals "$restore_failure_dir/ABE_EV_2.split_ncigar.bam.bai" "previous restore-failure bai"
assert_file_equals "$restore_failure_dir/unrelated.txt" "unrelated restore-failure bytes"
assert_not_exists "$restore_failure_dir/.step_05_split_n_cigar_reads.lock"
assert_no_step05_scratch "$restore_failure_dir"
assert_no_step05_recovery "$restore_failure_dir"

printf 'Running stale path and sidecar non-creation checks...\n'
stale_output="$tmp_dir/stale.out"
if grep -F "sorted.md" "$SCRIPT" "$JOB" >"$stale_output"; then
    cat "$stale_output" >&2
    fail "Step 05 files should not use stale sorted.md paths"
fi
assert_not_contains "$execute_output" "sorted.md"
assert_file_equals "$reference_fasta.fai" $'chrA\t6\t0\t0\t0\nchrB\t4\t0\t0\t0\n'
assert_contains "$(dirname "$reference_fasta")/genome.dict" $'@SQ\tSN:chrA\tLN:6'

printf 'All step_05 GATK SplitNCigarReads smoke tests passed.\n'
