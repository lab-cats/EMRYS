#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$repo_root"

fail() {
    printf 'FAIL: %s\n' "$*" >&2
    exit 1
}

tmp="$(mktemp -d "${TMPDIR:-/tmp}/emrys-r-contract.XXXXXX")"
trap 'rm -rf "$tmp"' EXIT

fake_rscript="$tmp/Rscript"
fake_log="$tmp/rscript.log"
cat >"$fake_rscript" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
printf 'EMRYS_USE_RENV=%s\tEMRYS_LOCAL_PILOT_R=%s\tEMRYS_RENV_LIBRARY=%s\tEMRYS_RENV_VERSION=%s\tRENV_SANDBOX=%s\tRENV_AUTO_SNAPSHOT=%s\tRENV_PROJECT=%s\tR_PROFILE_USER=%s\targs=' \
    "${EMRYS_USE_RENV:-<unset>}" \
    "${EMRYS_LOCAL_PILOT_R:-<unset>}" \
    "${EMRYS_RENV_LIBRARY:-<unset>}" \
    "${EMRYS_RENV_VERSION:-<unset>}" \
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
printf 'Package: renv\nVersion: 1.2.4\n' \
    >"$fake_renv_library/renv/DESCRIPTION"

# The shared selector uses Bash builtins, so a restricted PATH can distinguish
# an absent optional default from an invalid explicit selection without real R.
selector="$repo_root/tests/tools/select_test_rscript.sh"
selector_bin="$tmp/selector-bin"
empty_path="$tmp/empty-path"
mkdir -p "$selector_bin" "$empty_path"
for name in Rscript Rscript-global Rscript-owner; do
    printf '#!/bin/sh\nexit 0\n' >"$selector_bin/$name"
    chmod +x "$selector_bin/$name"
done
printf 'not executable\n' >"$selector_bin/nonexecutable"
cp "$selector_bin/Rscript-owner" "$tmp/Rscript with spaces"
check_selection() {
    local owner_override="$1" global_override="$2" search_path="$3"
    local expected_status="$4" expected_text="$5" status
    # Expansion belongs to the isolated child shell, not this fixture process.
    # shellcheck disable=SC2016
    if PATH="$search_path" RSCRIPT_BIN_OVERRIDE="$global_override" BASH_ENV='' ENV='' \
        "$BASH" -c 'set -euo pipefail; source "$1" fixture "$2"; printf "SELECTED:%s\n" "$rscript_bin"' \
        _ "$selector" "$owner_override" >"$tmp/selector.out" 2>"$tmp/selector.err"; then
        status=0
    else
        status=$?
    fi
    [[ "$status" -eq "$expected_status" ]] || fail "selector exit $status, expected $expected_status"
    if [[ "$expected_status" -eq 1 ]]; then
        [[ ! -s "$tmp/selector.out" && "$(<"$tmp/selector.err")" == "$expected_text" ]] ||
            fail "selector refusal did not preserve stderr-only diagnostics"
    else
        [[ ! -s "$tmp/selector.err" && "$(<"$tmp/selector.out")" == "$expected_text" ]] ||
            fail "selector returned unexpected success/skip output"
    fi
}
check_selection Rscript-owner Rscript-global "$selector_bin" 0 "SELECTED:$selector_bin/Rscript-owner"
check_selection '' Rscript-global "$selector_bin" 0 "SELECTED:$selector_bin/Rscript-global"
check_selection '' '' "$selector_bin" 0 "SELECTED:$selector_bin/Rscript"
check_selection "$tmp/Rscript with spaces" missing-global "$selector_bin" 0 "SELECTED:$tmp/Rscript with spaces"
check_selection '' "$selector_bin/Rscript-global" "$empty_path" 0 "SELECTED:$selector_bin/Rscript-global"
for bad_selection in missing-name "$tmp/missing-Rscript" "$selector_bin/nonexecutable" "$selector_bin"; do
    check_selection "$bad_selection" Rscript-global "$selector_bin" 1 \
        "ERROR: fixture real-R tests require an executable Rscript: $bad_selection"
