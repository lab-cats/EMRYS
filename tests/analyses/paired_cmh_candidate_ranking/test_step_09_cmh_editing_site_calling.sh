#!/usr/bin/env bash
# Local Step 09 wrapper tests with a fake Rscript implementation.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
script="$repo_root/src/emrys/analyses/paired_cmh_candidate_ranking/step_09_cmh_editing_site_calling.sh"
job="$repo_root/src/emrys/analyses/paired_cmh_candidate_ranking/step_09_cmh_editing_site_calling.slurm"
unset EMRYS_RUN_TOKEN
export EMRYS_SHA256_PYTHON="$repo_root/.venv/bin/python"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

fail() {
    printf 'FAIL: %s\n' "$*" >&2
    exit 1
}

expect_fail() {
    local pattern="$1"
    shift
    if "$@" >"$tmp/fail.out" 2>"$tmp/fail.err"; then
        fail "command unexpectedly succeeded: $*"
    fi
    grep -q "$pattern" "$tmp/fail.err" ||
        fail "failure did not contain '$pattern': $(cat "$tmp/fail.err")"
}

sha256() {
    shasum -a 256 "$1" | awk '{print $1}'
}

assert_file_equals() {
    local path="$1"
    local expected="$2"
    [[ -f "$path" ]] || fail "expected file does not exist: $path"
    [[ "$(<"$path")" == "$expected" ]] ||
        fail "unexpected file content: $path"
}

assert_no_finals() {
    local output_root="$1"
    local analysis="$2"
    local output_dir="$output_root/$analysis"
    local suffix
    for suffix in \
        cmh_all_sites.tsv \
        cmh_significant_sites.tsv \
        cmh_summary.tsv \
        mutation_spectrum.tsv \
        mutation_spectrum.pdf \
        depth_delta.pdf
    do
        [[ ! -e "$output_dir/$analysis.$suffix" ]] ||
            fail "unexpected stable output remains: $output_dir/$analysis.$suffix"
    done
}

assert_no_scratch() {
    local output_root="$1"
    local analysis="$2"
    local output_dir="$output_root/$analysis"
    local path
    for path in \
        "$output_dir"/."$analysis".step09.* \
        "$output_dir"/."$analysis".*.previous
    do
        [[ ! -e "$path" ]] || fail "Step 09 scratch path remains: $path"
    done
}

seed_prior_outputs() {
    local output_root="$1"
    local analysis="$2"
    local marker="$3"
    local output_dir="$output_root/$analysis"
    local suffix
    mkdir -p "$output_dir"
    for suffix in \
        cmh_all_sites.tsv \
        cmh_significant_sites.tsv \
        cmh_summary.tsv \
        mutation_spectrum.tsv \
        mutation_spectrum.pdf \
        depth_delta.pdf
    do
        printf '%s %s\n' "$marker" "$suffix" > "$output_dir/$analysis.$suffix"
    done
}

hash_output_set() {
    local output_root="$1"
    local analysis="$2"
    local output_dir="$output_root/$analysis"
    local suffix
    for suffix in \
        cmh_all_sites.tsv \
        cmh_significant_sites.tsv \
        cmh_summary.tsv \
        mutation_spectrum.tsv \
        mutation_spectrum.pdf \
        depth_delta.pdf
    do
        sha256 "$output_dir/$analysis.$suffix"
    done
}

assert_arg_pair() {
    local log="$1"
    local option="$2"
    local expected="$3"
    awk -v option="$option" -v expected="$expected" '
        previous == option && $0 == expected { found = 1 }
        { previous = $0 }
        END { exit !found }
    ' "$log" || fail "fake R arguments omitted $option $expected"
}

assert_header_omits() {
    local path="$1"
    shift
    local header
    local field
    IFS= read -r header < "$path"
    for field in "$@"; do
        if printf '%s\n' "$header" | tr '\t' '\n' | grep -Fqx "$field"; then
            fail "header unexpectedly records $field: $path"
        fi
    done
}

mkdir -p "$tmp/bin" "$tmp/step08/cohort" "$tmp/output"
sample_manifest="$tmp/samples.tsv"
partition_manifest="$tmp/partitions.tsv"
sites="$tmp/step08/cohort/cohort.step08_sites.tsv"
inputs="$tmp/step08/cohort/cohort.step08_inputs.tsv"

printf '%s\n' \
    $'sample_id\tr1_fastq\tr2_fastq\tstrandedness\tcondition\treplicate' \
    $'ABE_EV_2\tABE_EV_2_R1\tABE_EV_2_R2\treverse\tEV\t2' \
    $'ABE_PUM1_2\tABE_PUM1_2_R1\tABE_PUM1_2_R2\treverse\tPUM1\t2' \
    $'ABE_EV_3\tABE_EV_3_R1\tABE_EV_3_R2\treverse\tEV\t3' \
    $'ABE_PUM1_3\tABE_PUM1_3_R1\tABE_PUM1_3_R2\treverse\tPUM1\t3' \
    $'ABE_EV4\tABE_EV4_R1\tABE_EV4_R2\treverse\tEV\t4' \
    $'ABE_PUM1_4\tABE_PUM1_4_R1\tABE_PUM1_4_R2\treverse\tPUM1\t4' > "$sample_manifest"
printf '%s\n' \
    $'partition_id\tselector_type\tselector_value' \
    $'p1\tregion\t1:1-100' > "$partition_manifest"

sample_hash="$(sha256 "$sample_manifest")"
partition_hash="$(sha256 "$partition_manifest")"
sites_header=$'partition_id\tcandidate_id\torientation\tchromosome\tposition\talt_index\tgenomic_ref\tgenomic_alt\trna_ref\trna_alt\tannotation_strand\tgene_ids\ttranscript_ids\tis_cds\tis_five_prime_utr\tis_three_prime_utr\tis_exon\tis_intron\tqual\tfilter\tinfo_alt_depth\torientation_policy\tDP__ABE_EV_2\tDP__ABE_PUM1_2\tDP__ABE_EV_3\tDP__ABE_PUM1_3\tDP__ABE_EV4\tDP__ABE_PUM1_4\tAD__ABE_EV_2\tAD__ABE_PUM1_2\tAD__ABE_EV_3\tAD__ABE_PUM1_3\tAD__ABE_EV4\tAD__ABE_PUM1_4\tAF__ABE_EV_2\tAF__ABE_PUM1_2\tAF__ABE_EV_3\tAF__ABE_PUM1_3\tAF__ABE_EV4\tAF__ABE_PUM1_4'
printf '%s\n' "$sites_header" \
    $'p1\tFWD_like|1|10|T>C\tFWD_like\t1\t10\t1\tT\tC\tA\tG\t+\tg1\tt1\tTRUE\tFALSE\tFALSE\tTRUE\tFALSE\t60\tPASS\t20\tlegacy_provisional_v1\t100\t100\t100\t100\t100\t100\t10\t30\t20\t40\t15\t35\t0.1\t0.3\t0.2\t0.4\t0.15\t0.35' \
    $'p1\tREV_like|1|20|C>T\tREV_like\t1\t20\t1\tC\tT\tC\tT\t-\tg2\tt2\tFALSE\tFALSE\tFALSE\tTRUE\tFALSE\t60\tPASS\t10\tlegacy_provisional_v1\t100\t100\t100\t100\t100\t100\t5\t5\t5\t5\t5\t5\t0.05\t0.05\t0.05\t0.05\t0.05\t0.05' > "$sites"

receipt_header=$'cohort_id\tpartition_id\tselector_type\tselector_value\torientation\tstep07_receipt_path\tstep07_receipt_sha256\tvcf_path\tvcf_sha256\tsample_manifest_sha256\tpartition_manifest_sha256\tannotation_gtf\tannotation_gtf_sha256\tsample_count\tdeclared_vcf_record_count\tobserved_vcf_record_count\tobserved_alt_allele_count\tsupported_snv_count\tskipped_symbolic_count\tskipped_non_snv_count\tpublished_candidate_count\torientation_policy'
hash64="$(printf 'a%.0s' {1..64})"
printf '%s\n' "$receipt_header" \
    $'cohort\tp1\tregion\t1:1-100\tFWD_like\tlegacy.receipt\t'"$hash64"$'\tlegacy.fwd.vcf\t'"$hash64"$'\t'"$sample_hash"$'\t'"$partition_hash"$'\tgenome.gtf\t'"$hash64"$'\t6\t1\t1\t1\t1\t0\t0\t1\tlegacy_provisional_v1' \
    $'cohort\tp1\tregion\t1:1-100\tREV_like\tlegacy.receipt\t'"$hash64"$'\tlegacy.rev.vcf\t'"$hash64"$'\t'"$sample_hash"$'\t'"$partition_hash"$'\tgenome.gtf\t'"$hash64"$'\t6\t1\t1\t1\t1\t0\t0\t1\tlegacy_provisional_v1' > "$inputs"

copy_fixture() {
    local destination="$1"
    mkdir -p "$destination/step08/cohort" "$destination/output"
    cp "$sample_manifest" "$destination/samples.tsv"
    cp "$partition_manifest" "$destination/partitions.tsv"
    cp "$sites" "$destination/step08/cohort/cohort.step08_sites.tsv"
    cp "$inputs" "$destination/step08/cohort/cohort.step08_inputs.tsv"
}

add_background_sample() {
    local fixture="$1"
    local background_sample="NO_DOX_1"
    local manifest="$fixture/samples.tsv"
    local fixture_sites="$fixture/step08/cohort/cohort.step08_sites.tsv"
    local fixture_inputs="$fixture/step08/cohort/cohort.step08_inputs.tsv"
    local rewritten="$fixture/rewritten.tsv"
    local updated_sample_hash

    printf '%s\n' \
        $'NO_DOX_1\tNO_DOX_1_R1\tNO_DOX_1_R2\treverse\tNODOX\t1' \
        >> "$manifest"

    awk -F '\t' -v OFS='\t' -v sample="$background_sample" '
        {
            for (i = 1; i <= 28; i++) {
                printf "%s%s", (i == 1 ? "" : OFS), $i
            }
            printf OFS "%s", (NR == 1 ? "DP__" sample : "100")
            for (i = 29; i <= 34; i++) printf OFS "%s", $i
            printf OFS "%s", (NR == 1 ? "AD__" sample : "5")
            for (i = 35; i <= 40; i++) printf OFS "%s", $i
            printf OFS "%s\n", (NR == 1 ? "AF__" sample : "0.05")
        }
    ' "$fixture_sites" > "$rewritten"
    mv "$rewritten" "$fixture_sites"

    updated_sample_hash="$(sha256 "$manifest")"
    awk -F '\t' -v OFS='\t' -v sample_hash="$updated_sample_hash" '
        NR == 1 { print; next }
        { $10 = sample_hash; $14 = 7; print }
    ' "$fixture_inputs" > "$rewritten"
    mv "$rewritten" "$fixture_inputs"
}

