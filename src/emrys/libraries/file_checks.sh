# shellcheck shell=bash
# Shared file-validation helpers for Bash pipeline stages.

is_gzip_path() {
    [[ "$1" == *.gz ]]
}

sha256_file() {
    local path="$1"
    local python_bin="${EMRYS_SHA256_PYTHON:-}"

    if [[ -z "$python_bin" ]]; then
        if [[ "${EMRYS_REQUIRE_BOUND_SHA256:-0}" == 1 ]]; then
            die "EMRYS_SHA256_PYTHON must bind the admitted workflow Python launcher."
            return 1
        fi
        if command -v sha256sum >/dev/null 2>&1; then
            sha256sum "$path" | awk '{print $1}'
        elif command -v shasum >/dev/null 2>&1; then
            shasum -a 256 "$path" | awk '{print $1}'
        elif command -v python3 >/dev/null 2>&1; then
            python3 -c '
import hashlib
import sys

digest = hashlib.sha256()
with open(sys.argv[1], "rb") as handle:
    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
        digest.update(chunk)
print(digest.hexdigest())
' "$path"
        else
            die "No SHA-256 implementation found (sha256sum, shasum, or python3)."
        fi
        return
    fi
    if [[ "$python_bin" != /* ]]; then
        die "EMRYS_SHA256_PYTHON must be an absolute path: $python_bin"
        return 1
    fi
    if [[ ! -x "$python_bin" ]]; then
        die "EMRYS_SHA256_PYTHON is not executable: $python_bin"
        return 1
    fi
    "$python_bin" -X pycache_prefix=/dev/null -I -c '
import hashlib
import sys

digest = hashlib.sha256()
with open(sys.argv[1], "rb") as handle:
    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
        digest.update(chunk)
print(digest.hexdigest())
' "$path"
}

validate_nonempty_file() {
    local label="$1"
    local path="$2"
    [[ -s "$path" ]] || die "$label does not exist or is empty: $path"
}

validate_safe_id() {
    local label="$1"
    local value="$2"
    [[ "$value" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]] ||
        die "$label must match [A-Za-z0-9][A-Za-z0-9._-]*; got: $value"
}

validate_positive_integer() {
    local label="${1:-value}"
    local value="${2:-}"
    [[ "$value" =~ ^[1-9][0-9]*$ ]] ||
        die "$label must be a positive integer; got: $value"
}

validate_nonnegative_integer() {
    local label="${1:-value}"
    local value="${2:-}"
    [[ "$value" =~ ^(0|[1-9][0-9]*)$ ]] ||
        die "$label must be a non-negative integer; got: $value"
}