done
check_selection '' missing-global "$selector_bin" 1 \
    'ERROR: fixture real-R tests require an executable Rscript: missing-global'
check_selection '' '' "$empty_path" 0 \
    'SKIP: fixture real-R tests require Rscript; no default executable is available.'

# Each wrapper must pass its own override ahead of a deliberately invalid
# global choice and retain its help/fixture handoff. These are fake-R calls.
owner_log="$tmp/owner-selection.log"
for owner_selector in STEP08_TEST_RSCRIPT_BIN STEP09_TEST_RSCRIPT_BIN SCIENTIFIC_CONTEXT_TEST_RSCRIPT_BIN; do
    case "$owner_selector" in
        STEP08_TEST_RSCRIPT_BIN)
            wrapper=tests/stages/cohort_candidate_preprocessing/run_step_08_vcf_preprocessing_tests.sh ;;
        STEP09_TEST_RSCRIPT_BIN)
            wrapper=tests/analyses/paired_cmh_candidate_ranking/run_step_09_cmh_tests.sh ;;
        SCIENTIFIC_CONTEXT_TEST_RSCRIPT_BIN)
            wrapper=tests/analyses/paired_cmh_candidate_ranking/scientific_context_projection/run_scientific_context_projection_tests.sh ;;
    esac
    env STEP08_TEST_RSCRIPT_BIN= STEP09_TEST_RSCRIPT_BIN= SCIENTIFIC_CONTEXT_TEST_RSCRIPT_BIN= \
        "$owner_selector=$fake_rscript" RSCRIPT_BIN_OVERRIDE="$tmp/missing-global" \
        FAKE_R_LOG="$owner_log" EMRYS_TEST_FAKE_SCIENTIFIC_CONTEXT_R=1 \
        "$BASH" "$wrapper" >/dev/null
done
[[ "$(wc -l <"$owner_log" | tr -d ' ')" -eq 5 ]] ||
    fail "owner-selected wrappers did not retain all five fake-R help/fixture calls"

grep -Fq 'identical(use_renv, "1")' src/emrys/.Rprofile ||
    fail ".Rprofile does not guard renv activation"
grep -Fq 'EMRYS_USE_RENV must be exactly 0 or 1' src/emrys/.Rprofile ||
    fail ".Rprofile does not reject invalid activation values"
for legacy_selector in \
    NORAD_USE_RENV NORAD_LOCAL_PILOT_R NORAD_RENV_LIBRARY NORAD_RENV_VERSION; do
    grep -Fq "\"$legacy_selector\"" src/emrys/.Rprofile ||
        fail ".Rprofile does not detect legacy selector $legacy_selector"
done
grep -Fq 'Legacy NORAD R selectors are not accepted by EMRYS' src/emrys/.Rprofile ||
    fail ".Rprofile does not reject legacy R selectors"
if grep -Eq '^source\\("renv/activate\\.R"\\)' src/emrys/.Rprofile; then
    fail ".Rprofile activates renv unconditionally"
fi

grep -Fq '"bioconductor.version": "3.23"' src/emrys/renv/settings.json ||
    fail "renv settings do not pin Bioconductor 3.23"
test -s src/emrys/renv/activate.R || fail "renv activation script is missing"
test -s src/emrys/renv.lock || fail "renv lockfile is missing"
grep -Fq '"Version": "4.6.1"' src/emrys/renv.lock ||
    fail "renv lockfile does not pin R 4.6.1"
grep -Fq '"Version": "3.23"' src/emrys/renv.lock ||
    fail "renv lockfile does not record Bioconductor 3.23"
for package_name in \
    VariantAnnotation Biostrings GenomicRanges IRanges Rsamtools S4Vectors \
    SummarizedExperiment GenomeInfoDb BiocGenerics rtracklayer; do
    grep -Fq "\"$package_name\":" src/emrys/renv.lock ||
        fail "renv lockfile is missing $package_name"
