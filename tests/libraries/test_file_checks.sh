#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
test_root="$(mktemp -d)"
trap 'rm -rf "$test_root"' EXIT

fail() {
    printf 'FAIL: %s\n' "$*" >&2
    exit 1
}

expect_failure() {
    local label="$1"
    shift
    if "$@"; then
        fail "$label unexpectedly succeeded"
    fi
}

source "$repo_root/src/norad/libraries/file_checks.sh"

valid_samples="$test_root/valid-samples.tsv"
invalid_samples="$test_root/invalid-samples.tsv"
valid_partitions="$test_root/valid-partitions.tsv"
invalid_partitions="$test_root/invalid-partitions.tsv"

printf 'sample_id\nS1\n' >"$valid_samples"
printf 'wrong_header\nS1\n' >"$invalid_samples"
printf 'partition_id\tselector_type\tselector_value\np1\tregion\tchr1\n' \
    >"$valid_partitions"
printf 'wrong\theader\np1\tchr1\n' >"$invalid_partitions"

expect_failure "malformed sample manifest" \
    read_manifest_sample_ids "$invalid_samples"
expect_failure "malformed partition manifest" \
    read_manifest_partitions "$invalid_partitions"

reject_sample() {
    return 9
}

reject_partition() {
    return 8
}

sample_status=0
read_manifest_sample_ids "$valid_samples" reject_sample || sample_status=$?
[[ "$sample_status" == 9 ]] ||
    fail "sample callback status was $sample_status; expected 9"

partition_status=0
read_manifest_partitions "$valid_partitions" reject_partition || partition_status=$?
[[ "$partition_status" == 8 ]] ||
    fail "partition callback status was $partition_status; expected 8"

[[ "$(read_manifest_sample_ids "$valid_samples")" == S1 ]] ||
    fail "valid sample manifest did not preserve its sample ID"
[[ "$(read_manifest_partitions "$valid_partitions")" == $'p1\tregion\tchr1' ]] ||
    fail "valid partition manifest did not preserve its row"