fake_r="$tmp/bin/fake-r"
apply_marker="$tmp/r-invoked"
cat > "$fake_r" <<'FAKE_R'
#!/usr/bin/env bash
set -euo pipefail
if [[ -n "${FAKE_R_ARGS_LOG:-}" ]]; then
    printf '%s\n' "$@" > "$FAKE_R_ARGS_LOG"
fi
r_script_path="$1"
shift
control_condition="EV"
treatment_condition="PUM1"
background_condition=""
rna_ref="A"
rna_alt="G"
min_sample_dp="1"
mean_dp_threshold="50"
fdr_threshold="0.05"
common_or_threshold="1.2"
absolute_difference_threshold="0.005"
background_max_fraction="0.01"
while [[ "$#" -gt 0 ]]; do
    key="${1#--}"
    value="$2"
    case "$key" in
        analysis-id) analysis_id="$value" ;;
        cohort-id) cohort_id="$value" ;;
        sample-manifest) sample_manifest="$value" ;;
        partition-manifest) partition_manifest="$value" ;;
        sample-manifest-sha256) sample_hash="$value" ;;
        partition-manifest-sha256) partition_hash="$value" ;;
        step08-sites) step08_sites="$value" ;;
        step08-inputs) step08_inputs="$value" ;;
        step08-sites-sha256) sites_hash="$value" ;;
        step08-inputs-sha256) inputs_hash="$value" ;;
        control-condition) control_condition="$value" ;;
        treatment-condition) treatment_condition="$value" ;;
        background-condition) background_condition="$value" ;;
        rna-ref) rna_ref="$value" ;;
        rna-alt) rna_alt="$value" ;;
        min-sample-dp) min_sample_dp="$value" ;;
        mean-dp-threshold) mean_dp_threshold="$value" ;;
        fdr-threshold) fdr_threshold="$value" ;;
        common-or-threshold) common_or_threshold="$value" ;;
        absolute-difference-threshold) absolute_difference_threshold="$value" ;;
        background-max-fraction) background_max_fraction="$value" ;;
        all-sites-output) all_output="$value" ;;
        significant-sites-output) significant_output="$value" ;;
        summary-output) summary_output="$value" ;;
        mutation-spectrum-output) mutation_output="$value" ;;
        mutation-spectrum-pdf-output) mutation_pdf="$value" ;;
        depth-delta-pdf-output) depth_pdf="$value" ;;
    esac
    shift 2
done
printf invoked > "${FAKE_R_MARKER:?}"
if [[ -n "${FAKE_R_BARRIER_MARKER:-}" ]]; then
    : > "$FAKE_R_BARRIER_MARKER"
    while [[ ! -e "${FAKE_R_BARRIER_RELEASE:?}" ]]; do
        sleep 0.01
    done
fi
if [[ "${FAKE_R_MODE:-success}" == "fail" ]]; then
    exit 73
fi
samples=()
while IFS=$'\t' read -r sample; do samples+=("$sample"); done < <(
    awk -F '\t' 'NR == 1 {for(i=1;i<=NF;i++) if($i=="sample_id") c=i; next} {print $c}' "$sample_manifest"
)
sample_count="${#samples[@]}"
replicate_count="$(awk -F '\t' -v control="$control_condition" '
    NR == 1 {
        for (i = 1; i <= NF; i++) {
            if ($i == "condition") condition_col = i
            if ($i == "replicate") replicate_col = i
        }
        next
    }
    $condition_col == control && !seen[$replicate_col]++ { count++ }
    END { print count + 0 }
' "$sample_manifest")"
background_label="${background_condition:-NA}"
background_indices_csv=""
if [[ -n "$background_condition" ]]; then
    while IFS= read -r background_index; do
        [[ -z "$background_indices_csv" ]] || background_indices_csv+=","
        background_indices_csv+="$background_index"
    done < <(
        awk -F '\t' -v background="$background_condition" '
            NR == 1 {
                for (i = 1; i <= NF; i++) {
                    if ($i == "condition") condition_col = i
                }
                next
            }
            {
                sample_index++
                if ($condition_col == background) print sample_index
            }
        ' "$sample_manifest"
    )
fi
candidate_count="$(awk 'END { print (NR > 0 ? NR - 1 : 0) }' "$step08_sites")"
target_count="$(awk -F '\t' -v ref="$rna_ref" -v alt="$rna_alt" '
    NR > 1 && $9 == ref && $10 == alt { count++ }
    END { print count + 0 }
' "$step08_sites")"
not_target_count=$((candidate_count - target_count))
header=$'analysis_id\tpartition_id\tcandidate_id\torientation\tchromosome\tposition\talt_index\tgenomic_ref\tgenomic_alt\trna_ref\trna_alt\tannotation_strand\tgene_ids\ttranscript_ids\tis_cds\tis_five_prime_utr\tis_three_prime_utr\tis_exon\tis_intron\tqual\tfilter\tinfo_alt_depth\torientation_policy\tcontrol_condition\ttreatment_condition\ttarget_rna_change\treplicate_count\ttest_status\tcall_status\tbackground_condition\tbackground_status\tmin_analysis_dp\tmean_analysis_dp\tmean_control_af\tmean_treatment_af\ttreatment_control_difference\tmax_background_af\tcmh_statistic\tcmh_degrees_freedom\tcmh_p_value\tcmh_fdr_bh\tcommon_odds_ratio'
for s in "${samples[@]}"; do header+=$'\t'"DP__$s"; done
for s in "${samples[@]}"; do header+=$'\t'"AD__$s"; done
for s in "${samples[@]}"; do header+=$'\t'"AF__$s"; done
printf '%s\n' "$header" > "$all_output"
awk -F '\t' -v OFS='\t' \
    -v analysis="$analysis_id" \
    -v control="$control_condition" \
    -v treatment="$treatment_condition" \
    -v replicates="$replicate_count" \
    -v background="$background_label" \
    -v background_indices_csv="$background_indices_csv" \
    -v background_threshold="$background_max_fraction" \
    -v min_dp="$min_sample_dp" \
    -v sample_total="$sample_count" \
    -v target_ref="$rna_ref" \
    -v target_alt="$rna_alt" \
    -v target_change="$rna_ref>$rna_alt" '
BEGIN {
 if (background != "NA") {
  background_count=split(background_indices_csv, background_indices, ",")
 }
}
NR > 1 {
 is_target=($9==target_ref && $10==target_alt)
 test_status=(is_target ? "tested" : "not_target_change")
 background_status="disabled"
 max_background="NA"
 if (background != "NA") {
  background_missing=0
  background_low=0
  background_all_positive=1
  background_all_below=1
  background_max=-1
  for (background_number=1; background_number<=background_count; background_number++) {
   sample_index=background_indices[background_number]
   background_dp=$(22+sample_index)
   background_ad=$(22+sample_total+sample_index)
   if (background_dp=="NA" || background_ad=="NA") {
    background_missing=1
    continue
   }
   if (background_dp+0 < min_dp+0) background_low=1
   if (background_dp+0 <= 0) {
    background_all_positive=0
    continue
   }
   background_af=(background_ad+0)/(background_dp+0)
   if (background_af > background_max) background_max=background_af
   if (!(background_af < background_threshold+0)) background_all_below=0
  }
  if (background_missing) {
   background_status="missing_counts"
  } else if (background_low) {
   background_status="low_coverage"
   if (background_all_positive) max_background=background_max
  } else {
   background_status=(background_all_below ? "pass" : "fail_fraction")
   max_background=background_max
  }
 }
 call="not_tested"
 if (is_target) {
  call=((background_status=="disabled" || background_status=="pass") ? "significant_up" : "background_not_passed")
 }
 printf "%s", analysis
 for(i=1;i<=22;i++) printf OFS "%s", $i
 printf OFS control OFS treatment OFS target_change OFS replicates OFS test_status OFS call OFS background OFS background_status OFS "100" OFS "100" OFS "0.15" OFS "0.35" OFS "0.2" OFS max_background
 if (is_target) {
     printf OFS "10" OFS "1" OFS "0.001" OFS "0.002" OFS "3"
 } else {
     for (statistic = 1; statistic <= 5; statistic++) printf OFS "NA"
 }
 for(i=23;i<=NF;i++) printf OFS "%s", $i
 printf "\n"
}' "$step08_sites" >> "$all_output"
awk -F '\t' 'NR == 1 || $29 == "significant_up" ||
    $29 == "significant_down"' "$all_output" > "$significant_output"
status_counts="$(awk -F '\t' '
    NR > 1 {
        if ($28 == "tested") tested++
        else if ($28 == "not_target_change") not_target++
        else if ($28 == "missing_counts") missing++
        else if ($28 == "low_coverage") low++
        else if ($28 == "degenerate_table") degenerate++
        if ($29 == "below_mean_dp") below_mean++
        else if ($29 == "background_not_passed") background_failed++
        else if ($29 == "fdr_not_met") fdr_failed++
        else if ($29 == "effect_not_met") effect_failed++
        else if ($29 == "significant_up") up++
        else if ($29 == "significant_down") down++
    }
    END {
        print tested+0, not_target+0, missing+0, low+0, degenerate+0,
            below_mean+0, background_failed+0, fdr_failed+0,
            effect_failed+0, up+0, down+0
    }
' "$all_output")"
read -r tested_count not_target_count missing_count low_count \
    degenerate_count below_mean_count background_failed_count \
    fdr_failed_count effect_failed_count significant_up_count \
    significant_down_count <<< "$status_counts"
summary_header=$'analysis_id\tcohort_id\tcontrol_condition\ttreatment_condition\tbackground_condition\ttarget_rna_change\treplicate_count\tsample_count\tcandidate_count\ttarget_candidate_count\tsuccessfully_tested_count\tnot_target_change_count\tmissing_counts_count\tlow_coverage_count\tdegenerate_table_count\tbelow_mean_dp_count\tbackground_not_passed_count\tfdr_not_met_count\teffect_not_met_count\tsignificant_up_count\tsignificant_down_count\tsample_manifest_path\tsample_manifest_sha256\tpartition_manifest_path\tpartition_manifest_sha256\tstep08_sites_path\tstep08_sites_sha256\tstep08_inputs_path\tstep08_inputs_sha256\tmin_sample_dp\tmean_dp_threshold\tfdr_threshold\tcommon_or_threshold\tabsolute_difference_threshold\tbackground_max_fraction\tmultiple_testing_method\tcmh_alternative\tcontinuity_correction\torientation_policy'
printf '%s\n' "$summary_header" > "$summary_output"
printf '%s\t%s\t%s\t%s\t%s\t%s>%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\tBH\ttwo.sided\tTRUE\tlegacy_provisional_v1\n' \
 "$analysis_id" "$cohort_id" "$control_condition" "$treatment_condition" \
 "$background_label" "$rna_ref" "$rna_alt" "$replicate_count" "$sample_count" \
 "$candidate_count" "$target_count" "$tested_count" "$not_target_count" \
 "$missing_count" "$low_count" "$degenerate_count" "$below_mean_count" \
 "$background_failed_count" "$fdr_failed_count" "$effect_failed_count" \
 "$significant_up_count" "$significant_down_count" \
 "$sample_manifest" "$sample_hash" \
 "$partition_manifest" "$partition_hash" "$step08_sites" \
 "$sites_hash" "$step08_inputs" "$inputs_hash" \
 "$min_sample_dp" "$mean_dp_threshold" "$fdr_threshold" \
 "$common_or_threshold" "$absolute_difference_threshold" \
 "$background_max_fraction" >> "$summary_output"
