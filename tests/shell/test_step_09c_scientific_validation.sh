#!/usr/bin/env bash
# Focused local lifecycle tests for the public Step 09c shell launcher.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
script="$repo_root/scripts/step_09c_scientific_validation.sh"
fixture_builder="$repo_root/tests/fixtures/step09c/build_fixture.py"
test_root="$(mktemp -d)"
trap 'rm -rf "$test_root"' EXIT

fail() {
    printf 'FAIL: %s\n' "$*" >&2
    exit 1
}

assert_contains() {
    local value="$1"
    local expected="$2"
    [[ "$value" == *"$expected"* ]] ||
        fail "expected output to contain '$expected'"
}

assert_file_equals() {
    local path="$1"
    local expected="$2"
    [[ -f "$path" ]] || fail "expected file does not exist: $path"
    [[ "$(<"$path")" == "$expected" ]] ||
        fail "unexpected file content: $path"
}

expect_failure() {
    local expected_pattern="$1"
    shift
    if "$@" >"$test_root/failure.out" 2>"$test_root/failure.err"; then
        fail "command unexpectedly succeeded: $*"
    fi
    grep -Eiq "$expected_pattern" "$test_root/failure.err" ||
        fail "failure did not contain '$expected_pattern': $(<"$test_root/failure.err")"
}

if [[ -x "$repo_root/.venv/bin/python" ]]; then
    test_python="$repo_root/.venv/bin/python"
else
    test_python="$(command -v python3 || true)"
fi
[[ -n "$test_python" && -x "$test_python" ]] ||
    fail "Python is required for the Step 09c shell test."
[[ -f "$fixture_builder" ]] ||
    fail "Step 09c fixture builder is missing: $fixture_builder"

fixture_root="$test_root/fixture"
"$test_python" "$fixture_builder" \
    --root "$fixture_root" \
    --science-status evidence_incomplete

review_id="review_fixture"
input_args=(
    --review-id "$review_id"
    --sample-manifest "$fixture_root/samples.tsv"
    --partition-manifest "$fixture_root/partitions.tsv"
    --step08-sites "$fixture_root/step08/cohort.step08_sites.tsv"
    --step08-inputs "$fixture_root/step08/cohort.step08_inputs.tsv"
    --step08-summary "$fixture_root/step08/cohort.step08_summary.tsv"
    --step09-analysis-dir "$fixture_root/step09/analysis_primary"
    --review-plan "$fixture_root/review_plan.tsv"
    --evidence-manifest "$fixture_root/evidence_manifest.tsv"
)

run_step09c() {
    local output_root="$1"
    shift
    env PYTHON_BIN_OVERRIDE="$test_python" \
        bash "$script" \
        "${input_args[@]}" \
        --output-root "$output_root" \
        "$@"
}

printf 'Running Step 09c wrapper help and required-argument checks...\n'
help_output="$(bash "$script" --help)"
for option in \
    --review-id \
    --sample-manifest \
    --partition-manifest \
    --step08-sites \
    --step08-inputs \
    --step08-summary \
    --step09-analysis-dir \
    --review-plan \
    --evidence-manifest \
    --output-root \
    --execute
do
    assert_contains "$help_output" "$option"
done

expect_failure \
    "missing required argument" \
    env PYTHON_BIN_OVERRIDE="$test_python" \
    bash "$script" \
    --review-id "$review_id"

printf 'Running Step 09c side-effect-free dry-run check...\n'
dry_output_root="$test_root/dry-output"
run_step09c "$dry_output_root" >"$test_root/dry-run.out"
assert_contains "$(<"$test_root/dry-run.out")" "Mode: dry-run"
[[ ! -e "$dry_output_root" ]] ||
    fail "Step 09c dry-run created its output root: $dry_output_root"

printf 'Running Step 09c successful 13-output publication check...\n'
execute_output_root="$test_root/execute-output"
run_step09c "$execute_output_root" --execute >"$test_root/execute.out"
execute_dir="$execute_output_root/$review_id"
[[ -d "$execute_dir" ]] ||
    fail "Step 09c execute did not create its review directory."

published_count="$(
    find "$execute_dir" \
        -maxdepth 1 \
        -type f \
        -name "$review_id.step09c_*.tsv" |
        wc -l |
        tr -d '[:space:]'
)"
[[ "$published_count" == "13" ]] ||
    fail "expected exactly 13 published Step 09c TSVs; got $published_count"

summary="$execute_dir/$review_id.step09c_review_summary.tsv"
[[ -s "$summary" ]] ||
    fail "Step 09c review summary commit marker is missing or empty: $summary"
[[ ! -e "$execute_dir/.$review_id.step09c.lock" ]] ||
    fail "successful Step 09c execution retained its lock."

printf 'Running Step 09c foreign-lock refusal and preservation check...\n'
foreign_output_root="$test_root/foreign-output"
foreign_dir="$foreign_output_root/$review_id"
foreign_lock="$foreign_dir/.$review_id.step09c.lock"
mkdir -p "$foreign_lock"
printf 'foreign owner\n' >"$foreign_lock/owner"

expect_failure \
    "lock" \
    run_step09c "$foreign_output_root" --execute
assert_file_equals "$foreign_lock/owner" "foreign owner"
foreign_final_count="$(
    find "$foreign_dir" \
        -maxdepth 1 \
        -type f \
        -name "$review_id.step09c_*.tsv" |
        wc -l |
        tr -d '[:space:]'
)"
[[ "$foreign_final_count" == "0" ]] ||
    fail "foreign-lock refusal published stable Step 09c outputs."

printf 'Running Step 09c partial-prior-output refusal check...\n'
partial_output_root="$test_root/partial-output"
partial_dir="$partial_output_root/$review_id"
partial_file="$partial_dir/$review_id.step09c_review_plan.tsv"
mkdir -p "$partial_dir"
printf 'prior partial output\n' >"$partial_file"

expect_failure \
    "incomplete|all 13|all thirteen" \
    run_step09c "$partial_output_root" --execute
assert_file_equals "$partial_file" "prior partial output"
[[ ! -e "$partial_dir/$review_id.step09c_review_summary.tsv" ]] ||
    fail "partial-set refusal published a summary commit marker."

printf 'PASS: Step 09c scientific-validation shell tests\n'