done

for ignored_path in \
    'renv/library/' 'renv/cache/' 'renv/staging/' '.renv-cache/'; do
    grep -Fq "$ignored_path" .gitignore ||
        fail ".gitignore is missing $ignored_path"
done

python_bin="${PYTHON_BIN:-python3}"
"$python_bin" - "$repo_root/src/emrys/renv.lock" <<'PY'
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
grep -Fq '"BiocVersion":' src/emrys/renv.lock ||
    fail "renv lockfile does not include the Bioconductor release marker"
grep -Fq 'restore_status <- renv::status' src/emrys/resources/runtime/restore_r_environment.R ||
    fail "r-restore does not attest the restored library"
grep -Fq 'project = dirname(lockfile)' src/emrys/resources/runtime/restore_r_environment.R ||
    fail "r-restore does not scan installed EMRYS sources for dependencies"
# Match the R member access literally, without shell expansion.
# shellcheck disable=SC2016
grep -Fq 'lock_recorded_packages <- names(lock$Packages)' \
    src/emrys/resources/runtime/restore_r_environment.R ||
    fail "r-restore does not inventory every lock-recorded package"
grep -Fq 'hydration <- renv::hydrate' src/emrys/resources/runtime/restore_r_environment.R ||
    fail "r-restore does not hydrate lock-recorded external packages"
grep -Fq 'library = restored_library' src/emrys/resources/runtime/restore_r_environment.R ||
    fail "r-restore does not bind hydration and status to the selected library"
# Match the R member access literally, without shell expansion.
# shellcheck disable=SC2016
grep -Fq 'length(hydration$unresolved) > 0L' \
    src/emrys/resources/runtime/restore_r_environment.R ||
    fail "r-restore does not reject unresolved hydration packages"

for r_entrypoint in \
    scripts/check_r_environment.R src/emrys/resources/runtime/restore_r_environment.R; do
    grep -Fq 'commandArgs(trailingOnly = TRUE)' "$r_entrypoint" ||
        fail "$r_entrypoint does not inspect positional arguments"
    grep -Fq 'does not accept positional arguments.' "$r_entrypoint" ||
        fail "$r_entrypoint no longer rejects every positional argument"
done

grep -Fq 'EMRYS_LOCAL_PILOT_R", unset = "0"), "1"' \
    scripts/check_r_environment.R ||
    fail "r-check does not require non-bootstrapping library selection"
if grep -Eq 'renv::(restore|install|hydrate|snapshot)' \
    scripts/check_r_environment.R; then
    fail "r-check contains a dependency-mutating renv operation"
fi

rscript_bin="${RSCRIPT_BIN:-Rscript}"
if resolved_rscript="$(command -v "$rscript_bin" 2>/dev/null)"; then
    "$resolved_rscript" --vanilla - "$repo_root/src/emrys" "$tmp" <<'R'
args <- commandArgs(trailingOnly = TRUE)
package <- file.path(normalizePath(args[[2L]]), "package")
project <- file.path(normalizePath(args[[2L]]), "project")
dir.create(file.path(package, "renv"), recursive = TRUE)
dir.create(project)
for (path in c(".Rprofile", "renv.lock", "renv/settings.json")) {
    file.copy(file.path(args[[1L]], path), file.path(package, path))
}
# A fake activation body observes the settings at the actual source boundary;
# it does not bootstrap renv or exercise restoration/package installation.
writeLines(c(
    'stopifnot(Sys.getenv("RENV_CONFIG_AUTO_SNAPSHOT") == "FALSE",',
    '          identical(getOption("renv.config.auto.snapshot"), FALSE))',
    'options(emrys.activation.selected = TRUE)'
), file.path(package, "renv/activate.R"))
snapshot <- function(root) {
    files <- sort(list.files(root, recursive = TRUE, all.files = TRUE,
                             full.names = TRUE))
    tools::md5sum(files)
}
before <- snapshot(package)
Sys.setenv(EMRYS_USE_RENV = "1", EMRYS_LOCAL_PILOT_R = "0",
           RENV_CONFIG_AUTO_SNAPSHOT = "TRUE", RENV_CONFIG_SANDBOX_ENABLED = "TRUE",
           RENV_PROJECT = project, R_PROFILE_USER = file.path(package, ".Rprofile"))
