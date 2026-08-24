#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$repo_root"

fail() {
    printf 'FAIL: %s\n' "$*" >&2
    exit 1
}

tmp="$(mktemp -d "${TMPDIR:-/tmp}/norad-r-contract.XXXXXX")"
trap 'rm -rf "$tmp"' EXIT

fake_rscript="$tmp/Rscript"
fake_log="$tmp/rscript.log"
cat >"$fake_rscript" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
printf 'NORAD_USE_RENV=%s\tNORAD_LOCAL_PILOT_R=%s\tNORAD_RENV_LIBRARY=%s\tNORAD_RENV_VERSION=%s\tRENV_SANDBOX=%s\tRENV_AUTO_SNAPSHOT=%s\tRENV_PROJECT=%s\tR_PROFILE_USER=%s\targs=' \
    "${NORAD_USE_RENV:-<unset>}" \
    "${NORAD_LOCAL_PILOT_R:-<unset>}" \
    "${NORAD_RENV_LIBRARY:-<unset>}" \
    "${NORAD_RENV_VERSION:-<unset>}" \
    "${RENV_CONFIG_SANDBOX_ENABLED:-<unset>}" \
    "${RENV_CONFIG_AUTO_SNAPSHOT:-<unset>}" \
    "${RENV_PROJECT:-<unset>}" \
    "${R_PROFILE_USER:-<unset>}" >>"${FAKE_R_LOG:?}"
printf '%q ' "$@" >>"$FAKE_R_LOG"
printf '\n' >>"$FAKE_R_LOG"
case "$*" in
    *step_08_vcf_preprocessing.R*--help*)
        printf 'Usage: step_08_vcf_preprocessing.R --cohort-id ID\n'
        ;;
    *step_09_cmh_editing_site_calling.R*--help*)
        printf 'Usage: step_09_cmh_editing_site_calling.R --analysis-id ID\n'
        ;;
esac
EOF
chmod +x "$fake_rscript"

fake_renv_library="$tmp/renv-library"
mkdir -p "$fake_renv_library/renv"
printf 'Package: renv\nVersion: 1.2.3\n' \
    >"$fake_renv_library/renv/DESCRIPTION"

grep -Fq 'identical(use_renv, "1")' .Rprofile ||
    fail ".Rprofile does not guard renv activation"
grep -Fq 'NORAD_USE_RENV must be exactly 0 or 1' .Rprofile ||
    fail ".Rprofile does not reject invalid activation values"
if grep -Eq '^source\\("renv/activate\\.R"\\)' .Rprofile; then
    fail ".Rprofile activates renv unconditionally"
fi

grep -Fq '"bioconductor.version": "3.23"' renv/settings.json ||
    fail "renv settings do not pin Bioconductor 3.23"
test -s renv/activate.R || fail "renv activation script is missing"
test -s renv.lock || fail "renv lockfile is missing"
grep -Fq '"Version": "4.6.1"' renv.lock ||
    fail "renv lockfile does not pin R 4.6.1"
grep -Fq '"Version": "3.23"' renv.lock ||
    fail "renv lockfile does not record Bioconductor 3.23"
for package_name in \
    VariantAnnotation Biostrings GenomicRanges IRanges Rsamtools S4Vectors \
    SummarizedExperiment GenomeInfoDb BiocGenerics rtracklayer; do
    grep -Fq "\"$package_name\":" renv.lock ||
        fail "renv lockfile is missing $package_name"
done

for ignored_path in \
    'renv/library/' 'renv/cache/' 'renv/staging/' '.renv-cache/'; do
    grep -Fq "$ignored_path" .gitignore ||
        fail ".gitignore is missing $ignored_path"
done

python_bin="${PYTHON_BIN:-python3}"
"$python_bin" - "$repo_root/renv.lock" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as stream:
    lock = json.load(stream)

expected_repositories = [
    {"Name": "BioC", "URL": "https://bioc-release.r-universe.dev"},
    {"Name": "CRAN", "URL": "https://cloud.r-project.org"},
]
if lock["R"]["Repositories"] != expected_repositories:
    raise SystemExit("renv.lock repository policy is not canonical")

