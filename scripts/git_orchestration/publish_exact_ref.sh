#!/usr/bin/env bash
# Publish one exact reviewed branch tip with canonical compare-and-swap checks.
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
# shellcheck source=_common.sh
source "$script_dir/_common.sh"

usage() {
  cat <<'EOF'
Usage: publish_exact_ref.sh [options]

Required:
  --repo PATH                 --branch NAME
  --parent SHA                --final SHA
  --expected-remote ABSENT|SHA
  --source-repo PATH          --source-ref REF
  --source-sha SHA            --fragment PATH
  --integration-id ID         --base SHA
  --outcome applied|no-op     --request-id ID (repeat)

Optional:
  --final-path PATH           Exact applied-package path (repeat)
  --remote NAME               Git remote name (default: origin)
  --execute                   Push the exact ref; default prints it only
EOF
}

repository=
branch=
parent_sha=
final_sha=
expected_remote=
source_repo=
source_ref=
source_sha=
fragment_path=
integration_id=
base_sha=
outcome=
remote=origin
execute=0
request_ids=()
final_paths=()

while (($#)); do
  case $1 in
    --repo) repository=${2-}; shift 2 ;;
    --branch) branch=${2-}; shift 2 ;;
    --parent) parent_sha=${2-}; shift 2 ;;
    --final) final_sha=${2-}; shift 2 ;;
    --expected-remote) expected_remote=${2-}; shift 2 ;;
    --source-repo) source_repo=${2-}; shift 2 ;;
    --source-ref) source_ref=${2-}; shift 2 ;;
    --source-sha) source_sha=${2-}; shift 2 ;;
    --fragment) fragment_path=${2-}; shift 2 ;;
    --integration-id) integration_id=${2-}; shift 2 ;;
    --base) base_sha=${2-}; shift 2 ;;
    --outcome) outcome=${2-}; shift 2 ;;
    --request-id) request_ids+=("${2-}"); shift 2 ;;
    --final-path) final_paths+=("${2-}"); shift 2 ;;
    --remote) remote=${2-}; shift 2 ;;
    --execute) execute=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "unknown argument: $1" ;;
  esac
done

[[ -n $repository && -n $branch && -n $parent_sha && -n $final_sha ]] ||
  die 'repository, branch, parent, and final SHA are required'
[[ -n $expected_remote && -n $source_repo && -n $source_ref && \
  -n $source_sha && -n $fragment_path ]] ||
  die 'expected remote state, source repository, and frozen source identity are required'
[[ -n $integration_id && -n $base_sha && -n $outcome ]] ||
  die 'integration ID, base, and package outcome are required'