options(renv.config.auto.snapshot = TRUE)
source(Sys.getenv("R_PROFILE_USER"))
stopifnot(isTRUE(getOption("emrys.activation.selected")),
          Sys.getenv("RENV_CONFIG_SYNCHRONIZED_CHECK") == "FALSE",
          Sys.getenv("RENV_PATHS_LOCKFILE") == file.path(package, "renv.lock"),
          Sys.getenv("RENV_PATHS_ROOT") == file.path(project, "renv/state"),
          Sys.getenv("RENV_PATHS_LIBRARY_STAGING") == file.path(project, "renv/staging"),
          file.exists(file.path(project, "renv/settings.json")),
          Sys.getenv("RENV_CONFIG_SANDBOX_ENABLED") == "TRUE",
          identical(before, snapshot(package)))
Sys.setenv(RENV_PROJECT = package)
stopifnot(tryCatch({ source(Sys.getenv("R_PROFILE_USER")); FALSE },
                  error = function(e) grepl("outside the installed", conditionMessage(e))))

# Guarded inspection selects an existing DESCRIPTION-only fixture library;
# no renv namespace is loaded and neither library nor lock/settings may change.
library <- file.path(normalizePath(args[[2L]]), "renv-library")
library_before <- snapshot(library)
project_before <- snapshot(project)
Sys.setenv(EMRYS_LOCAL_PILOT_R = "1", EMRYS_RENV_LIBRARY = library,
           EMRYS_RENV_VERSION = "1.2.4", RENV_CONFIG_AUTO_SNAPSHOT = "TRUE")
options(renv.config.auto.snapshot = TRUE, emrys.activation.selected = FALSE)
source(Sys.getenv("R_PROFILE_USER"))
stopifnot(Sys.getenv("RENV_CONFIG_AUTO_SNAPSHOT") == "FALSE",
          identical(getOption("renv.config.auto.snapshot"), FALSE),
          identical(getOption("emrys.activation.selected"), FALSE),
          identical(normalizePath(.libPaths()[[1L]]), library),
          Sys.getenv("RENV_CONFIG_SANDBOX_ENABLED") == "TRUE",
          identical(before, snapshot(package)),
          identical(project_before, snapshot(project)),
          identical(library_before, snapshot(library)))
empty_library <- file.path(normalizePath(args[[2L]]), "empty-library")
dir.create(empty_library)
Sys.setenv(EMRYS_RENV_LIBRARY = empty_library)
stopifnot(tryCatch({ source(Sys.getenv("R_PROFILE_USER")); FALSE },
                  error = function(e) grepl("no installed renv package", conditionMessage(e))),
          length(snapshot(empty_library)) == 0L,
          identical(before, snapshot(package)),
          identical(project_before, snapshot(project)),
          identical(library_before, snapshot(library)))

# An unselected EMRYS profile must not override unrelated R session policy.
Sys.setenv(EMRYS_USE_RENV = "0", EMRYS_LOCAL_PILOT_R = "0",
           RENV_CONFIG_AUTO_SNAPSHOT = "TRUE")
options(renv.config.auto.snapshot = TRUE)
source(Sys.getenv("R_PROFILE_USER"))
stopifnot(Sys.getenv("RENV_CONFIG_AUTO_SNAPSHOT") == "TRUE",
          identical(getOption("renv.config.auto.snapshot"), TRUE),
          identical(getOption("emrys.activation.selected"), FALSE))
