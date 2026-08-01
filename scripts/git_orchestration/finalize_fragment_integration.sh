#!/usr/bin/env bash
# Finalize one applied fragment exchange; dry-run is the default.
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
# shellcheck source=_common.sh
source "$script_dir/_common.sh"

usage() {
  cat <<'EOF'
Usage: finalize_fragment_integration.sh [options]

Required:
  --repo PATH                 --branch NAME
  --parent SHA                --applied SHA
  --fragment PATH             --final-path PATH (repeat)
  --message-file PATH         --integration-id ID
  --source-repo PATH          --source-sha SHA
  --source-ref REF
  --base SHA                  --request-id ID (repeat)

Optional:
  --remote NAME               Git remote name (default: origin)
  --execute                   Stage, remove, and amend; default prints only
EOF
}

repository=
branch=
parent_sha=
applied_sha=
fragment_path=
message_file=
integration_id=
source_repo=
source_sha=
source_ref=
base_sha=
remote=origin
execute=0
final_paths=()
request_ids=()

while (($#)); do
  case $1 in
    --repo) repository=${2-}; shift 2 ;;
    --branch) branch=${2-}; shift 2 ;;
    --parent) parent_sha=${2-}; shift 2 ;;
    --applied) applied_sha=${2-}; shift 2 ;;
    --fragment) fragment_path=${2-}; shift 2 ;;
    --final-path) final_paths+=("${2-}"); shift 2 ;;
    --message-file) message_file=${2-}; shift 2 ;;
    --integration-id) integration_id=${2-}; shift 2 ;;
    --source-repo) source_repo=${2-}; shift 2 ;;
    --source-sha) source_sha=${2-}; shift 2 ;;
    --source-ref) source_ref=${2-}; shift 2 ;;
    --base) base_sha=${2-}; shift 2 ;;
    --request-id) request_ids+=("${2-}"); shift 2 ;;
    --remote) remote=${2-}; shift 2 ;;
    --execute) execute=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "unknown argument: $1" ;;
  esac
done

[[ -n $repository && -n $branch && -n $parent_sha && -n $applied_sha ]] ||
  die 'repository, branch, parent, and applied SHA are required'
