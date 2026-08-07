# Shared file-validation helpers for Bash pipeline stages.

is_gzip_path() {
    [[ "$1" == *.gz ]]
}

sha256_file() {
    local path="$1"

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

validate_exact_header() {
    local label="$1"
    local path="$2"
    local expected="$3"
    local observed

    validate_nonempty_file "$label" "$path"
    IFS= read -r observed < "$path"
    [[ "$observed" == "$expected" ]] || die "$label header is invalid: $path"
}