expected_bioconductor_metadata = {
    "Source": "Bioconductor",
    "RemoteType": "bioconductor",
    "Repository": "Bioconductor 3.23",
}
bad = []
for name, package in lock["Packages"].items():
    if not any(
        package.get(field) == expected
        for field, expected in expected_bioconductor_metadata.items()
    ):
        continue
    mismatches = [
        f"{field}={package.get(field)!r}"
        for field, expected in expected_bioconductor_metadata.items()
        if package.get(field) != expected
    ]
    if mismatches:
        bad.append(f"{name} ({', '.join(mismatches)})")
if bad:
    raise SystemExit(
        "Bioconductor package metadata is not canonical: "
        + "; ".join(sorted(bad))
    )
PY
grep -Fq '"BiocVersion":' renv.lock ||
    fail "renv lockfile does not include the Bioconductor release marker"
grep -Fq 'restore_status <- renv::status' scripts/restore_r_environment.R ||
    fail "r-restore does not attest the restored library"
grep -Fq 'lock_recorded_packages <- names(lock$Packages)' \
    scripts/restore_r_environment.R ||
    fail "r-restore does not inventory every lock-recorded package"
grep -Fq 'hydration <- renv::hydrate' scripts/restore_r_environment.R ||
    fail "r-restore does not hydrate lock-recorded external packages"
grep -Fq 'library = restored_library' scripts/restore_r_environment.R ||
    fail "r-restore does not bind hydration and status to the selected library"
grep -Fq 'length(hydration$unresolved) > 0L' \
    scripts/restore_r_environment.R ||
    fail "r-restore does not reject unresolved hydration packages"

for r_entrypoint in \
    scripts/check_r_environment.R scripts/restore_r_environment.R; do
    grep -Fq 'commandArgs(trailingOnly = TRUE)' "$r_entrypoint" ||
        fail "$r_entrypoint does not inspect positional arguments"
    grep -Fq 'does not accept positional arguments.' "$r_entrypoint" ||
        fail "$r_entrypoint no longer rejects every positional argument"
done

grep -Fq 'NORAD_LOCAL_PILOT_R", unset = "0"), "1"' \
    scripts/check_r_environment.R ||
    fail "r-check does not require non-bootstrapping library selection"
if grep -Eq 'renv::(restore|install|hydrate|snapshot)' \
    scripts/check_r_environment.R; then
    fail "r-check contains a dependency-mutating renv operation"
fi

rscript_bin="${RSCRIPT_BIN:-Rscript}"
if resolved_rscript="$(command -v "$rscript_bin" 2>/dev/null)"; then
    r_cli_cwd="$tmp/r-cli-cwd"
    mkdir -p "$r_cli_cwd"
    for r_entrypoint in \
        scripts/check_r_environment.R scripts/restore_r_environment.R; do
        entrypoint_name="$(basename "$r_entrypoint")"
        for argument in --help unexpected-positional-argument; do
            stdout_path="$tmp/${entrypoint_name}.${argument#--}.stdout"
            stderr_path="$tmp/${entrypoint_name}.${argument#--}.stderr"
            before_snapshot="$(find "$r_cli_cwd" -mindepth 1 -print | sort)"
            if (
                cd "$r_cli_cwd"
                R_PROFILE_USER="$tmp/no-r-profile" \
                    R_ENVIRON_USER="$tmp/no-r-environ" \
                    NORAD_USE_RENV=0 \
                    "$resolved_rscript" "$repo_root/$r_entrypoint" "$argument"
            ) >"$stdout_path" 2>"$stderr_path"; then
                fail "$r_entrypoint accepted unsupported argument $argument"
            fi
            test ! -s "$stdout_path" ||
                fail "$r_entrypoint wrote stdout for rejected argument $argument"
            grep -Fq \
                "$entrypoint_name does not accept positional arguments." \
                "$stderr_path" ||
                fail "$r_entrypoint did not report its argument contract"
            if grep -Fqi 'usage' "$stderr_path"; then
                fail "$r_entrypoint unexpectedly implemented help"
            fi
            after_snapshot="$(find "$r_cli_cwd" -mindepth 1 -print | sort)"
            [[ "$after_snapshot" == "$before_snapshot" ]] ||
                fail "$r_entrypoint changed the arbitrary working directory"
        done
    done