[[ ${#request_ids[@]} -gt 0 ]] || die 'at least one request ID is required'
[[ $outcome = applied || $outcome = no-op ]] ||
  die 'package outcome must be applied or no-op'
[[ $source_ref = refs/heads/* ]] || die 'source ref must be a full branch ref'
canonical_ref="refs/heads/$branch"
[[ $source_ref != "$canonical_ref" ]] ||
  die 'frozen source ref and canonical publication ref must differ'
source_branch=${source_ref#refs/heads/}
[[ -n $source_branch ]] || die 'source ref must name a branch'
require_fragment_path "$fragment_path"
if ((${#final_paths[@]} > 0)); then
  require_unique_values 'final paths' "${final_paths[@]}"
  for final_candidate_path in "${final_paths[@]}"; do
    require_repo_relative_path "$final_candidate_path" 'final path'
    [[ $final_candidate_path != "$fragment_path" ]] ||
      die 'fragment must not be included in the final path set'
  done
fi

if [[ $outcome = applied ]]; then
  [[ ${#final_paths[@]} -gt 0 ]] ||
    die 'an applied package requires at least one exact final path'
else
  [[ ${#final_paths[@]} -eq 0 ]] ||
    die 'a no-op package must not declare final paths'
fi

verify_checkout "$repository" "$branch" "$final_sha" clean
verify_single_child "$repository" "$parent_sha" "$final_sha"
require_no_git_operation "$repository"
verify_checkout "$source_repo" "$source_branch" "$source_sha" clean
require_no_git_operation "$source_repo"
verify_single_child "$source_repo" "$base_sha" "$source_sha"
require_fragment_identity \
  "$source_repo" "$source_sha" "$fragment_path" "$integration_id" \
  "${request_ids[@]}"
git -C "$repository" diff --check "$parent_sha" "$final_sha" --
require_commit_trailer "$repository" "$final_sha" \
  Fragment-Integration-ID "$integration_id"
require_commit_trailer "$repository" "$final_sha" Fragment-Source-SHA "$source_sha"
require_commit_trailer "$repository" "$final_sha" Fragment-Source-Ref "$source_ref"
require_commit_trailer "$repository" "$final_sha" Fragment-Base-SHA "$base_sha"
require_commit_trailer "$repository" "$final_sha" Integration-Parent-SHA "$parent_sha"
require_commit_trailer "$repository" "$final_sha" Fragment-Package-Outcome "$outcome"
require_commit_request_trailers "$repository" "$final_sha" "${request_ids[@]}"
verify_remote_ref "$source_repo" "$remote" "$source_ref" "$source_sha"
verify_remote_ref "$repository" "$remote" "$canonical_ref" "$expected_remote"
if [[ $expected_remote != ABSENT ]]; then
  verify_ancestor "$repository" "$expected_remote" "$final_sha"
fi

expected_fragment_paths=docs/fragments/README.md
actual_fragment_paths=$(git -C "$repository" ls-tree -r --name-only \
  "$final_sha" -- docs/fragments | LC_ALL=C sort)
[[ $actual_fragment_paths = "$expected_fragment_paths" ]] ||
  die 'a candidate fragment survives the reviewed final tree'

if [[ $outcome = no-op ]]; then
  git -C "$repository" diff --quiet "$parent_sha" "$final_sha" -- ||
    die 'a no-op package changes the canonical tree'
else
  git -C "$repository" diff --quiet "$parent_sha" "$final_sha" -- &&
    die 'an applied package must change the canonical tree'
  expected_final_paths=$(printf '%s\n' "${final_paths[@]}" | LC_ALL=C sort)
  actual_final_paths=$(git -C "$repository" diff --name-only --no-renames \
    "$parent_sha" "$final_sha" -- | LC_ALL=C sort)
  [[ $actual_final_paths = "$expected_final_paths" ]] ||
    die 'committed paths do not equal the explicit final path set'
fi

if [[ $expected_remote = ABSENT ]]; then
  canonical_lease="--force-with-lease=$canonical_ref:"
else
  canonical_lease="--force-with-lease=$canonical_ref:$expected_remote"
fi
push_command=(
  git -C "$repository" push
  "$canonical_lease"
  "$remote"
  "$final_sha:$canonical_ref"
)

if [[ $execute -eq 0 ]]; then
  print_command "${push_command[@]}"
  print_command git -C "$repository" branch \
    --set-upstream-to="$remote/$branch" "$branch"
  printf 'PASS publication preconditions; no remote state changed\n'
  exit 0
fi

"${push_command[@]}"
verify_remote_ref "$repository" "$remote" "$canonical_ref" "$final_sha"
verify_remote_ref "$source_repo" "$remote" "$source_ref" "$source_sha"
verify_checkout "$repository" "$branch" "$final_sha" clean
verify_checkout "$source_repo" "$source_branch" "$source_sha" clean
git -C "$repository" branch --set-upstream-to="$remote/$branch" "$branch"
upstream_name=$(git -C "$repository" rev-parse --abbrev-ref --symbolic-full-name '@{upstream}')
[[ $upstream_name = "$remote/$branch" ]] || die "unexpected upstream: $upstream_name"
[[ $(git -C "$repository" rev-parse '@{upstream}') = "$final_sha" ]] ||
  die 'upstream SHA does not equal the reviewed final SHA'
[[ $(git -C "$repository" rev-list --left-right --count HEAD...'@{upstream}') = $'0\t0' ]] ||
  die 'local branch and upstream are not equal'
[[ -z $(git -C "$repository" status --porcelain=v1 --untracked-files=all) ]] ||
  die 'worktree became dirty during publication'
printf 'PASS published exact canonical ref: %s\n' "$final_sha"
