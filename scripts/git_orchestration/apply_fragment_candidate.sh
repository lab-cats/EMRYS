#!/usr/bin/env bash
# Rebind and apply one frozen fragment candidate; dry-run is the default.
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
# shellcheck source=_common.sh
source "$script_dir/_common.sh"

usage() {
  cat <<'EOF'
Usage: apply_fragment_candidate.sh [options]

Required:
  --candidate-repo PATH       --candidate-branch NAME
  --candidate SHA             --base SHA
  --fragment PATH             --expected-change STATUS PATH (repeat)
  --allowed-path PATH (repeat)
  --canonical-repo PATH       --canonical-branch NAME
  --parent SHA

Optional:
  --remote NAME               Git remote name (default: origin)
  --execute                   Perform the cherry-pick; default prints it only
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
remote=origin
execute=0
expected_changes=()
allowed_paths=()

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

verify_checkout "$canonical_repo" "$canonical_branch" "$parent_sha" clean
require_no_git_operation "$canonical_repo"
verify_ancestor "$canonical_repo" "$base_sha" "$parent_sha"
canonical_ref="refs/heads/$canonical_branch"
verify_remote_ref "$canonical_repo" "$remote" "$canonical_ref" "$parent_sha"

if [[ $execute -eq 0 ]]; then
  print_command git -C "$canonical_repo" cherry-pick "$candidate_sha"
  printf 'PASS application preconditions; no Git state changed\n'
  exit 0
fi

if ! git -C "$canonical_repo" cherry-pick "$candidate_sha"; then
  git -C "$canonical_repo" status --porcelain=v2 >&2 || true
  git -C "$canonical_repo" diff --name-only --diff-filter=U >&2 || true
  git -C "$canonical_repo" diff --cc >&2 || true
  cherry_pick_head=$(git -C "$canonical_repo" rev-parse \
    --path-format=absolute --git-path CHERRY_PICK_HEAD)
  if [[ -f $cherry_pick_head ]]; then
    git -C "$canonical_repo" cherry-pick --abort
    verify_checkout "$canonical_repo" "$canonical_branch" "$parent_sha" clean
    die 'cherry-pick conflicted; abort restored the exact clean parent'
  fi
  die 'cherry-pick failed without an abortable conflict; preserve the worktree'
fi

applied_sha=$(git -C "$canonical_repo" rev-parse HEAD)
verify_single_child "$canonical_repo" "$parent_sha" "$applied_sha"
verify_checkout "$canonical_repo" "$canonical_branch" "$applied_sha" clean
printf 'PASS applied fragment candidate: %s\n' "$applied_sha"