else
    printf 'SKIP: Rscript unavailable for direct environment-CLI checks\n'
fi

FAKE_R_LOG="$fake_log" make RSCRIPT_BIN="$fake_rscript" r-restore >/dev/null
FAKE_R_LOG="$fake_log" make \
    RSCRIPT_BIN="$fake_rscript" \
    RENV_LIBRARY="$fake_renv_library" \
    r-check >/dev/null
FAKE_R_LOG="$fake_log" make \
    RSCRIPT_BIN="$fake_rscript" \
    RENV_LIBRARY="$fake_renv_library" \
    NORAD_TEST_FAKE_SCIENTIFIC_CONTEXT_R=1 \
    local-real-r-test >/dev/null

line_count="$(wc -l <"$fake_log" | tr -d ' ')"
[[ "$line_count" -eq 8 ]] ||
    fail "expected eight guarded fake-R invocations, found $line_count"

while IFS= read -r line; do
    [[ "$line" == NORAD_USE_RENV=1$'\t'* ]] ||
        fail "Make target invoked R without NORAD_USE_RENV=1: $line"
    [[ "$line" == *$'\tRENV_SANDBOX=FALSE\t'* ]] ||
        fail "Make target did not disable the pathological local sandbox: $line"
    [[ "$line" == *$'\tRENV_AUTO_SNAPSHOT=FALSE\t'* ]] ||
        fail "Make target allowed automatic lockfile snapshots: $line"
    [[ "$line" == *$'\tRENV_PROJECT='"$repo_root"$'\t'* ]] ||
        fail "Make target invoked R without the repository project: $line"
    [[ "$line" == *$'\tR_PROFILE_USER='"$repo_root/.Rprofile"$'\t'* ]] ||
        fail "Make target invoked R without the guarded profile: $line"
done <"$fake_log"

restore_line="$(sed -n '1p' "$fake_log")"
[[ "$restore_line" == *$'\tNORAD_LOCAL_PILOT_R=0\t'* ]] ||
    fail "r-restore did not select bootstrap-capable operator mode"

tail -n +2 "$fake_log" | while IFS= read -r line; do
    [[ "$line" == *$'\tNORAD_LOCAL_PILOT_R=1\t'* ]] ||
        fail "R check/test did not select non-bootstrapping mode: $line"
    [[ "$line" == *$'\tNORAD_RENV_LIBRARY='"$fake_renv_library"$'\t'* ]] ||
        fail "R check/test did not bind the exact existing library: $line"
    [[ "$line" == *$'\tNORAD_RENV_VERSION=1.2.3\t'* ]] ||
        fail "R check/test did not bind the exact renv version: $line"
done

grep -Fq 'scripts/restore_r_environment.R' "$fake_log" ||
    fail "r-restore did not invoke the restore script"
grep -Fq 'scripts/check_r_environment.R' "$fake_log" ||
    fail "r-check did not invoke the check script"
grep -Fq 'tests/stages/cohort_candidate_preprocessing/test_step_08_vcf_preprocessing.R' "$fake_log" ||
    fail "local-real-r-test did not run Step 08 fixtures"
grep -Fq 'tests/analyses/paired_cmh_candidate_ranking/test_step_09_cmh_editing_site_calling.R' "$fake_log" ||
    fail "local-real-r-test did not run Step 09 fixtures"
[[ "$(grep -Fc 'scientific_context_projection.R --help' "$fake_log")" -eq 1 ]] ||
    fail "local-real-r-test did not log exactly one Step 10 R invocation"

if make \
    RSCRIPT_BIN="$tmp/missing-rscript" \
    RENV_LIBRARY="$fake_renv_library" \
    r-check >"$tmp/missing.out" 2>&1; then
    fail "r-check accepted a missing explicit Rscript executable"
fi

if make RSCRIPT_BIN="$fake_rscript" RENV_LIBRARY= \
    r-check >"$tmp/missing-library.out" 2>&1; then
    fail "r-check accepted a missing explicit RENV_LIBRARY"
fi

printf 'PASS: guarded local R environment contract\n'