printf '%s\n' $'analysis_id\trna_ref\trna_alt\tmutation_type\tcandidate_count\tcandidate_fraction\tsuccessfully_tested_count\tsignificant_up_count\tsignificant_down_count' > "$mutation_output"
for mut in A\>C A\>G A\>T C\>A C\>G C\>T G\>A G\>C G\>T T\>A T\>C T\>G; do
 count="$(awk -F '\t' -v mutation="$mut" '
     NR > 1 && ($9 ">" $10) == mutation { count++ }
     END { print count + 0 }
 ' "$step08_sites")"
 read -r tested significant_up significant_down < <(
     awk -F '\t' -v mutation="$mut" '
         NR > 1 && ($10 ">" $11) == mutation {
             if ($28 == "tested") tested++
             if ($29 == "significant_up") up++
             if ($29 == "significant_down") down++
         }
         END { print tested+0, up+0, down+0 }
     ' "$all_output"
 )
 fraction="$(awk -v count="$count" -v total="$candidate_count" '
     BEGIN { printf "%.17g", (total == 0 ? 0 : count / total) }
 ')"
 printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
     "$analysis_id" "${mut:0:1}" "${mut:2:1}" "$mut" "$count" \
     "$fraction" "$tested" "$significant_up" "$significant_down" \
     >> "$mutation_output"
done
for pdf in "$mutation_pdf" "$depth_pdf"; do
 printf '%s\n%s\n' '%PDF-1.4' '%%EOF' > "$pdf"
done
case "${FAKE_R_MODE:-success}" in
    success) ;;
    omit_summary) rm -f "$summary_output" ;;
    bad_pdf) printf 'not a PDF\n' > "$mutation_pdf" ;;
    mutate_sample) printf '\n' >> "$sample_manifest" ;;
    mutate_partition) printf '\n' >> "$partition_manifest" ;;
    mutate_sites) printf '\n' >> "$step08_sites" ;;
    mutate_inputs) printf '\n' >> "$step08_inputs" ;;
    mutate_r_script)
        printf '\n# changed while fake R was running\n' >> "$r_script_path"
        ;;
    tamper_background_max)
        awk -F '\t' -v OFS='\t' '
            NR == 2 { $37 = "0.04" }
            { print }
        ' "$all_output" > "$all_output.tampered"
        mv "$all_output.tampered" "$all_output"
        ;;
    tamper_background_status)
        awk -F '\t' -v OFS='\t' '
            NR == 2 { $31 = "pass" }
            { print }
        ' "$all_output" > "$all_output.tampered"
        mv "$all_output.tampered" "$all_output"
        ;;
    *) exit 74 ;;
esac
FAKE_R
chmod +x "$fake_r"

cat > "$tmp/bin/module" <<'FAKE_MODULE'
#!/usr/bin/env bash
exit 0
FAKE_MODULE
chmod +x "$tmp/bin/module"

cat > "$tmp/bin/mv" <<'FAKE_MV'
#!/usr/bin/env bash
set -euo pipefail
destination="${!#}"
source="${1:-}"

if [[ -n "${FAKE_MV_LOG:-}" ]]; then
    printf '%s\t%s\n' "$source" "$destination" >> "$FAKE_MV_LOG"
fi

if [[ -n "${FAKE_MV_FAIL_ONCE_DEST:-}" &&
      "$destination" == "$FAKE_MV_FAIL_ONCE_DEST" &&
      ! -e "${FAKE_MV_FAIL_MARKER:?}" ]]; then
    : > "$FAKE_MV_FAIL_MARKER"
    printf 'forced fake mv failure for %s\n' "$destination" >&2
    exit 91
fi

if [[ -n "${FAKE_MV_FAIL_RESTORE_SOURCE:-}" &&
      "${1:-}" == "$FAKE_MV_FAIL_RESTORE_SOURCE" &&
      ! -e "${FAKE_MV_RESTORE_FAIL_MARKER:?}" ]]; then
    : > "$FAKE_MV_RESTORE_FAIL_MARKER"
    printf 'forced fake restore failure for %s\n' "${1:-}" >&2
    exit 92
fi

if [[ -n "${FAKE_MV_CORRUPT_ONCE_DEST:-}" &&
      "$destination" == "$FAKE_MV_CORRUPT_ONCE_DEST" &&
      ! -e "${FAKE_MV_CORRUPT_MARKER:?}" ]]; then
    /bin/mv "$@"
    : > "$FAKE_MV_CORRUPT_MARKER"
    printf 'valid-looking post-publication padding\n' >> "$destination"
    exit 0
fi

if [[ -n "${FAKE_MV_BARRIER_DEST:-}" &&
      "$destination" == "$FAKE_MV_BARRIER_DEST" ]]; then
    /bin/mv "$@"
    : > "${FAKE_MV_BARRIER_MARKER:?}"
    while [[ ! -e "${FAKE_MV_BARRIER_RELEASE:?}" ]]; do
        sleep 0.01
    done
    exit 0
fi

exec /bin/mv "$@"
FAKE_MV
chmod +x "$tmp/bin/mv"

base=(
    "$script"
    --analysis-id analysis
    --cohort-id cohort
    --sample-manifest "$sample_manifest"
    --partition-manifest "$partition_manifest"
    --step08-root "$tmp/step08"
    --output-root "$tmp/output"
    --rscript-bin "$fake_r"
    --r-script "$repo_root/src/emrys/analyses/paired_cmh_candidate_ranking/step_09_cmh_editing_site_calling.R"
)

run_step09() {
    local fixture="$1"
    local analysis="$2"
    shift 2
    "$script" --analysis-id "$analysis" --cohort-id cohort \
        --sample-manifest "$fixture/samples.tsv" \
        --partition-manifest "$fixture/partitions.tsv" \
        --step08-root "$fixture/step08" \
        --output-root "$fixture/output" \
        --rscript-bin "${STEP09_RSCRIPT_BIN:-$fake_r}" \
        --r-script "${STEP09_R_PROGRAM:-$repo_root/src/emrys/analyses/paired_cmh_candidate_ranking/step_09_cmh_editing_site_calling.R}" \
        "$@"
}

assert_preflight_preserved() {
    local fixture="$1"
    local analysis="$2"
    assert_file_equals "$fixture/output/unrelated.txt" "preflight sentinel"
    [[ ! -e "$fixture/output/$analysis" ]] ||
        fail "runtime preflight mutated the analysis output: $fixture/output/$analysis"
    [[ "$(find "$fixture/output" -mindepth 1 -print | wc -l | tr -d ' ')" == "1" ]] ||
        fail "runtime preflight mutated the output root: $fixture/output"
}

run_input_mutation_case() {
    local mode="$1"
    local analysis="$2"
    local diagnostic="$3"
    local fixture="$tmp/$analysis"
    local marker="$fixture/fake-r.invoked"
    copy_fixture "$fixture"
    mkdir -p "$fixture/output/$analysis"
    printf 'unrelated bytes\n' > "$fixture/output/$analysis/unrelated.txt"
    FAKE_R_MARKER="$marker" FAKE_R_MODE="$mode" \
        expect_fail "$diagnostic" run_step09 "$fixture" "$analysis" --execute
    [[ -e "$marker" ]] || fail "$mode did not invoke fake R"
    assert_no_finals "$fixture/output" "$analysis"
    assert_no_scratch "$fixture/output" "$analysis"
    assert_file_equals "$fixture/output/$analysis/unrelated.txt" "unrelated bytes"
}

missing_rscript="$tmp/missing-rscript"
copy_fixture "$missing_rscript"
printf 'preflight sentinel\n' > "$missing_rscript/output/unrelated.txt"
expect_fail "Rscript does not exist: $missing_rscript/bin/missing-rscript" \
    "$script" --analysis-id missing-rscript --cohort-id cohort \
    --sample-manifest "$missing_rscript/samples.tsv" \
    --partition-manifest "$missing_rscript/partitions.tsv" \
    --step08-root "$missing_rscript/step08" \
    --output-root "$missing_rscript/output" \
    --rscript-bin "$missing_rscript/bin/missing-rscript" \
    --r-script "$repo_root/src/emrys/analyses/paired_cmh_candidate_ranking/step_09_cmh_editing_site_calling.R"
assert_preflight_preserved "$missing_rscript" missing-rscript

nonexecutable_rscript="$tmp/nonexecutable-rscript"
copy_fixture "$nonexecutable_rscript"
mkdir -p "$nonexecutable_rscript/bin"
printf '#!/usr/bin/env bash\nexit 0\n' > "$nonexecutable_rscript/bin/nonexecutable-rscript"
chmod 0644 "$nonexecutable_rscript/bin/nonexecutable-rscript"
printf 'preflight sentinel\n' > "$nonexecutable_rscript/output/unrelated.txt"
expect_fail "Rscript exists but is not executable: $nonexecutable_rscript/bin/nonexecutable-rscript" \
    "$script" --analysis-id nonexecutable-rscript --cohort-id cohort \
    --sample-manifest "$nonexecutable_rscript/samples.tsv" \
    --partition-manifest "$nonexecutable_rscript/partitions.tsv" \
    --step08-root "$nonexecutable_rscript/step08" \
    --output-root "$nonexecutable_rscript/output" \
    --rscript-bin "$nonexecutable_rscript/bin/nonexecutable-rscript" \
    --r-script "$repo_root/src/emrys/analyses/paired_cmh_candidate_ranking/step_09_cmh_editing_site_calling.R"
assert_preflight_preserved "$nonexecutable_rscript" nonexecutable-rscript

missing_r_program="$tmp/missing-r-program"
copy_fixture "$missing_r_program"
printf 'preflight sentinel\n' > "$missing_r_program/output/unrelated.txt"
expect_fail "Step 09 R script does not exist or is empty: $missing_r_program/missing.R" \
    "$script" --analysis-id missing-r-program --cohort-id cohort \
    --sample-manifest "$missing_r_program/samples.tsv" \
    --partition-manifest "$missing_r_program/partitions.tsv" \
    --step08-root "$missing_r_program/step08" \
    --output-root "$missing_r_program/output" \
    --rscript-bin "$fake_r" \
    --r-script "$missing_r_program/missing.R"
assert_preflight_preserved "$missing_r_program" missing-r-program

