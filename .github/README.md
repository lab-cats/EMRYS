# GitHub integration

Repository automation and policy live here. The [workflows](workflows/)
run engineering checks against an exact revision. Their results establish
software behavior, not institutional, production, scientific, or biological proof.

## Hosted merge-rule observation

A September 22 source-bound review at `3a672fdf8e55b30efc63dea9aecc4a29d28a5f4d`
read rulesets `21180321` (Reviews) and `21339165` (no-push-master). Effective
`master` rules required PR review and CodeQL quality/coverage but exposed no
`required_status_checks`; both allowed OrganizationAdmin always-bypass. The
correction branch `codex/pr302-original-intent-corrections` had no effective
rules. Legacy protection endpoints returned 404, which does not negate rulesets.
This is a dated API observation, not current hosted configuration or an actual
merge-block test. No settings were changed. If a merge-policy correction is
selected, verify emitted check names and failed, cancelled, missing, intended-skip
and changed-head cases while preserving other protections and opt-in/stacked-PR
policy. The [frozen observation](https://github.com/lab-cats/EMRYS/blob/06f88dbca7161599d7445f8cb2bfedf58f377282/docs/tasks/polish-campaign.md#33-make-the-required-merge-checks-explicit)
retains the original query scope; it does not itself authorize a hosted change.
