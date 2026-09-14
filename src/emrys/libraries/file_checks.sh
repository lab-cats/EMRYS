# shellcheck shell=bash
# Shared file-validation helpers for Bash pipeline stages.

is_gzip_path() {
    [[ "$1" == *.gz ]]
}

require_executable() {
    [[ "$2" == /* && -f "$2" && -x "$2" ]] ||
        die "$1 must be an absolute executable file: $2"
}

sha256_file() {
    local path="$1"
    local python_bin="${EMRYS_SHA256_PYTHON:-}"

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