basename_rscript="$tmp/basename-rscript"
copy_fixture "$basename_rscript"
mkdir -p "$basename_rscript/bin" "$basename_rscript/cwd"
cp "$fake_r" "$basename_rscript/bin/fake-r-basename"
basename_marker="$basename_rscript/fake-r.invoked"
(
    cd "$basename_rscript/cwd"
    env \
        PATH="$basename_rscript/bin:$PATH" \
        FAKE_R_MARKER="$basename_marker" \
        "$script" --analysis-id basename-rscript --cohort-id cohort \
        --sample-manifest "$basename_rscript/samples.tsv" \
        --partition-manifest "$basename_rscript/partitions.tsv" \
        --step08-root "$basename_rscript/step08" \
        --output-root "$basename_rscript/output" \
        --rscript-bin fake-r-basename \
        --r-script "$repo_root/src/emrys/analyses/paired_cmh_candidate_ranking/step_09_cmh_editing_site_calling.R" \
        --execute > "$basename_rscript/execute.out"
)
[[ -e "$basename_marker" ]] || fail "PATH-basename Rscript was not invoked"
for suffix in \
    cmh_all_sites.tsv \
    cmh_significant_sites.tsv \
    cmh_summary.tsv \
    mutation_spectrum.tsv \
    mutation_spectrum.pdf \
    depth_delta.pdf
do
    [[ -s "$basename_rscript/output/basename-rscript/basename-rscript.$suffix" ]] ||
        fail "PATH-basename Rscript output is missing: $suffix"
done
assert_no_scratch "$basename_rscript/output" basename-rscript
[[ -z "$(find "$basename_rscript/cwd" -mindepth 1 -print -quit)" ]] ||
    fail "PATH-basename execution mutated the arbitrary working directory"

rm -f "$apply_marker"
EMRYS_RUN_TOKEN=explicit-owner-09 SLURM_JOB_ID=scheduler-09 \
    FAKE_R_MARKER="$apply_marker" "${base[@]}" > "$tmp/dry.out"
[[ ! -e "$apply_marker" ]] || fail "dry-run invoked R"
[[ ! -e "$tmp/output/analysis" ]] || fail "dry-run created output directory"
grep -q 'Run token: explicit-owner-09' "$tmp/dry.out" ||
    fail "explicit Step 09 owner token did not take precedence"
grep -q -- '--background-max-fraction' "$tmp/dry.out" ||
    fail "dry-run omitted policy arguments"
grep -q 'replicate=2 control=ABE_EV_2 treatment=ABE_PUM1_2' "$tmp/dry.out" ||
    fail "dry-run omitted the explicit replicate 2 pair"
grep -q 'replicate=3 control=ABE_EV_3 treatment=ABE_PUM1_3' "$tmp/dry.out" ||
    fail "dry-run omitted the explicit replicate 3 pair"
grep -q 'replicate=4 control=ABE_EV4 treatment=ABE_PUM1_4' "$tmp/dry.out" ||
    fail "dry-run omitted the explicit replicate 4 pair"

"${base[@]}" \
    --mean-dp-threshold 0 \
    --fdr-threshold 1 \
    --absolute-difference-threshold 0 \
    > "$tmp/accepted-zero-one-boundaries.out"
"${base[@]}" --absolute-difference-threshold 1 \
    > "$tmp/accepted-absolute-one-boundary.out"
expect_fail "mean_dp_threshold" \
    "${base[@]}" --mean-dp-threshold -1
expect_fail "fdr_threshold" \
    "${base[@]}" --fdr-threshold 1.01
expect_fail "absolute_difference_threshold" \
    "${base[@]}" --absolute-difference-threshold -0.01
expect_fail "absolute_difference_threshold" \
    "${base[@]}" --absolute-difference-threshold 1.01

duplicate_manifest_header="$tmp/duplicate-manifest-header"
copy_fixture "$duplicate_manifest_header"
awk -F '\t' -v OFS='\t' '
    NR == 1 { $6 = "condition" }
    { print }
' "$duplicate_manifest_header/samples.tsv" \
    > "$duplicate_manifest_header/rewritten.tsv"
mv "$duplicate_manifest_header/rewritten.tsv" \
    "$duplicate_manifest_header/samples.tsv"
expect_fail "duplicate sample manifest column: condition" \
    run_step09 "$duplicate_manifest_header" duplicate-manifest-header

manifest_field_count="$tmp/manifest-field-count"
copy_fixture "$manifest_field_count"
awk -F '\t' -v OFS='\t' '
    NR == 2 { print $0, "extra"; next }
    { print }
' "$manifest_field_count/samples.tsv" > "$manifest_field_count/rewritten.tsv"
mv "$manifest_field_count/rewritten.tsv" "$manifest_field_count/samples.tsv"
expect_fail "sample manifest row 2 has 7 fields; expected 6" \
    run_step09 "$manifest_field_count" manifest-field-count

partition_field_count="$tmp/partition-field-count"
copy_fixture "$partition_field_count"
printf '%s\n' $'p2\tregion\t2:1-100\textra' \
    >> "$partition_field_count/partitions.tsv"
expect_fail "partition manifest row 3 has 4 fields; expected 3" \
    run_step09 "$partition_field_count" partition-field-count

missing_replicate="$tmp/missing-replicate"
copy_fixture "$missing_replicate"
awk -F '\t' -v OFS='\t' '
    NR == 2 { $6 = "" }
    { print }
' "$missing_replicate/samples.tsv" > "$missing_replicate/rewritten.tsv"
mv "$missing_replicate/rewritten.tsv" "$missing_replicate/samples.tsv"
expect_fail "analysis sample ABE_EV_2 has an empty replicate" \
    run_step09 "$missing_replicate" missing-replicate

unmatched_replicate="$tmp/unmatched-replicate"
copy_fixture "$unmatched_replicate"
awk -F '\t' '$1 != "ABE_PUM1_4"' \
    "$unmatched_replicate/samples.tsv" > "$unmatched_replicate/rewritten.tsv"
mv "$unmatched_replicate/rewritten.tsv" "$unmatched_replicate/samples.tsv"
expect_fail "control replicate 4 has no treatment pair" \
    run_step09 "$unmatched_replicate" unmatched-replicate

duplicate_pair="$tmp/duplicate-pair"
copy_fixture "$duplicate_pair"
printf '%s\n' \
    $'ABE_EV_2_DUP\tABE_EV_2_DUP_R1\tABE_EV_2_DUP_R2\treverse\tEV\t2' \
    >> "$duplicate_pair/samples.tsv"
expect_fail "condition EV has more than one sample for replicate 2" \
    run_step09 "$duplicate_pair" duplicate-pair

one_stratum="$tmp/one-stratum"
copy_fixture "$one_stratum"
head -3 "$one_stratum/samples.tsv" > "$one_stratum/rewritten.tsv"
mv "$one_stratum/rewritten.tsv" "$one_stratum/samples.tsv"
expect_fail "at least two replicate strata" \
    run_step09 "$one_stratum" one-stratum

background_same="$tmp/background-same"
copy_fixture "$background_same"
expect_fail "Background condition must differ from control and treatment" \
    run_step09 "$background_same" background-same --background-condition EV

background_absent="$tmp/background-absent"
copy_fixture "$background_absent"
expect_fail "background condition has no samples: NODOX" \
    run_step09 "$background_absent" background-absent --background-condition NODOX

background_valid="$tmp/background-valid"
copy_fixture "$background_valid"
add_background_sample "$background_valid"
background_args_log="$background_valid/fake-r.args"
background_marker="$background_valid/fake-r.invoked"
FAKE_R_MARKER="$background_marker" \
FAKE_R_ARGS_LOG="$background_args_log" \
"$script" --analysis-id background-valid --cohort-id cohort \
    --sample-manifest "$background_valid/samples.tsv" \
    --partition-manifest "$background_valid/partitions.tsv" \
    --step08-root "$background_valid/step08" \
    --output-root "$background_valid/output" \
    --background-condition NODOX \
    --background-max-fraction 0.009 \
    --rscript-bin "$fake_r" \
    --r-script "$repo_root/src/emrys/analyses/paired_cmh_candidate_ranking/step_09_cmh_editing_site_calling.R" \
    --execute > "$background_valid/execute.out"
[[ -e "$background_marker" ]] ||
    fail "valid explicit background did not invoke fake R"
awk '
    previous == "--background-condition" && $0 == "NODOX" { found = 1 }
    { previous = $0 }
    END { exit !found }
' "$background_args_log" ||
    fail "valid explicit background was not forwarded to fake R"
awk '
    previous == "--background-max-fraction" && $0 == "0.009" { found = 1 }
    { previous = $0 }
    END { exit !found }
' "$background_args_log" ||
    fail "background fraction was not forwarded to fake R"
background_all="$background_valid/output/background-valid/background-valid.cmh_all_sites.tsv"
awk -F '\t' '
    NR == 2 {
        if ($29 != "background_not_passed" ||
            $31 != "fail_fraction" ||
            ($37 + 0) != 0.05) exit 1
        target_seen = 1
    }
    NR == 3 {
        if ($29 != "not_tested" ||
            $31 != "fail_fraction" ||
            ($37 + 0) != 0.05) exit 1
        nontarget_seen = 1
    }
    END { exit !(target_seen && nontarget_seen) }
' "$background_all" ||
    fail "background status/max were not derived from preserved DP/AD"

tampered_background_max="$tmp/tampered-background-max"
copy_fixture "$tampered_background_max"
add_background_sample "$tampered_background_max"
FAKE_R_MARKER="$tampered_background_max/fake-r.invoked" \
FAKE_R_MODE=tamper_background_max \
    expect_fail \
        "Step 09 all-sites rows do not preserve the Step 08 source/analysis contract" \
        run_step09 "$tampered_background_max" tampered-background-max \
        --background-condition NODOX --background-max-fraction 0.009 --execute
assert_no_finals "$tampered_background_max/output" tampered-background-max
assert_no_scratch "$tampered_background_max/output" tampered-background-max

tampered_background_status="$tmp/tampered-background-status"
copy_fixture "$tampered_background_status"
add_background_sample "$tampered_background_status"
FAKE_R_MARKER="$tampered_background_status/fake-r.invoked" \
FAKE_R_MODE=tamper_background_status \
    expect_fail \
        "Step 09 all-sites rows do not preserve the Step 08 source/analysis contract" \
        run_step09 "$tampered_background_status" tampered-background-status \
        --background-condition NODOX --background-max-fraction 0.009 --execute
assert_no_finals "$tampered_background_status/output" tampered-background-status
assert_no_scratch "$tampered_background_status/output" tampered-background-status

