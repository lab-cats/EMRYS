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
printf 'NORAD_USE_RENV=%s\tRENV_SANDBOX=%s\tRENV_AUTO_SNAPSHOT=%s\tRENV_PROJECT=%s\tR_PROFILE_USER=%s\targs=' \
    "${NORAD_USE_RENV:-<unset>}" \
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
    VariantAnnotation GenomicRanges IRanges S4Vectors \
    SummarizedExperiment GenomeInfoDb BiocGenerics rtracklayer; do
    grep -Fq "\"$package_name\":" renv.lock ||
        fail "renv lockfile is missing $package_name"
done

for ignored_path in \
    'renv/library/' 'renv/cache/' 'renv/staging/' '.renv-cache/'; do
    grep -Fq "$ignored_path" .gitignore ||
        fail ".gitignore is missing $ignored_path"
done

grep -Fq 'https://bioc-release.r-universe.dev' renv.lock ||
    fail "renv lockfile does not record the Bioconductor release binary source"
grep -Fq '"BiocVersion":' renv.lock ||
    fail "renv lockfile does not include the Bioconductor release marker"

for r_entrypoint in \
    scripts/check_r_environment.R scripts/restore_r_environment.R; do
    grep -Fq 'commandArgs(trailingOnly = TRUE)' "$r_entrypoint" ||
        fail "$r_entrypoint does not inspect positional arguments"
    grep -Fq 'does not accept positional arguments.' "$r_entrypoint" ||
        fail "$r_entrypoint no longer rejects every positional argument"
done

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
FAKE_R_LOG="$fake_log" make RSCRIPT_BIN="$fake_rscript" r-check >/dev/null
FAKE_R_LOG="$fake_log" make RSCRIPT_BIN="$fake_rscript" local-real-r-test \
    >/dev/null

line_count="$(wc -l <"$fake_log" | tr -d ' ')"
[[ "$line_count" -eq 7 ]] ||
    fail "expected seven guarded fake-R invocations, found $line_count"

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

grep -Fq 'scripts/restore_r_environment.R' "$fake_log" ||
    fail "r-restore did not invoke the restore script"
grep -Fq 'scripts/check_r_environment.R' "$fake_log" ||
    fail "r-check did not invoke the check script"
grep -Fq 'tests/stages/cohort_candidate_preprocessing/test_step_08_vcf_preprocessing.R' "$fake_log" ||
    fail "local-real-r-test did not run Step 08 fixtures"
grep -Fq 'tests/analyses/paired_cmh_candidate_ranking/test_step_09_cmh_editing_site_calling.R' "$fake_log" ||
    fail "local-real-r-test did not run Step 09 fixtures"

if make RSCRIPT_BIN="$tmp/missing-rscript" r-check >"$tmp/missing.out" 2>&1; then
    fail "r-check accepted a missing explicit Rscript executable"
fi

printf 'PASS: guarded local R environment contract\n'
