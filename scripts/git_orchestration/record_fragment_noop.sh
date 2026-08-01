#!/usr/bin/env bash
# Record a terminal fragment exchange with no canonical tree change.
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
# shellcheck source=_common.sh
source "$script_dir/_common.sh"

usage() {
  cat <<'EOF'
Usage: record_fragment_noop.sh [options]

Required:
  --candidate-repo PATH       --candidate-branch NAME
  --candidate SHA             --base SHA
  --fragment PATH             --expected-change STATUS PATH (repeat)
  --allowed-path PATH (repeat)
  --canonical-repo PATH       --canonical-branch NAME
  --parent SHA                --message-file PATH
  --integration-id ID         --request-id ID (repeat)

Optional:
  --remote NAME               Git remote name (default: origin)
  --execute                   Create the empty commit; default prints only
EOF
}

candidate_repo=
candidate_branch=
candidate_sha=
base_sha=
fragment_path=
canonical_repo=
canonical_branch=
parent_sha=
message_file=
integration_id=
remote=origin
execute=0
expected_changes=()
allowed_paths=()
request_ids=()

while (($#)); do
  case $1 in
    --candidate-repo) candidate_repo=${2-}; shift 2 ;;
    --candidate-branch) candidate_branch=${2-}; shift 2 ;;
    --candidate) candidate_sha=${2-}; shift 2 ;;
    --base) base_sha=${2-}; shift 2 ;;
    --fragment) fragment_path=${2-}; shift 2 ;;
    --expected-change)
      (($# >= 3)) || die '--expected-change requires STATUS and PATH'
      expected_changes+=("$2" "$3")
      shift 3
      ;;
    --allowed-path) allowed_paths+=("${2-}"); shift 2 ;;
    --canonical-repo) canonical_repo=${2-}; shift 2 ;;
    --canonical-branch) canonical_branch=${2-}; shift 2 ;;
    --parent) parent_sha=${2-}; shift 2 ;;
    --message-file) message_file=${2-}; shift 2 ;;
    --integration-id) integration_id=${2-}; shift 2 ;;
    --request-id) request_ids+=("${2-}"); shift 2 ;;
    --remote) remote=${2-}; shift 2 ;;
    --execute) execute=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "unknown argument: $1" ;;
  esac
done

[[ -n $candidate_repo && -n $candidate_branch && -n $candidate_sha ]] ||
  die 'candidate repository, branch, and SHA are required'
[[ -n $base_sha && -n $fragment_path ]] || die 'base and fragment are required'
[[ ${#expected_changes[@]} -gt 0 && ${#allowed_paths[@]} -gt 0 ]] ||
  die 'expected changes and allowed paths are required'
[[ -n $canonical_repo && -n $canonical_branch && -n $parent_sha ]] ||
  die 'canonical repository, branch, and parent are required'
[[ -n $message_file && -n $integration_id && ${#request_ids[@]} -gt 0 ]] ||
  die 'message file, integration ID, and request IDs are required'

norad_python_bin=${NORAD_PYTHON_BIN:-python3}
candidate_command=(
  "$norad_python_bin" "$script_dir/validate_fragment_candidate.py"
  --repo "$candidate_repo"
  --branch "$candidate_branch"
  --base "$base_sha"
  --candidate "$candidate_sha"
  --fragment "$fragment_path"
  --remote "$remote"
)
for ((index = 0; index < ${#expected_changes[@]}; index += 2)); do
  candidate_command+=(
    --expected-change "${expected_changes[index]}" "${expected_changes[index + 1]}"
  )
done
for allowed_candidate_path in "${allowed_paths[@]}"; do
  candidate_command+=(--allowed-path "$allowed_candidate_path")
done
"${candidate_command[@]}"
require_no_git_operation "$candidate_repo"
require_fragment_identity \
  "$candidate_repo" "$candidate_sha" "$fragment_path" "$integration_id" \
  "${request_ids[@]}"

verify_checkout "$canonical_repo" "$canonical_branch" "$parent_sha" clean
require_no_git_operation "$canonical_repo"
verify_ancestor "$canonical_repo" "$base_sha" "$parent_sha"
[[ $(git -C "$canonical_repo" ls-files -- docs/fragments) = docs/fragments/README.md ]] ||
  die 'a candidate fragment already exists in the canonical tree'
canonical_ref="refs/heads/$canonical_branch"
verify_remote_ref "$canonical_repo" "$remote" "$canonical_ref" "$parent_sha"

require_regular_message_file "$message_file"
message_blob=$(git hash-object -- "$message_file")
source_ref="refs/heads/$candidate_branch"
require_message_trailer "$message_file" Fragment-Integration-ID "$integration_id"
require_message_trailer "$message_file" Fragment-Source-SHA "$candidate_sha"
require_message_trailer "$message_file" Fragment-Source-Ref "$source_ref"
require_message_trailer "$message_file" Fragment-Base-SHA "$base_sha"
require_message_trailer "$message_file" Integration-Parent-SHA "$parent_sha"
require_message_trailer "$message_file" Fragment-Package-Outcome no-op
require_request_trailers "$message_file" "${request_ids[@]}"

if [[ $execute -eq 0 ]]; then
  print_command git -C "$canonical_repo" commit --allow-empty -F "$message_file"
  printf 'PASS no-op preconditions; no Git state changed\n'
  exit 0
fi

require_regular_message_file "$message_file"
[[ $(git hash-object -- "$message_file") = "$message_blob" ]] ||
  die 'message file changed after validation'
message_snapshot=$(mktemp "${TMPDIR:-/tmp}/norad-fragment-message.XXXXXX") ||
  die 'could not create a temporary message snapshot'
trap 'rm -f "$message_snapshot"' EXIT
cp "$message_file" "$message_snapshot"
[[ $(git hash-object -- "$message_snapshot") = "$message_blob" ]] ||
  die 'message file changed while it was copied'

git -C "$canonical_repo" commit --allow-empty -F "$message_snapshot"
final_sha=$(git -C "$canonical_repo" rev-parse HEAD)
verify_single_child "$canonical_repo" "$parent_sha" "$final_sha"
verify_checkout "$canonical_repo" "$canonical_branch" "$final_sha" clean
git -C "$canonical_repo" diff --quiet "$parent_sha" "$final_sha" -- ||
  die 'no-op integration changed the canonical tree; preserve the worktree'
[[ $(git -C "$canonical_repo" ls-files -- docs/fragments) = docs/fragments/README.md ]] ||
  die 'a candidate fragment survived the no-op integration'
require_commit_trailer "$canonical_repo" "$final_sha" Fragment-Integration-ID "$integration_id"
require_commit_trailer "$canonical_repo" "$final_sha" Fragment-Source-SHA "$candidate_sha"
require_commit_trailer "$canonical_repo" "$final_sha" Fragment-Source-Ref "$source_ref"
require_commit_trailer "$canonical_repo" "$final_sha" Fragment-Base-SHA "$base_sha"
require_commit_trailer "$canonical_repo" "$final_sha" Integration-Parent-SHA "$parent_sha"
require_commit_trailer "$canonical_repo" "$final_sha" Fragment-Package-Outcome no-op
require_commit_request_trailers "$canonical_repo" "$final_sha" "${request_ids[@]}"
printf 'PASS recorded no-op fragment integration: %s\n' "$final_sha"