wrong_receipt_order="$tmp/wrong-receipt-order"
copy_fixture "$wrong_receipt_order"
{
    head -1 "$wrong_receipt_order/step08/cohort/cohort.step08_inputs.tsv"
    sed -n '3p' "$wrong_receipt_order/step08/cohort/cohort.step08_inputs.tsv"
    sed -n '2p' "$wrong_receipt_order/step08/cohort/cohort.step08_inputs.tsv"
} > "$wrong_receipt_order/rewritten.tsv"
mv "$wrong_receipt_order/rewritten.tsv" \
    "$wrong_receipt_order/step08/cohort/cohort.step08_inputs.tsv"
expect_fail "Step 08 input receipt content/order/counts are invalid" \
    run_step09 "$wrong_receipt_order" wrong-receipt-order

stale_manifest_hash="$tmp/stale-manifest-hash"
copy_fixture "$stale_manifest_hash"
awk -F '\t' -v OFS='\t' -v stale_hash="$(printf 'b%.0s' {1..64})" '
    NR > 1 { $10 = stale_hash }
    { print }
' "$stale_manifest_hash/step08/cohort/cohort.step08_inputs.tsv" \
    > "$stale_manifest_hash/rewritten.tsv"
mv "$stale_manifest_hash/rewritten.tsv" \
    "$stale_manifest_hash/step08/cohort/cohort.step08_inputs.tsv"
expect_fail "Step 08 input receipt content/order/counts are invalid" \
    run_step09 "$stale_manifest_hash" stale-manifest-hash

receipt_reconciliation="$tmp/receipt-reconciliation"
copy_fixture "$receipt_reconciliation"
awk -F '\t' -v OFS='\t' '
    NR == 2 { $17 = 2 }
    { print }
' "$receipt_reconciliation/step08/cohort/cohort.step08_inputs.tsv" \
    > "$receipt_reconciliation/rewritten.tsv"
mv "$receipt_reconciliation/rewritten.tsv" \
    "$receipt_reconciliation/step08/cohort/cohort.step08_inputs.tsv"
expect_fail "Step 08 input receipt content/order/counts are invalid" \
    run_step09 "$receipt_reconciliation" receipt-reconciliation

reordered_sample_columns="$tmp/reordered-sample-columns"
copy_fixture "$reordered_sample_columns"
awk -F '\t' -v OFS='\t' '
    NR == 1 {
        temporary = $23
        $23 = $24
        $24 = temporary
    }
    { print }
' "$reordered_sample_columns/step08/cohort/cohort.step08_sites.tsv" \
    > "$reordered_sample_columns/rewritten.tsv"
mv "$reordered_sample_columns/rewritten.tsv" \
    "$reordered_sample_columns/step08/cohort/cohort.step08_sites.tsv"
expect_fail "Step 08 sites table header is invalid" \
    run_step09 "$reordered_sample_columns" reordered-sample-columns

missing_sample_column="$tmp/missing-sample-column"
copy_fixture "$missing_sample_column"
awk -F '\t' -v OFS='\t' '
    { NF--; print }
' "$missing_sample_column/step08/cohort/cohort.step08_sites.tsv" \
    > "$missing_sample_column/rewritten.tsv"
mv "$missing_sample_column/rewritten.tsv" \
    "$missing_sample_column/step08/cohort/cohort.step08_sites.tsv"
expect_fail "Step 08 sites table header is invalid" \
    run_step09 "$missing_sample_column" missing-sample-column

duplicate_candidate="$tmp/duplicate-candidate"
copy_fixture "$duplicate_candidate"
awk -F '\t' -v OFS='\t' '
    NR == 2 { first_candidate = $2 }
    NR == 3 { $2 = first_candidate }
    { print }
' "$duplicate_candidate/step08/cohort/cohort.step08_sites.tsv" \
    > "$duplicate_candidate/rewritten.tsv"
mv "$duplicate_candidate/rewritten.tsv" \
    "$duplicate_candidate/step08/cohort/cohort.step08_sites.tsv"
expect_fail "Step 08 sites table rows or partition/orientation counts are invalid" \
    run_step09 "$duplicate_candidate" duplicate-candidate

orientation_count_mismatch="$tmp/orientation-count-mismatch"
copy_fixture "$orientation_count_mismatch"
awk -F '\t' -v OFS='\t' '
    NR == 3 { $3 = "FWD_like" }
    { print }
' "$orientation_count_mismatch/step08/cohort/cohort.step08_sites.tsv" \
    > "$orientation_count_mismatch/rewritten.tsv"
mv "$orientation_count_mismatch/rewritten.tsv" \
    "$orientation_count_mismatch/step08/cohort/cohort.step08_sites.tsv"
expect_fail "Step 08 sites table rows or partition/orientation counts are invalid" \
    run_step09 "$orientation_count_mismatch" orientation-count-mismatch

header_only="$tmp/header-only"
copy_fixture "$header_only"
head -1 "$header_only/step08/cohort/cohort.step08_sites.tsv" \
    > "$header_only/rewritten.tsv"
mv "$header_only/rewritten.tsv" \
    "$header_only/step08/cohort/cohort.step08_sites.tsv"
awk -F '\t' -v OFS='\t' '
    NR > 1 {
        for (field = 15; field <= 21; field++) $field = 0
    }
    { print }
' "$header_only/step08/cohort/cohort.step08_inputs.tsv" \
    > "$header_only/rewritten.tsv"
mv "$header_only/rewritten.tsv" \
    "$header_only/step08/cohort/cohort.step08_inputs.tsv"
header_only_marker="$header_only/fake-r.invoked"
FAKE_R_MARKER="$header_only_marker" \
    run_step09 "$header_only" header-only --execute > "$header_only/execute.out"
header_only_output="$header_only/output/header-only"
[[ -e "$header_only_marker" ]] ||
    fail "header-only Step 08 inputs did not invoke fake R"
[[ "$(wc -l < "$header_only_output/header-only.cmh_all_sites.tsv" | tr -d ' ')" == "1" ]] ||
    fail "header-only all-sites output contains data rows"
[[ "$(wc -l < "$header_only_output/header-only.cmh_significant_sites.tsv" | tr -d ' ')" == "1" ]] ||
    fail "header-only significant-sites output contains data rows"
awk -F '\t' 'NR == 2 && $9 == 0 && $10 == 0 && $11 == 0 { found = 1 }
    END { exit !found }' \
    "$header_only_output/header-only.cmh_summary.tsv" ||
    fail "header-only summary did not report zero candidates"
awk -F '\t' 'NR > 1 { total += $5 } END { exit !(total == 0) }' \
    "$header_only_output/header-only.mutation_spectrum.tsv" ||
    fail "header-only mutation spectrum did not reconcile to zero"

fake_r_failure="$tmp/fake-r-failure"
copy_fixture "$fake_r_failure"
fake_r_failure_marker="$fake_r_failure/fake-r.invoked"
FAKE_R_MARKER="$fake_r_failure_marker" FAKE_R_MODE=fail \
    expect_fail "Step 09 R CMH analysis failed" \
        run_step09 "$fake_r_failure" fake-r-failure --execute
[[ -e "$fake_r_failure_marker" ]] ||
    fail "fake-R failure mode was not invoked"
assert_no_finals "$fake_r_failure/output" fake-r-failure
assert_no_scratch "$fake_r_failure/output" fake-r-failure

omitted_output="$tmp/omitted-output"
copy_fixture "$omitted_output"
omitted_output_marker="$omitted_output/fake-r.invoked"
FAKE_R_MARKER="$omitted_output_marker" FAKE_R_MODE=omit_summary \
    expect_fail "Step 09 summary does not exist or is empty" \
        run_step09 "$omitted_output" omitted-output --execute
assert_no_finals "$omitted_output/output" omitted-output
assert_no_scratch "$omitted_output/output" omitted-output

malformed_pdf="$tmp/malformed-pdf"
copy_fixture "$malformed_pdf"
malformed_pdf_marker="$malformed_pdf/fake-r.invoked"
FAKE_R_MARKER="$malformed_pdf_marker" FAKE_R_MODE=bad_pdf \
    expect_fail "Step 09 mutation-spectrum PDF is missing a PDF signature" \
        run_step09 "$malformed_pdf" malformed-pdf --execute
assert_no_finals "$malformed_pdf/output" malformed-pdf
assert_no_scratch "$malformed_pdf/output" malformed-pdf

run_input_mutation_case \
    mutate_sample sample-manifest-mutation \
    "Sample manifest changed during Step 09"
run_input_mutation_case \
    mutate_partition partition-manifest-mutation \
    "Partition manifest changed during Step 09"
run_input_mutation_case \
    mutate_sites step08-sites-mutation \
    "Step 08 sites table changed during Step 09"
run_input_mutation_case \
    mutate_inputs step08-inputs-mutation \
    "Step 08 input receipt changed during Step 09"

r_script_mutation="$tmp/r-script-mutation"
copy_fixture "$r_script_mutation"
cp "$repo_root/src/emrys/analyses/paired_cmh_candidate_ranking/step_09_cmh_editing_site_calling.R" \
    "$r_script_mutation/step09_impl.R"
mkdir -p "$r_script_mutation/output/r-script-mutation"
printf 'unrelated bytes\n' > \
    "$r_script_mutation/output/r-script-mutation/unrelated.txt"
FAKE_R_MARKER="$r_script_mutation/fake-r.invoked" \
FAKE_R_MODE=mutate_r_script \
"$script" --analysis-id r-script-mutation --cohort-id cohort \
    --sample-manifest "$r_script_mutation/samples.tsv" \
    --partition-manifest "$r_script_mutation/partitions.tsv" \
    --step08-root "$r_script_mutation/step08" \
    --output-root "$r_script_mutation/output" \
    --rscript-bin "$fake_r" \
    --r-script "$r_script_mutation/step09_impl.R" \
    --execute > "$r_script_mutation/execute.out"
grep -q 'changed while fake R was running' "$r_script_mutation/step09_impl.R" ||
    fail "selected R program was not mutated while Step 09 was running"
for suffix in \
    cmh_all_sites.tsv \
    cmh_significant_sites.tsv \
    cmh_summary.tsv \
    mutation_spectrum.tsv \
    mutation_spectrum.pdf \
    depth_delta.pdf
do
    [[ -s "$r_script_mutation/output/r-script-mutation/r-script-mutation.$suffix" ]] ||
        fail "R-program mutation did not publish $suffix"
done
assert_no_scratch "$r_script_mutation/output" r-script-mutation
assert_file_equals \
    "$r_script_mutation/output/r-script-mutation/unrelated.txt" \
    "unrelated bytes"
assert_header_omits \
    "$r_script_mutation/output/r-script-mutation/r-script-mutation.cmh_summary.tsv" \
    rscript_path \
    rscript_version \
    r_script_path \
    r_script_sha256 \
    r_version \
    r_package_state \
    run_token \
    attempt_id \
    all_sites_sha256 \
    significant_sites_sha256 \
    mutation_spectrum_sha256 \
    mutation_spectrum_pdf_sha256 \
    depth_delta_pdf_sha256