[[ -n $fragment_path && ${#final_paths[@]} -gt 0 ]] ||
  die 'fragment and at least one final path are required'
[[ -n $message_file && -n $integration_id && -n $source_repo && \
  -n $source_sha ]] ||
  die 'message file, integration ID, source repository, and source SHA are required'
[[ -n $source_ref && -n $base_sha && ${#request_ids[@]} -gt 0 ]] ||
  die 'source ref, base, and at least one request ID are required'

verify_checkout "$repository" "$branch" "$applied_sha" allow-dirty
verify_single_child "$repository" "$parent_sha" "$applied_sha"
require_no_git_operation "$repository"
require_full_sha "$source_sha" 'source SHA'
require_full_sha "$base_sha" 'base SHA'
[[ $source_ref = refs/heads/* ]] || die 'source ref must be a full branch ref'
source_branch=${source_ref#refs/heads/}
[[ -n $source_branch ]] || die 'source ref must name a branch'
require_fragment_path "$fragment_path"
require_unique_values 'final paths' "${final_paths[@]}"
final_pathspecs=()
for final_candidate_path in "${final_paths[@]}"; do
  require_repo_relative_path "$final_candidate_path" 'final path'
  [[ $final_candidate_path != "$fragment_path" ]] ||
    die 'fragment must not be included in the final path set'
  final_pathspecs+=("$(literal_pathspec "$final_candidate_path")")
done
fragment_pathspec=$(literal_pathspec "$fragment_path")

verify_checkout "$source_repo" "$source_branch" "$source_sha" clean
require_no_git_operation "$source_repo"
verify_single_child "$source_repo" "$base_sha" "$source_sha"
verify_remote_ref "$source_repo" "$remote" "$source_ref" "$source_sha"
require_fragment_identity \
  "$source_repo" "$source_sha" "$fragment_path" "$integration_id" \
  "${request_ids[@]}"
require_fragment_identity \
  "$repository" "$applied_sha" "$fragment_path" "$integration_id" \
  "${request_ids[@]}"
git -C "$repository" cat-file -e "$applied_sha:$fragment_path" ||
  die 'fragment is absent from the applied candidate commit'
source_fragment_oid=$(git -C "$source_repo" rev-parse "$source_sha:$fragment_path")
applied_fragment_oid=$(git -C "$repository" rev-parse "$applied_sha:$fragment_path")
[[ $source_fragment_oid = "$applied_fragment_oid" ]] ||
  die 'applied fragment does not match the frozen source fragment'
[[ $(commit_patch_id "$source_repo" "$source_sha") = \
  "$(commit_patch_id "$repository" "$applied_sha")" ]] ||
  die 'applied commit patch does not match the frozen source candidate'
git -C "$repository" diff --cached --quiet ||
  die 'the real index already contains staged changes'

require_regular_message_file "$message_file"
message_blob=$(git hash-object -- "$message_file")
require_message_trailer "$message_file" Fragment-Integration-ID "$integration_id"
require_message_trailer "$message_file" Fragment-Source-SHA "$source_sha"
require_message_trailer "$message_file" Fragment-Source-Ref "$source_ref"
require_message_trailer "$message_file" Fragment-Base-SHA "$base_sha"
require_message_trailer "$message_file" Integration-Parent-SHA "$parent_sha"
require_message_trailer "$message_file" Fragment-Package-Outcome applied
require_request_trailers "$message_file" "${request_ids[@]}"

message_snapshot=
cleanup_temporary_files() {
  if [[ -n $message_snapshot ]]; then
    rm -f "$message_snapshot"
  fi
}
trap cleanup_temporary_files EXIT
expected_final_paths=$(printf '%s\n' "${final_paths[@]}" | LC_ALL=C sort)
tracked_worktree_paths=$(git -C "$repository" diff \
  --name-only --no-renames --no-ext-diff --no-textconv "$parent_sha" --)
untracked_worktree_paths=$(git -C "$repository" \
  ls-files --others --exclude-standard)
actual_final_paths=$(
  printf '%s\n%s\n' "$tracked_worktree_paths" "$untracked_worktree_paths" |
    awk -v fragment="$fragment_path" 'NF && $0 != fragment' |
    LC_ALL=C sort -u
)
[[ $actual_final_paths = "$expected_final_paths" ]] ||
  die 'working parent-to-result paths do not equal the explicit final path set'
git -C "$repository" diff --check "$parent_sha" --
expected_fragment_paths=$(printf '%s\n' docs/fragments/README.md "$fragment_path" |
  LC_ALL=C sort)
actual_fragment_paths=$(git -C "$repository" ls-tree -r --name-only \
  "$applied_sha" -- docs/fragments | LC_ALL=C sort)
[[ $actual_fragment_paths = "$expected_fragment_paths" ]] ||
  die 'applied tree contains an unexpected integration-fragment path'

if [[ $execute -eq 0 ]]; then
  print_command git -C "$repository" add -- "${final_pathspecs[@]}"
  print_command git -C "$repository" rm -- "$fragment_pathspec"
  print_command git -C "$repository" commit --amend --allow-empty -F "$message_file"
  printf 'PASS finalization preconditions; no Git state changed\n'
  exit 0
fi

require_regular_message_file "$message_file"
[[ $(git hash-object -- "$message_file") = "$message_blob" ]] ||
  die 'message file changed after validation'
message_snapshot=$(mktemp "${TMPDIR:-/tmp}/norad-fragment-message.XXXXXX") ||
  die 'could not create a temporary message snapshot'
cp "$message_file" "$message_snapshot"
[[ $(git hash-object -- "$message_snapshot") = "$message_blob" ]] ||
  die 'message file changed while it was copied'

git -C "$repository" add -- "${final_pathspecs[@]}"
git -C "$repository" rm -- "$fragment_pathspec"
[[ -z $(git -C "$repository" diff --name-only) ]] ||
  die 'unstaged changes remain; preserve the worktree for inspection'
[[ -z $(git -C "$repository" ls-files --others --exclude-standard) ]] ||
  die 'untracked paths remain; preserve the worktree for inspection'
git -C "$repository" diff --cached --check "$parent_sha" --

actual_final_paths=$(git -C "$repository" \
  diff --cached --name-only --no-renames "$parent_sha" -- | LC_ALL=C sort)
[[ $actual_final_paths = "$expected_final_paths" ]] ||
  die 'parent-to-index paths do not equal the explicit final path set'
[[ $(git -C "$repository" ls-files -- docs/fragments) = docs/fragments/README.md ]] ||
  die 'a candidate fragment would survive finalization'

git -C "$repository" commit --amend --allow-empty -F "$message_snapshot"
final_sha=$(git -C "$repository" rev-parse HEAD)
verify_single_child "$repository" "$parent_sha" "$final_sha"
verify_checkout "$repository" "$branch" "$final_sha" clean
git -C "$repository" diff --check "$parent_sha" "$final_sha" --
actual_final_paths=$(git -C "$repository" \
  diff --name-only --no-renames "$parent_sha" "$final_sha" -- | LC_ALL=C sort)
[[ $actual_final_paths = "$expected_final_paths" ]] ||
  die 'committed paths do not equal the explicit final path set'
[[ $(git -C "$repository" ls-files -- docs/fragments) = docs/fragments/README.md ]] ||
  die 'a candidate fragment survived the final commit'

require_commit_trailer "$repository" "$final_sha" Fragment-Integration-ID "$integration_id"
require_commit_trailer "$repository" "$final_sha" Fragment-Source-SHA "$source_sha"
require_commit_trailer "$repository" "$final_sha" Fragment-Source-Ref "$source_ref"
require_commit_trailer "$repository" "$final_sha" Fragment-Base-SHA "$base_sha"
require_commit_trailer "$repository" "$final_sha" Integration-Parent-SHA "$parent_sha"
require_commit_trailer "$repository" "$final_sha" Fragment-Package-Outcome applied
require_commit_request_trailers "$repository" "$final_sha" "${request_ids[@]}"
printf 'PASS finalized fragment integration: %s\n' "$final_sha"
