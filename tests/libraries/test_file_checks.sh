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

die() {
    printf 'ERROR: %s\n' "$*" >&2
    return 1
}

hash_input="$test_root/hash-input.txt"
printf 'bound hashing\n' >"$hash_input"
unset NORAD_SHA256_PYTHON
NORAD_REQUIRE_BOUND_SHA256=1
expect_failure "missing SHA-256 Python binding" sha256_file "$hash_input"
unset NORAD_REQUIRE_BOUND_SHA256
NORAD_SHA256_PYTHON=python3
expect_failure "relative SHA-256 Python binding" sha256_file "$hash_input"
NORAD_SHA256_PYTHON="$(command -v python3)"
[[ "$(sha256_file "$hash_input")" == \
   "0c009bef8b5cd42114e0daf15a7ded967e9fd9041adaa491055fb90b8573bc4f" ]] ||
    fail "bound Python did not produce the expected SHA-256 digest"
export NORAD_SHA256_PYTHON

source "$repo_root/src/norad/libraries/signal_traps.sh"

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

residue_root="$test_root/residue"
mkdir -p "$residue_root"
require_no_owner_residue "Step fixture" "$residue_root" '.sample.step.*'
printf 'preserve\n' >"$residue_root/.sample.step.old-token.tmp"
expect_failure "cross-token owner residue" \
    require_no_owner_residue "Step fixture" "$residue_root" '.sample.step.*'
[[ -f "$residue_root/.sample.step.old-token.tmp" ]] ||
    fail "residue inspection removed the foreign path"
require_no_owner_residue "Unrelated owner" "$residue_root" '.other.step.*'

staged_publication="$test_root/staged-publication.txt"
final_publication="$test_root/final-publication.txt"
printf 'complete publication\n' >"$staged_publication"
publish_file_create_exclusive \
    "test publication" "$staged_publication" "$final_publication"
[[ "$final_publication" -ef "$staged_publication" ]] ||
    fail "create-exclusive publication did not retain the staged inode"
remove_owned_published_file \
    "test publication" "$staged_publication" "$final_publication"
[[ ! -e "$final_publication" ]] ||
    fail "owned publication rollback left the final path"

printf 'late foreign final\n' >"$final_publication"
expect_failure "late foreign final" \
    publish_file_create_exclusive \
    "test publication" "$staged_publication" "$final_publication"
[[ "$(cat "$final_publication")" == "late foreign final" ]] ||
    fail "create-exclusive publication changed a foreign final"

rm -f "$final_publication"
ln "$staged_publication" "$final_publication"
foreign_replacement="$test_root/foreign-replacement.txt"
printf 'foreign replacement\n' >"$foreign_replacement"
mv "$foreign_replacement" "$final_publication"
expect_failure "foreign replacement ownership" \
    remove_owned_published_file \
    "test publication" "$staged_publication" "$final_publication"
[[ "$(cat "$final_publication")" == "foreign replacement" ]] ||
    fail "rollback changed a foreign replacement"

rm -f "$final_publication"
ln "$staged_publication" "$final_publication"
same_byte_replacement="$test_root/same-byte-replacement.txt"
cp "$final_publication" "$same_byte_replacement"
mv "$same_byte_replacement" "$final_publication"
expect_failure "same-byte foreign replacement ownership" \
    require_owned_published_file \
    "test publication" "$staged_publication" "$final_publication"
[[ "$(cat "$final_publication")" == "complete publication" ]] ||
    fail "ownership check changed a same-byte foreign replacement"

rm -f "$final_publication"
expect_failure "disappeared final ownership" \
    remove_owned_published_file \
    "test publication" "$staged_publication" "$final_publication"

lock_path="$test_root/owned-lock"
lock_owner_file="$lock_path/owner"
run_token="lock-test"
lock_acquired=false
mkdir "$lock_path"
printf 'run_token=%s\n' "$run_token" >"$lock_owner_file"
lock_acquired=true
printf 'unexpected residue\n' >"$lock_path/foreign"
expect_failure "lock residue preservation" remove_owned_lock
[[ -f "$lock_owner_file" && -f "$lock_path/foreign" &&
   "$lock_acquired" == true ]] ||
    fail "failed lock release did not preserve ownership evidence"
rm -f "$lock_path/foreign"
remove_owned_lock
[[ ! -e "$lock_path" && "$lock_acquired" == false ]] ||
    fail "clean owned lock was not removed"