foreign_lock="$tmp/foreign-lock"
copy_fixture "$foreign_lock"
foreign_lock_dir="$foreign_lock/output/foreign-lock/.foreign-lock.step09.lock"
mkdir -p "$foreign_lock_dir"
printf 'foreign owner\n' > "$foreign_lock_dir/owner"
expect_fail "Step 09 lock already exists" \
    env \
    FAKE_R_MARKER="$foreign_lock/fake-r.invoked" \
    "$script" --analysis-id foreign-lock --cohort-id cohort \
    --sample-manifest "$foreign_lock/samples.tsv" \
    --partition-manifest "$foreign_lock/partitions.tsv" \
    --step08-root "$foreign_lock/step08" \
    --output-root "$foreign_lock/output" \
    --rscript-bin "$fake_r" \
    --r-script "$repo_root/src/emrys/analyses/paired_cmh_candidate_ranking/step_09_cmh_editing_site_calling.R" \
    --execute
assert_file_equals "$foreign_lock_dir/owner" "foreign owner"
[[ ! -e "$foreign_lock/fake-r.invoked" ]] ||
    fail "foreign lock case invoked fake R"

owner_failure_analysis="owner-write-failure"
owner_failure_dir="$tmp/output/$owner_failure_analysis"
owner_failure_lock="$owner_failure_dir/.$owner_failure_analysis.step09.lock"
owner_failure_marker="$tmp/owner-write-failure.invoked"
mkdir -p "$owner_failure_dir"
if (
    umask 0222
    FAKE_R_MARKER="$owner_failure_marker" \
        "$script" --analysis-id "$owner_failure_analysis" --cohort-id cohort \
        --sample-manifest "$sample_manifest" \
        --partition-manifest "$partition_manifest" \
        --step08-root "$tmp/step08" --output-root "$tmp/output" \
        --rscript-bin "$fake_r" \
        --r-script "$repo_root/src/emrys/analyses/paired_cmh_candidate_ranking/step_09_cmh_editing_site_calling.R" \
        --execute
) > "$tmp/owner-write-failure.out" 2> "$tmp/owner-write-failure.err"; then
    fail "owner metadata write failure unexpectedly succeeded"
fi
[[ ! -e "$owner_failure_marker" ]] ||
    fail "owner metadata write failure invoked fake R"
[[ ! -e "$owner_failure_lock" ]] ||
    fail "owner metadata write failure orphaned the owned lock"

replacement="$tmp/replacement"
copy_fixture "$replacement"
seed_prior_outputs "$replacement/output" replacement "previous replacement"
replacement_marker="$replacement/fake-r.invoked"
expect_fail "under --no-clobber" \
    env FAKE_R_MARKER="$replacement_marker" \
    "$script" --analysis-id replacement --cohort-id cohort \
    --sample-manifest "$replacement/samples.tsv" \
    --partition-manifest "$replacement/partitions.tsv" \
    --step08-root "$replacement/step08" \
    --output-root "$replacement/output" \
    --rscript-bin "$fake_r" \
    --r-script "$repo_root/src/emrys/analyses/paired_cmh_candidate_ranking/step_09_cmh_editing_site_calling.R" \
    --no-clobber --execute
[[ ! -e "$replacement_marker" ]] ||
    fail "--no-clobber invoked fake R"
for replacement_path in "$replacement/output/replacement"/replacement.*
do
    grep -q "previous replacement" "$replacement_path" ||
        fail "--no-clobber changed prior content: $replacement_path"
done
FAKE_R_MARKER="$replacement_marker" \
"$script" --analysis-id replacement --cohort-id cohort \
    --sample-manifest "$replacement/samples.tsv" \
    --partition-manifest "$replacement/partitions.tsv" \
    --step08-root "$replacement/step08" \
    --output-root "$replacement/output" \
    --rscript-bin "$fake_r" \
    --r-script "$repo_root/src/emrys/analyses/paired_cmh_candidate_ranking/step_09_cmh_editing_site_calling.R" \
    --execute > "$replacement/execute.out"
replacement_dir="$replacement/output/replacement"
for replacement_path in "$replacement_dir"/replacement.*
do
    grep -q "previous replacement" "$replacement_path" &&
        fail "successful replacement retained prior content: $replacement_path"
done
assert_no_scratch "$replacement/output" replacement

publication_order="$tmp/publication-order"
copy_fixture "$publication_order"
seed_prior_outputs \
    "$publication_order/output" publication-order "prior publication order"
publication_order_dir="$publication_order/output/publication-order"
printf 'unrelated bytes\n' > "$publication_order_dir/unrelated.txt"
publication_order_log="$publication_order/mv.log"
publication_order_marker="$publication_order/summary-visible"
publication_order_release="$publication_order/release"
env \
    PATH="$tmp/bin:$PATH" \
    SLURM_JOB_ID=publishorder09 \
    FAKE_R_MARKER="$publication_order/fake-r.invoked" \
    FAKE_MV_LOG="$publication_order_log" \
    FAKE_MV_BARRIER_DEST="$publication_order_dir/publication-order.cmh_summary.tsv" \
    FAKE_MV_BARRIER_MARKER="$publication_order_marker" \
    FAKE_MV_BARRIER_RELEASE="$publication_order_release" \
    "$script" --analysis-id publication-order --cohort-id cohort \
    --sample-manifest "$publication_order/samples.tsv" \
    --partition-manifest "$publication_order/partitions.tsv" \
    --step08-root "$publication_order/step08" \
    --output-root "$publication_order/output" \
    --rscript-bin "$fake_r" \
    --r-script "$repo_root/src/emrys/analyses/paired_cmh_candidate_ranking/step_09_cmh_editing_site_calling.R" \
    --execute > "$publication_order/execute.out" \
    2> "$publication_order/execute.err" &
publication_order_pid=$!
publication_order_seen=false
for _ in {1..500}; do
    if [[ -e "$publication_order_marker" ]]; then
        publication_order_seen=true
        break
    fi
    if ! kill -0 "$publication_order_pid" 2>/dev/null; then
        break
    fi
    sleep 0.01
done
if [[ "$publication_order_seen" != true ]]; then
    : > "$publication_order_release"
    wait "$publication_order_pid" 2>/dev/null || true
    fail "summary-publication barrier was not reached: $(cat "$publication_order/execute.err")"
fi
publication_order_error=""
for suffix in \
    cmh_all_sites.tsv \
    cmh_significant_sites.tsv \
    mutation_spectrum.tsv \
    mutation_spectrum.pdf \
    depth_delta.pdf \
    cmh_summary.tsv
do
    publication_final="$publication_order_dir/publication-order.$suffix"
    publication_backup="$publication_order_dir/.publication-order.$suffix.publishorder09.previous"
    if [[ ! -s "$publication_final" ]]; then
        publication_order_error="new final was not visible at the summary barrier: $suffix"
    elif grep -q "prior publication order" "$publication_final"; then
        publication_order_error="prior final remained visible at the summary barrier: $suffix"
    elif [[ ! -s "$publication_backup" ]]; then
        publication_order_error="predecessor backup was not retained at the summary barrier: $suffix"
    elif [[ "$(<"$publication_backup")" != "prior publication order $suffix" ]]; then
        publication_order_error="predecessor backup changed at the summary barrier: $suffix"
    fi
done
[[ -d "$publication_order_dir/.publication-order.step09.lock" ]] ||
    publication_order_error="owned lock was not held at the summary barrier"
[[ "$(<"$publication_order_dir/unrelated.txt")" == "unrelated bytes" ]] ||
    publication_order_error="unrelated output changed at the summary barrier"
: > "$publication_order_release"
wait "$publication_order_pid" ||
    fail "barrier-controlled publication failed: $(cat "$publication_order/execute.err")"
[[ -z "$publication_order_error" ]] || fail "$publication_order_error"

observed_publication_moves="$(tail -n 6 "$publication_order_log")"
expected_publication_moves="$(printf '%s\t%s\n' \
    "$publication_order_dir/.publication-order.step09.publishorder09.all.tmp.tsv" \
    "$publication_order_dir/publication-order.cmh_all_sites.tsv" \
    "$publication_order_dir/.publication-order.step09.publishorder09.significant.tmp.tsv" \
    "$publication_order_dir/publication-order.cmh_significant_sites.tsv" \
    "$publication_order_dir/.publication-order.step09.publishorder09.mutation.tmp.tsv" \
    "$publication_order_dir/publication-order.mutation_spectrum.tsv" \
    "$publication_order_dir/.publication-order.step09.publishorder09.mutation.tmp.pdf" \
    "$publication_order_dir/publication-order.mutation_spectrum.pdf" \
    "$publication_order_dir/.publication-order.step09.publishorder09.depth.tmp.pdf" \
    "$publication_order_dir/publication-order.depth_delta.pdf" \
    "$publication_order_dir/.publication-order.step09.publishorder09.summary.tmp.tsv" \
    "$publication_order_dir/publication-order.cmh_summary.tsv")"
[[ "$observed_publication_moves" == "$expected_publication_moves" ]] ||
    fail "Step 09 final publication order changed"
assert_file_equals "$publication_order_dir/unrelated.txt" "unrelated bytes"
assert_no_scratch "$publication_order/output" publication-order

signal_replacement="$tmp/signal-replacement"
copy_fixture "$signal_replacement"
seed_prior_outputs \
    "$signal_replacement/output" signal-replacement "prior signal replacement"
signal_replacement_dir="$signal_replacement/output/signal-replacement"
printf 'unrelated bytes\n' > "$signal_replacement_dir/unrelated.txt"
signal_replacement_marker="$signal_replacement/summary-visible"
signal_replacement_release="$signal_replacement/release"
env \
    PATH="$tmp/bin:$PATH" \
    SLURM_JOB_ID=signalreplace09 \
    FAKE_R_MARKER="$signal_replacement/fake-r.invoked" \
    FAKE_MV_BARRIER_DEST="$signal_replacement_dir/signal-replacement.cmh_summary.tsv" \
    FAKE_MV_BARRIER_MARKER="$signal_replacement_marker" \
    FAKE_MV_BARRIER_RELEASE="$signal_replacement_release" \
    "$script" --analysis-id signal-replacement --cohort-id cohort \
    --sample-manifest "$signal_replacement/samples.tsv" \
    --partition-manifest "$signal_replacement/partitions.tsv" \
    --step08-root "$signal_replacement/step08" \
    --output-root "$signal_replacement/output" \
    --rscript-bin "$fake_r" \
    --r-script "$repo_root/src/emrys/analyses/paired_cmh_candidate_ranking/step_09_cmh_editing_site_calling.R" \
    --execute > "$signal_replacement/execute.out" \
    2> "$signal_replacement/execute.err" &
signal_replacement_pid=$!
signal_replacement_seen=false
for _ in {1..500}; do
    if [[ -e "$signal_replacement_marker" ]]; then
        signal_replacement_seen=true
        break
    fi
    if ! kill -0 "$signal_replacement_pid" 2>/dev/null; then
        break
    fi
    sleep 0.01