cat("PASS: real-R snapshot guard; fake restoration activation; unchanged inspection bytes\n")
R
    r_cli_cwd="$tmp/r-cli-cwd"
    mkdir -p "$r_cli_cwd"
    for r_entrypoint in \
        scripts/check_r_environment.R src/emrys/resources/runtime/restore_r_environment.R; do
        entrypoint_name="$(basename "$r_entrypoint")"
        for argument in --help unexpected-positional-argument; do
            stdout_path="$tmp/${entrypoint_name}.${argument#--}.stdout"
            stderr_path="$tmp/${entrypoint_name}.${argument#--}.stderr"
            before_snapshot="$(find "$r_cli_cwd" -mindepth 1 -print | sort)"
            if (
                cd "$r_cli_cwd"
                R_PROFILE_USER="$tmp/no-r-profile" \
                    R_ENVIRON_USER="$tmp/no-r-environ" \
                    EMRYS_USE_RENV=0 \
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

fake_restore_project="$tmp/restore-project"
mkdir -p "$fake_restore_project"
FAKE_R_LOG="$fake_log" make RSCRIPT_BIN="$fake_rscript" \
    RENV_PROJECT="$fake_restore_project" r-restore >/dev/null
FAKE_R_LOG="$fake_log" make \
    RSCRIPT_BIN="$fake_rscript" \
    RENV_LIBRARY="$fake_renv_library" \
    r-check >/dev/null
FAKE_R_LOG="$fake_log" make \
    RSCRIPT_BIN="$fake_rscript" \
    RENV_LIBRARY="$fake_renv_library" \
    EMRYS_TEST_FAKE_SCIENTIFIC_CONTEXT_R=1 \
    local-real-r-test >/dev/null

line_count="$(wc -l <"$fake_log" | tr -d ' ')"
[[ "$line_count" -eq 7 ]] ||
    fail "expected seven guarded fake-R invocations, found $line_count"

while IFS= read -r line; do
    [[ "$line" == EMRYS_USE_RENV=1$'\t'* ]] ||
        fail "Make target invoked R without EMRYS_USE_RENV=1: $line"
    [[ "$line" == *$'\tRENV_SANDBOX=FALSE\t'* ]] ||
        fail "Make target did not disable the pathological local sandbox: $line"
    [[ "$line" == *$'\tRENV_AUTO_SNAPSHOT=FALSE\t'* ]] ||
        fail "Make target allowed automatic lockfile snapshots: $line"
    [[ "$line" == *$'\tR_PROFILE_USER='"$repo_root/src/emrys/.Rprofile"$'\t'* ]] ||
        fail "Make target invoked R without the guarded profile: $line"
done <"$fake_log"

restore_line="$(sed -n '1p' "$fake_log")"
[[ "$restore_line" == *$'\tEMRYS_LOCAL_PILOT_R=0\t'* ]] ||
    fail "r-restore did not select bootstrap-capable operator mode"
[[ "$restore_line" == *$'\tRENV_PROJECT='"$fake_restore_project"$'\t'* ]] ||
    fail "r-restore did not select the external mutable project"

tail -n +2 "$fake_log" | while IFS= read -r line; do
    [[ "$line" == *$'\tRENV_PROJECT='"$repo_root/src/emrys"$'\t'* ]] ||
        fail "Make target invoked guarded R without the installed package project: $line"
    [[ "$line" == *$'\tEMRYS_LOCAL_PILOT_R=1\t'* ]] ||
        fail "R check/test did not select non-bootstrapping mode: $line"
    [[ "$line" == *$'\tEMRYS_RENV_LIBRARY='"$fake_renv_library"$'\t'* ]] ||
        fail "R check/test did not bind the exact existing library: $line"
    [[ "$line" == *$'\tEMRYS_RENV_VERSION=1.2.4\t'* ]] ||
        fail "R check/test did not bind the exact renv version: $line"
done

grep -Fq 'src/emrys/resources/runtime/restore_r_environment.R' "$fake_log" ||
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
