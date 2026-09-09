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

source "$repo_root/src/emrys/libraries/file_checks.sh"

die() {
    printf 'ERROR: %s\n' "$*" >&2
    return 1
}

hash_input="$test_root/hash-input.txt"
printf 'bound hashing\n' >"$hash_input"
unset EMRYS_SHA256_PYTHON
EMRYS_REQUIRE_BOUND_SHA256=1
expect_failure "missing SHA-256 Python binding" sha256_file "$hash_input"
unset EMRYS_REQUIRE_BOUND_SHA256
EMRYS_SHA256_PYTHON=python3
expect_failure "relative SHA-256 Python binding" sha256_file "$hash_input"
EMRYS_TEST_REAL_PYTHON="$(command -v python3)"
export EMRYS_TEST_REAL_PYTHON
guarded_python="$test_root/guarded-python"
# shellcheck disable=SC2016 # The generated launcher expands its own arguments.
printf '%s\n' \
    '#!/usr/bin/env bash' \
    'set -euo pipefail' \
    '[[ "$#" -ge 4 ]] || exit 91' \
    '[[ "$1" == -X && "$2" == pycache_prefix=/dev/null && "$3" == -I && "$4" == -c ]] || exit 92' \
    'shift 4' \
    'exec "$EMRYS_TEST_REAL_PYTHON" -X pycache_prefix=/dev/null -I -c "$@"' \
    >"$guarded_python"
chmod 0755 "$guarded_python"
EMRYS_SHA256_PYTHON="$guarded_python"
[[ "$(sha256_file "$hash_input")" == \
   "0c009bef8b5cd42114e0daf15a7ded967e9fd9041adaa491055fb90b8573bc4f" ]] ||
    fail "bound Python did not use the controlled prefix and expected SHA-256 digest"
export EMRYS_SHA256_PYTHON