done
if [[ "$signal_replacement_seen" != true ]]; then
    : > "$signal_replacement_release"
    kill -TERM "$signal_replacement_pid" 2>/dev/null || true
    wait "$signal_replacement_pid" 2>/dev/null || true
    fail "signal-replacement summary barrier was not reached"
fi
[[ -s "$signal_replacement_dir/signal-replacement.cmh_summary.tsv" ]] ||
    fail "replacement summary was not visible before TERM"
if grep -q "prior signal replacement" \
    "$signal_replacement_dir/signal-replacement.cmh_summary.tsv"; then
    fail "prior summary remained visible before TERM"
fi
kill -TERM "$signal_replacement_pid"
: > "$signal_replacement_release"
set +e
wait "$signal_replacement_pid"
signal_replacement_status=$?
set -e
[[ "$signal_replacement_status" -eq 143 ]] ||
    fail "expected TERM exit 143; got $signal_replacement_status"
for suffix in \
    cmh_all_sites.tsv \
    cmh_significant_sites.tsv \
    cmh_summary.tsv \
    mutation_spectrum.tsv \
    mutation_spectrum.pdf \
    depth_delta.pdf
do
    assert_file_equals \
        "$signal_replacement_dir/signal-replacement.$suffix" \
        "prior signal replacement $suffix"
done
assert_file_equals "$signal_replacement_dir/unrelated.txt" "unrelated bytes"
assert_no_scratch "$signal_replacement/output" signal-replacement

concurrency="$tmp/concurrency"
copy_fixture "$concurrency"
concurrency_marker="$concurrency/winner-at-r"
concurrency_release="$concurrency/release"
env \
    SLURM_JOB_ID=concurrencywinner09 \
    FAKE_R_MARKER="$concurrency/winner-r.invoked" \
    FAKE_R_BARRIER_MARKER="$concurrency_marker" \
    FAKE_R_BARRIER_RELEASE="$concurrency_release" \
    "$script" --analysis-id concurrency --cohort-id cohort \
    --sample-manifest "$concurrency/samples.tsv" \
    --partition-manifest "$concurrency/partitions.tsv" \
    --step08-root "$concurrency/step08" \
    --output-root "$concurrency/output" \
    --rscript-bin "$fake_r" \
    --r-script "$repo_root/src/emrys/analyses/paired_cmh_candidate_ranking/step_09_cmh_editing_site_calling.R" \
    --execute > "$concurrency/winner.out" \
    2> "$concurrency/winner.err" &
concurrency_winner_pid=$!
concurrency_seen=false
for _ in {1..500}; do
    if [[ -e "$concurrency_marker" ]]; then
        concurrency_seen=true
        break
    fi
    if ! kill -0 "$concurrency_winner_pid" 2>/dev/null; then
        break
    fi
    sleep 0.01
done
if [[ "$concurrency_seen" != true ]]; then
    : > "$concurrency_release"
    kill -TERM "$concurrency_winner_pid" 2>/dev/null || true
    wait "$concurrency_winner_pid" 2>/dev/null || true
    fail "same-analysis winner did not reach the fake-R barrier"
fi
concurrency_dir="$concurrency/output/concurrency"
concurrency_lock="$concurrency_dir/.concurrency.step09.lock"
[[ -d "$concurrency_lock" ]] ||
    fail "same-analysis winner did not hold the analysis lock"
grep -Fqx $'run_token\tconcurrencywinner09' "$concurrency_lock/owner" ||
    fail "same-analysis winner lock recorded the wrong run token"
assert_no_finals "$concurrency/output" concurrency
set +e
env \
    SLURM_JOB_ID=concurrencyloser09 \
    FAKE_R_MARKER="$concurrency/loser-r.invoked" \
    "$script" --analysis-id concurrency --cohort-id cohort \
    --sample-manifest "$concurrency/samples.tsv" \
    --partition-manifest "$concurrency/partitions.tsv" \
    --step08-root "$concurrency/step08" \
    --output-root "$concurrency/output" \
    --rscript-bin "$fake_r" \
    --r-script "$repo_root/src/emrys/analyses/paired_cmh_candidate_ranking/step_09_cmh_editing_site_calling.R" \
    --execute > "$concurrency/loser.out" \
    2> "$concurrency/loser.err"
concurrency_loser_status=$?
set -e
[[ "$concurrency_loser_status" -eq 1 ]] ||
    fail "expected competing same-analysis execution to exit 1; got $concurrency_loser_status"
grep -Fqx "ERROR: Step 09 lock already exists: $concurrency_lock" \
    "$concurrency/loser.err" ||
    fail "competing same-analysis execution reported the wrong lock failure"
[[ ! -e "$concurrency/loser-r.invoked" ]] ||
    fail "competing same-analysis execution invoked fake R"
grep -Fqx $'run_token\tconcurrencywinner09' "$concurrency_lock/owner" ||
    fail "competing execution changed the winner lock owner"
: > "$concurrency_release"
wait "$concurrency_winner_pid" ||
    fail "admitted same-analysis execution failed: $(cat "$concurrency/winner.err")"
for suffix in \
    cmh_all_sites.tsv \
    cmh_significant_sites.tsv \
    cmh_summary.tsv \
    mutation_spectrum.tsv \
    mutation_spectrum.pdf \
    depth_delta.pdf
do
    [[ -s "$concurrency_dir/concurrency.$suffix" ]] ||
        fail "same-analysis winner did not publish $suffix"
done
[[ "$(find "$concurrency_dir" -maxdepth 1 -type f | wc -l | tr -d ' ')" == "6" ]] ||
    fail "same-analysis executions left more than one final output set"
assert_no_scratch "$concurrency/output" concurrency

move_failure="$tmp/move-failure"
copy_fixture "$move_failure"
seed_prior_outputs "$move_failure/output" move-failure "prior move failure"
move_failure_before="$(hash_output_set "$move_failure/output" move-failure)"
move_failure_dir="$move_failure/output/move-failure"
expect_fail "forced fake mv failure" \
    env \
    PATH="$tmp/bin:$PATH" \
    SLURM_JOB_ID=movefail09 \
    FAKE_R_MARKER="$move_failure/fake-r.invoked" \
    FAKE_MV_FAIL_ONCE_DEST="$move_failure_dir/move-failure.mutation_spectrum.tsv" \
    FAKE_MV_FAIL_MARKER="$move_failure/mv-failed" \
    "$script" --analysis-id move-failure --cohort-id cohort \
    --sample-manifest "$move_failure/samples.tsv" \
    --partition-manifest "$move_failure/partitions.tsv" \
    --step08-root "$move_failure/step08" \
    --output-root "$move_failure/output" \
    --rscript-bin "$fake_r" \
    --r-script "$repo_root/src/emrys/analyses/paired_cmh_candidate_ranking/step_09_cmh_editing_site_calling.R" \
    --execute
move_failure_after="$(hash_output_set "$move_failure/output" move-failure)"
[[ "$move_failure_after" == "$move_failure_before" ]] ||
    fail "publication move failure did not restore all six prior outputs"
assert_no_scratch "$move_failure/output" move-failure

restore_failure="$tmp/restore-failure"
copy_fixture "$restore_failure"
seed_prior_outputs "$restore_failure/output" restore-failure "prior restore failure"
restore_failure_dir="$restore_failure/output/restore-failure"
restore_failure_final="$restore_failure_dir/restore-failure.mutation_spectrum.tsv"
restore_failure_backup="$restore_failure_dir/.restore-failure.mutation_spectrum.tsv.restorefail09.previous"
restore_failure_lock="$restore_failure_dir/.restore-failure.step09.lock"
if env \
    PATH="$tmp/bin:$PATH" \
    SLURM_JOB_ID=restorefail09 \
    FAKE_R_MARKER="$restore_failure/fake-r.invoked" \
    FAKE_MV_FAIL_ONCE_DEST="$restore_failure_final" \
    FAKE_MV_FAIL_MARKER="$restore_failure/publish-mv-failed" \
    FAKE_MV_FAIL_RESTORE_SOURCE="$restore_failure_backup" \
    FAKE_MV_RESTORE_FAIL_MARKER="$restore_failure/restore-mv-failed" \
    "$script" --analysis-id restore-failure --cohort-id cohort \
    --sample-manifest "$restore_failure/samples.tsv" \
    --partition-manifest "$restore_failure/partitions.tsv" \
    --step08-root "$restore_failure/step08" \
    --output-root "$restore_failure/output" \
    --rscript-bin "$fake_r" \
    --r-script "$repo_root/src/emrys/analyses/paired_cmh_candidate_ranking/step_09_cmh_editing_site_calling.R" \
    --execute \
    > "$restore_failure/execute.out" \
    2> "$restore_failure/execute.err"
then
    fail "publication plus restore failure unexpectedly succeeded"
fi
grep -q "Could not restore Step 09 backup during rollback" \
    "$restore_failure/execute.err" ||
    fail "restore failure did not identify the unrestored backup"
grep -q "Step 09 rollback was incomplete; retaining the owned lock" \
    "$restore_failure/execute.err" ||
    fail "restore failure did not report incomplete rollback"
[[ -e "$restore_failure/publish-mv-failed" &&
   -e "$restore_failure/restore-mv-failed" ]] ||
    fail "restore-failure shims were not both exercised"
[[ -d "$restore_failure_lock" ]] ||
    fail "incomplete rollback did not retain its owned lock"
grep -Fqx $'run_token\trestorefail09' "$restore_failure_lock/owner" ||
    fail "retained recovery lock has the wrong owner token"
assert_file_equals \
    "$restore_failure_backup" \
    "prior restore failure mutation_spectrum.tsv"
[[ ! -e "$restore_failure_final" ]] ||
    fail "failed restore left an ambiguous mutation-spectrum final"
for restored_suffix in \
    cmh_all_sites.tsv \
    cmh_significant_sites.tsv \
    cmh_summary.tsv \
    mutation_spectrum.pdf \
    depth_delta.pdf
do
    assert_file_equals \
        "$restore_failure_dir/restore-failure.$restored_suffix" \
        "prior restore failure $restored_suffix"
    [[ ! -e "$restore_failure_dir/.restore-failure.$restored_suffix.restorefail09.previous" ]] ||
        fail "restored output retained a redundant backup: $restored_suffix"
done
for restore_temp in "$restore_failure_dir"/.restore-failure.step09.restorefail09.*
do
    [[ ! -e "$restore_temp" ]] ||
        fail "incomplete rollback retained an owned temp: $restore_temp"
done

postvalidation="$tmp/postvalidation"
copy_fixture "$postvalidation"
seed_prior_outputs "$postvalidation/output" postvalidation "prior postvalidation"
postvalidation_before="$(hash_output_set "$postvalidation/output" postvalidation)"
postvalidation_dir="$postvalidation/output/postvalidation"
expect_fail "Published Step 09 output changed during publication" \
    env \
    PATH="$tmp/bin:$PATH" \
    SLURM_JOB_ID=postvalidate09 \
    FAKE_R_MARKER="$postvalidation/fake-r.invoked" \
    FAKE_MV_CORRUPT_ONCE_DEST="$postvalidation_dir/postvalidation.mutation_spectrum.pdf" \
    FAKE_MV_CORRUPT_MARKER="$postvalidation/mv-corrupted" \
    "$script" --analysis-id postvalidation --cohort-id cohort \
    --sample-manifest "$postvalidation/samples.tsv" \
    --partition-manifest "$postvalidation/partitions.tsv" \
    --step08-root "$postvalidation/step08" \
    --output-root "$postvalidation/output" \
    --rscript-bin "$fake_r" \
    --r-script "$repo_root/src/emrys/analyses/paired_cmh_candidate_ranking/step_09_cmh_editing_site_calling.R" \
    --execute
postvalidation_after="$(hash_output_set "$postvalidation/output" postvalidation)"
[[ "$postvalidation_after" == "$postvalidation_before" ]] ||
    fail "post-publication hash failure did not restore prior outputs"
assert_no_scratch "$postvalidation/output" postvalidation

first_publish_failure="$tmp/first-publish-failure"
copy_fixture "$first_publish_failure"
first_publish_dir="$first_publish_failure/output/first-publish-failure"
expect_fail "forced fake mv failure" \
    env \
    PATH="$tmp/bin:$PATH" \
    SLURM_JOB_ID=firstpublish09 \
    FAKE_R_MARKER="$first_publish_failure/fake-r.invoked" \
    FAKE_MV_FAIL_ONCE_DEST="$first_publish_dir/first-publish-failure.mutation_spectrum.tsv" \
    FAKE_MV_FAIL_MARKER="$first_publish_failure/mv-failed" \
    "$script" --analysis-id first-publish-failure --cohort-id cohort \
    --sample-manifest "$first_publish_failure/samples.tsv" \
    --partition-manifest "$first_publish_failure/partitions.tsv" \
    --step08-root "$first_publish_failure/step08" \
    --output-root "$first_publish_failure/output" \
    --rscript-bin "$fake_r" \
    --r-script "$repo_root/src/emrys/analyses/paired_cmh_candidate_ranking/step_09_cmh_editing_site_calling.R" \
    --execute
assert_no_finals "$first_publish_failure/output" first-publish-failure
assert_no_scratch "$first_publish_failure/output" first-publish-failure

stale_scratch="$tmp/stale-scratch"
copy_fixture "$stale_scratch"
stale_scratch_dir="$stale_scratch/output/stale-scratch"
stale_scratch_path="$stale_scratch_dir/.stale-scratch.step09.older-token.all.tmp.tsv"
mkdir -p "$stale_scratch_dir"
printf 'foreign scratch\n' > "$stale_scratch_path"
expect_fail "residue requires operator inspection" \
    env \
    SLURM_JOB_ID=newer-token \
    FAKE_R_MARKER="$stale_scratch/fake-r.invoked" \
    "$script" --analysis-id stale-scratch --cohort-id cohort \
    --sample-manifest "$stale_scratch/samples.tsv" \
    --partition-manifest "$stale_scratch/partitions.tsv" \
    --step08-root "$stale_scratch/step08" \
    --output-root "$stale_scratch/output" \
    --rscript-bin "$fake_r" \
    --r-script "$repo_root/src/emrys/analyses/paired_cmh_candidate_ranking/step_09_cmh_editing_site_calling.R" \
    --no-clobber \
    --execute
assert_file_equals "$stale_scratch_path" "foreign scratch"
[[ ! -e "$stale_scratch_dir/.stale-scratch.step09.lock" ]] ||
    fail "stale scratch refusal left an owned lock"
[[ ! -e "$stale_scratch/fake-r.invoked" ]] ||
    fail "stale scratch refusal invoked fake R"

FAKE_R_MARKER="$apply_marker" "${base[@]}" --execute > "$tmp/execute.out"
out="$tmp/output/analysis"
for path in \
    "$out/analysis.cmh_all_sites.tsv" \
    "$out/analysis.cmh_significant_sites.tsv" \
    "$out/analysis.cmh_summary.tsv" \
    "$out/analysis.mutation_spectrum.tsv" \
    "$out/analysis.mutation_spectrum.pdf" \
    "$out/analysis.depth_delta.pdf"
do
    [[ -s "$path" ]] || fail "missing published output: $path"
done
[[ "$(wc -l < "$out/analysis.cmh_all_sites.tsv" | tr -d ' ')" == "3" ]] ||
    fail "all-sites row count did not reconcile"
[[ "$(wc -l < "$out/analysis.cmh_significant_sites.tsv" | tr -d ' ')" == "2" ]] ||
    fail "significant subset is invalid"
[[ "$(wc -l < "$out/analysis.mutation_spectrum.tsv" | tr -d ' ')" == "13" ]] ||
    fail "mutation spectrum is not canonical"

mkdir -p "$out/.analysis.step09.lock"
expect_fail "lock already exists" "${base[@]}" --execute
rm -rf "$out/.analysis.step09.lock"

rm -f "$out/analysis.cmh_summary.tsv"
expect_fail "incomplete" "${base[@]}" --execute

grep -q 'bash src/emrys/analyses/paired_cmh_candidate_ranking/step_09_cmh_editing_site_calling.sh' "$job" ||
    fail "SLURM wrapper does not delegate to the Step 09 shell implementation"
if grep -Eq 'mantelhaen[.]test|p[.]adjust|VariantAnnotation|read[.]table' "$job"; then
    fail "SLURM wrapper embeds analysis logic"
fi

job_fixture="$tmp/job-wrapper"
copy_fixture "$job_fixture"
mkdir -p \
    "$job_fixture/src/emrys/analyses/paired_cmh_candidate_ranking" \
    "$job_fixture/src/emrys/libraries"
cp "$script" "$job_fixture/src/emrys/analyses/paired_cmh_candidate_ranking/step_09_cmh_editing_site_calling.sh"
cp "$repo_root/src/emrys/libraries/argument_parsing.sh" \
    "$job_fixture/src/emrys/libraries/"
job_output_root="$job_fixture/job-output"
env \
    PATH="$tmp/bin:$PATH" \
    SLURM_SUBMIT_DIR="$job_fixture" \
    ANALYSIS_ID=job-dry \
    COHORT_ID=cohort \
    SAMPLE_MANIFEST="$job_fixture/samples.tsv" \
    PARTITION_MANIFEST="$job_fixture/partitions.tsv" \
    STEP08_ROOT="$job_fixture/step08" \
    OUTPUT_ROOT="$job_output_root" \
    RSCRIPT_BIN_OVERRIDE="$fake_r" \
    STEP09_R_SCRIPT="$repo_root/src/emrys/analyses/paired_cmh_candidate_ranking/step_09_cmh_editing_site_calling.R" \
    EXECUTE=0 \
    bash "$job" > "$job_fixture/dry.out"
grep -q -- '--analysis-id job-dry' "$job_fixture/dry.out" ||
    fail "SLURM dry-run did not forward the analysis ID"
grep -q -- '--control-condition EV' "$job_fixture/dry.out" ||
    fail "SLURM dry-run did not forward the default control"
grep -q -- '--treatment-condition PUM1' "$job_fixture/dry.out" ||
    fail "SLURM dry-run did not forward the default treatment"
grep -q -- '--rna-ref A' "$job_fixture/dry.out" ||
    fail "SLURM dry-run did not forward the default RNA reference"
grep -q -- '--rna-alt G' "$job_fixture/dry.out" ||
    fail "SLURM dry-run did not forward the default RNA alternate"
grep -q "Step 09 completed in dry-run mode" "$job_fixture/dry.out" ||
    fail "SLURM wrapper did not preserve dry-run mode"
[[ ! -e "$job_output_root/job-dry" ]] ||
    fail "SLURM dry-run created a final output directory"

job_marker="$job_fixture/fake-r.invoked"
job_args="$job_fixture/fake-r.args"
env \
    PATH="$tmp/bin:$PATH" \
    SLURM_SUBMIT_DIR="$job_fixture" \
    ANALYSIS_ID=job-execute \
    COHORT_ID=cohort \
    SAMPLE_MANIFEST="$job_fixture/samples.tsv" \
    PARTITION_MANIFEST="$job_fixture/partitions.tsv" \
    STEP08_ROOT="$job_fixture/step08" \
    OUTPUT_ROOT="$job_output_root" \
    RSCRIPT_BIN_OVERRIDE="$fake_r" \
    STEP09_R_SCRIPT="$repo_root/src/emrys/analyses/paired_cmh_candidate_ranking/step_09_cmh_editing_site_calling.R" \
    FAKE_R_MARKER="$job_marker" \
    FAKE_R_ARGS_LOG="$job_args" \
    EXECUTE=1 \
    bash "$job" > "$job_fixture/execute.out"
[[ -e "$job_marker" ]] || fail "SLURM execute mode did not invoke fake R"
grep -q -- '--execute' "$job_fixture/execute.out" ||
    fail "SLURM wrapper did not forward execute mode"
assert_arg_pair "$job_args" --analysis-id job-execute
assert_arg_pair "$job_args" --cohort-id cohort
assert_arg_pair "$job_args" --control-condition EV
assert_arg_pair "$job_args" --treatment-condition PUM1
assert_arg_pair "$job_args" --rna-ref A
assert_arg_pair "$job_args" --rna-alt G
assert_arg_pair "$job_args" --min-sample-dp 1
assert_arg_pair "$job_args" --mean-dp-threshold 50
assert_arg_pair "$job_args" --fdr-threshold 0.05
assert_arg_pair "$job_args" --common-or-threshold 1.2
assert_arg_pair "$job_args" --absolute-difference-threshold 0.005
assert_arg_pair "$job_args" --background-max-fraction 0.01
for job_path in \
    "$job_output_root/job-execute/job-execute.cmh_all_sites.tsv" \
    "$job_output_root/job-execute/job-execute.cmh_significant_sites.tsv" \
    "$job_output_root/job-execute/job-execute.cmh_summary.tsv" \
    "$job_output_root/job-execute/job-execute.mutation_spectrum.tsv" \
    "$job_output_root/job-execute/job-execute.mutation_spectrum.pdf" \
    "$job_output_root/job-execute/job-execute.depth_delta.pdf"
do
    [[ -s "$job_path" ]] || fail "SLURM execute output is missing: $job_path"
done
assert_no_scratch "$job_output_root" job-execute

expect_fail "EXECUTE must be 0 or 1" \
    env \
    PATH="$tmp/bin:$PATH" \
    SLURM_SUBMIT_DIR="$job_fixture" \
    EXECUTE=2 \
    bash "$job"

bash -n "$script"
bash -n "$job"
printf 'PASS: Step 09 shell wrapper tests\n'
