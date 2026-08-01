#!/usr/bin/env bash
# Shared fail-closed checks for git_orchestration entry points.

die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

require_full_sha() {
  local value=$1
  local label=$2
  [[ $value =~ ^[0-9a-f]{40}$ ]] || die "$label must be a full SHA-1"
}

require_repo_relative_path() {
  local value=$1
  local label=$2
  [[ -n $value && $value != /* && $value != *$'\n'* && $value != *$'\r'* ]] ||
    die "$label must be a single-line repository-relative path"
  [[ $value != :* ]] || die "$label must not use Git pathspec magic"
  [[ $value != */ && $value != *//* ]] ||
    die "$label contains an empty path component"
  case "/$value/" in
    */./*|*/../*) die "$label contains an invalid path component" ;;
  esac
}

require_fragment_path() {
  local value=$1
  require_repo_relative_path "$value" 'fragment path'
  [[ $value =~ ^docs/fragments/[A-Z][A-Z0-9]*-[A-Z0-9-]+\.md$ ]] ||
    die 'fragment path must use docs/fragments/<FRAGMENT-ID>.md'
  [[ $value != docs/fragments/README.md ]] || die 'fragment path must not be README.md'
}

literal_pathspec() {
  printf ':(top,literal)%s' "$1"
}

require_unique_values() {
  local label=$1
  shift
  local outer
  local inner
  local index=0
  for outer in "$@"; do
    local compare=0
    for inner in "$@"; do
      if [[ $outer = "$inner" && $compare -lt $index ]]; then
        die "$label contains a duplicate value: $outer"
      fi
      compare=$((compare + 1))
    done
    index=$((index + 1))
  done
}

require_worktree_root() {
  local repository=$1
  [[ $repository = /* ]] || die "repository path must be absolute: $repository"
  [[ -d $repository ]] || die "repository path is unavailable: $repository"
  local resolved
  resolved=$(cd "$repository" && pwd -P) || die "cannot resolve repository: $repository"
  local top
  top=$(git -C "$repository" rev-parse --show-toplevel) || die "not a Git worktree: $repository"
  [[ $top = "$resolved" ]] || die "repository is not the worktree root: $repository"
}

require_no_git_operation() {
  local repository=$1
  local marker
  for marker in CHERRY_PICK_HEAD MERGE_HEAD REVERT_HEAD BISECT_LOG \
    rebase-apply rebase-merge sequencer; do
    local marker_path
    marker_path=$(git -C "$repository" rev-parse \
      --path-format=absolute --git-path "$marker")
    [[ ! -e $marker_path ]] || die "Git operation state already exists: $marker"
  done
}

verify_checkout() {
  local repository=$1
  local branch=$2
  local expected_head=$3
  local cleanliness=${4:-clean}
  require_worktree_root "$repository"
  require_full_sha "$expected_head" 'expected HEAD'
  [[ $branch != refs/* && -n $branch ]] || die 'branch must be a short name'
  local branch_ref="refs/heads/$branch"
  [[ $(git -C "$repository" symbolic-ref --quiet --short HEAD) = "$branch" ]] ||
    die "unexpected branch in $repository"
  [[ $(git -C "$repository" show-ref --verify --hash "$branch_ref") = "$expected_head" ]] ||
    die "local ref moved: $branch_ref"
  [[ $(git -C "$repository" rev-parse HEAD) = "$expected_head" ]] ||
    die "HEAD moved in $repository"
  if [[ $cleanliness = clean ]]; then
    [[ -z $(git -C "$repository" status --porcelain=v1 --untracked-files=all) ]] ||
      die "worktree is not clean: $repository"
  elif [[ $cleanliness != allow-dirty ]]; then
    die "invalid cleanliness mode: $cleanliness"
  fi
}

verify_remote_ref() {
  local repository=$1
  local remote=$2
  local branch_ref=$3
  local expected=$4
  local output
  local status=0
  output=$(git -C "$repository" ls-remote --exit-code --heads "$remote" "$branch_ref") ||
    status=$?
  if [[ $expected = ABSENT ]]; then
    [[ $status -eq 2 && -z $output ]] || die "remote ref exists: $branch_ref"
    return
  fi
  require_full_sha "$expected" 'expected remote SHA'
  [[ $status -eq 0 ]] || die "remote ref is unavailable: $branch_ref"
  [[ $output = "$expected"$'\t'"$branch_ref" ]] || die "remote ref moved: $branch_ref"
}

verify_single_child() {
  local repository=$1
  local parent_sha=$2
  local child_sha=$3
  require_full_sha "$parent_sha" 'parent SHA'
  require_full_sha "$child_sha" 'child SHA'
  [[ $(git -C "$repository" rev-list --parents -n 1 "$child_sha") = \
    "$child_sha $parent_sha" ]] || die 'commit is not one non-merge child of parent'
  [[ $(git -C "$repository" rev-list --count "$parent_sha..$child_sha") -eq 1 ]] ||
    die 'commit range does not contain exactly one commit'
}

verify_ancestor() {
  local repository=$1
  local ancestor=$2
  local descendant=$3
  require_full_sha "$ancestor" 'ancestor SHA'
  require_full_sha "$descendant" 'descendant SHA'
  git -C "$repository" merge-base --is-ancestor "$ancestor" "$descendant" ||
    die "$ancestor is not an ancestor of $descendant"
}

commit_patch_id() {
  local repository=$1
  local commit_sha=$2
  local patch_id
  patch_id=$(git -C "$repository" show --pretty=format: --no-ext-diff --binary \
    "$commit_sha" | git patch-id --stable | awk 'NR == 1 {print $1}') ||
    die "could not calculate patch identity for $commit_sha"
  [[ -n $patch_id ]] || die "commit has no patch identity: $commit_sha"
  printf '%s\n' "$patch_id"
}

require_regular_message_file() {
  local message_file=$1
  [[ -f $message_file && ! -L $message_file ]] ||
    die "message file must be a regular non-symlink: $message_file"
}

require_fragment_identity() {
  local repository=$1
  local commit_sha=$2
  local fragment_path=$3
  local integration_id=$4
  shift 4
  require_fragment_path "$fragment_path"
  require_unique_values 'request IDs' "$@"
  [[ $# -gt 0 ]] || die 'at least one request ID is required'
  local filename=${fragment_path##*/}
  filename=${filename%.md}
  [[ $integration_id = "$filename" ]] ||
    die 'integration ID does not match the fragment filename'
  local request_id
  for request_id in "$@"; do
    [[ -n $request_id && $request_id != *$'\n'* && \
      $request_id != *$'\r'* && $request_id != */* && \
      $request_id != *=* && $request_id != *'`'* && \
      $request_id != *';'* ]] ||
      die "invalid request ID: $request_id"
  done
  local fragment_text
  fragment_text=$(git -C "$repository" show "$commit_sha:$fragment_path") ||
    die 'fragment object is unavailable at the frozen commit'
  local actual_ids
  actual_ids=$(printf '%s\n' "$fragment_text" |
    sed -n 's/^## Request `\([^`][^`]*\)`$/\1/p' |
    LC_ALL=C sort)
  local expected_ids
  expected_ids=$(printf '%s\n' "$@" | LC_ALL=C sort)
  [[ $actual_ids = "$expected_ids" ]] ||
    die 'declared request IDs do not match the fragment requests'
}

require_message_trailer() {
  local message_file=$1
  local key=$2
  local expected=$3
  local count
  count=$(git interpret-trailers --parse <"$message_file" |
    awk -F ': ' -v key="$key" \
      '$1 == key {count++} END {print count+0}')
  [[ $count -eq 1 ]] || die "message must contain exactly one parsed $key trailer"
  local actual
  actual=$(git interpret-trailers --parse <"$message_file" |
    awk -F ': ' -v key="$key" \
      '$1 == key {sub(/^[^:]+: /, ""); print}')
  [[ $actual = "$expected" ]] || die "unexpected $key trailer"
}

require_request_trailers() {
  local message_file=$1
  shift
  local parsed
  parsed=$(git interpret-trailers --parse <"$message_file")
  require_request_trailer_text "$parsed" "$@"
}

commit_trailers() {
  local repository=$1
  local commit_sha=$2
  git -C "$repository" show -s --format=%B "$commit_sha" |
    git interpret-trailers --parse
}

require_commit_trailer() {
  local repository=$1
  local commit_sha=$2
  local key=$3
  local expected=$4
  local parsed
  parsed=$(commit_trailers "$repository" "$commit_sha")
  local count
  count=$(printf '%s\n' "$parsed" |
    awk -F ': ' -v key="$key" \
      '$1 == key {count++} END {print count+0}')
  [[ $count -eq 1 ]] || die "commit must contain exactly one parsed $key trailer"
  local actual
  actual=$(printf '%s\n' "$parsed" |
    awk -F ': ' -v key="$key" \
      '$1 == key {sub(/^[^:]+: /, ""); print}')
  [[ $actual = "$expected" ]] || die "unexpected committed $key trailer"
}

require_commit_request_trailers() {
  local repository=$1
  local commit_sha=$2
  shift 2
  local parsed
  parsed=$(commit_trailers "$repository" "$commit_sha")
  require_request_trailer_text "$parsed" "$@"
}

require_terminal_details() {
  local details=$1
  local outcome=$2
  local label=$3
  case $outcome in
    accept|partial)
      [[ $details =~ ^destination=([^;]+)\;\ effect=(.+)$ ]] ||
        die "$label needs nonempty destination and effect details"
      [[ ${BASH_REMATCH[1]} != none ]] ||
        die "$label needs a concrete destination"
      ;;
    reject)
      [[ $details =~ ^destination=none\;\ reason=(.+)$ ]] ||
        die "$label needs destination=none and a nonempty reason"
      ;;
    defer)
      [[ $details =~ ^destination=([^;]+)\;\ reason=(.+)$ ]] ||
        die "$label needs an implemented destination and nonempty reason"
      [[ ${BASH_REMATCH[1]} != none ]] ||
        die "$label needs an implemented destination"
      ;;
    stale)
      [[ $details =~ ^destination=none\;\ drift=(.+)$ ]] ||
        die "$label needs destination=none and nonempty drift"
      ;;
    *) die "$label has an invalid terminal disposition" ;;
  esac
}

require_subset_label() {
  local subset_id=$1
  local label=$2
  [[ -n $subset_id && $subset_id != *$'\n'* && \
    $subset_id != *$'\r'* && $subset_id != */* && \
    $subset_id != *=* && $subset_id != *'`'* && \
    $subset_id != *';'* ]] || die "invalid $label: $subset_id"
}

require_request_trailer_text() {
  local parsed=$1
  shift
  [[ $# -gt 0 ]] || die 'at least one request ID is required'
  require_unique_values 'request IDs' "$@"
  local total
  total=$(printf '%s\n' "$parsed" |
    awk -F ': ' '$1 == "Fragment-Request-Disposition" {count++} END {print count+0}')
  [[ $total -eq $# ]] ||
    die 'request-disposition trailer count does not match the declared request IDs'

  local global_accepted
  local global_residual
  global_accepted=$(printf '%s\n' "$parsed" |
    awk -F ': ' '$1 == "Fragment-Accepted-Subset" {count++} END {print count+0}')
  global_residual=$(printf '%s\n' "$parsed" |
    awk -F ': ' '$1 == "Fragment-Residual-Disposition" {count++} END {print count+0}')
  local accounted_accepted=0
  local accounted_residual=0
  local request_id
  for request_id in "$@"; do
    local values
    values=$(printf '%s\n' "$parsed" | awk -F ': ' -v id="$request_id" \
      '$1 == "Fragment-Request-Disposition" && index($2, id "=") == 1 {
        sub(/^[^:]+: /, ""); print
      }')
    [[ $(printf '%s\n' "$values" | awk 'NF {count++} END {print count+0}') -eq 1 ]] ||
      die "record must contain one disposition for request $request_id"
    local outcome=${values#"$request_id="}
    outcome=${outcome%%;*}
    case $outcome in
      accept|partial|reject|defer|stale) ;;
      *) die "request $request_id has an invalid terminal disposition" ;;
    esac
    local disposition_prefix="$request_id=$outcome; "
    [[ $values = "$disposition_prefix"* ]] ||
      die "request $request_id disposition lacks a structured detail"
    require_terminal_details \
      "${values#"$disposition_prefix"}" "$outcome" "request $request_id"

    local accepted_count
    local residual_count
    accepted_count=$(printf '%s\n' "$parsed" | awk -F ': ' -v id="$request_id" \
      '$1 == "Fragment-Accepted-Subset" && index($2, id "/") == 1 {
        count++
      } END {print count+0}')
    residual_count=$(printf '%s\n' "$parsed" | awk -F ': ' -v id="$request_id" \
      '$1 == "Fragment-Residual-Disposition" && index($2, id "/") == 1 {
        count++
      } END {print count+0}')
    accounted_accepted=$((accounted_accepted + accepted_count))
    accounted_residual=$((accounted_residual + residual_count))
    if [[ $outcome = partial ]]; then
      [[ $accepted_count -gt 0 && $residual_count -gt 0 ]] ||
        die "partial request $request_id needs accepted and residual subset records"
      local accepted_values
      accepted_values=$(printf '%s\n' "$parsed" | awk -F ': ' -v id="$request_id" \
        '$1 == "Fragment-Accepted-Subset" && index($2, id "/") == 1 {
          sub(/^[^:]+: /, ""); print
        }')
      local accepted_value
      while IFS= read -r accepted_value; do
        local accepted_remainder=${accepted_value#"$request_id/"}
        [[ $accepted_remainder != "$accepted_value" && \
          $accepted_remainder = *'; destination='* ]] ||
          die "partial request $request_id has a malformed accepted subset"
        local accepted_subset=${accepted_remainder%%;*}
        require_subset_label "$accepted_subset" 'accepted subset ID'
        local accepted_destination=${accepted_remainder#"$accepted_subset; destination="}
        [[ $accepted_destination != "$accepted_remainder" && \
          -n $accepted_destination && $accepted_destination != none && \
          $accepted_destination != *';'* ]] ||
          die "partial request $request_id has a malformed accepted subset destination"
      done <<<"$accepted_values"
      local residual_values
      residual_values=$(printf '%s\n' "$parsed" | awk -F ': ' -v id="$request_id" \
        '$1 == "Fragment-Residual-Disposition" && index($2, id "/") == 1 {
          sub(/^[^:]+: /, ""); print
        }')
      local residual_value
      while IFS= read -r residual_value; do
        local residual_remainder=${residual_value#"$request_id/"}
        [[ $residual_remainder != "$residual_value" && \
          $residual_remainder = ?*"="* ]] ||
          die "partial request $request_id has a malformed residual subset"
        local residual_subset=${residual_remainder%%=*}
        require_subset_label "$residual_subset" 'residual subset ID'
        local residual_outcome=${residual_remainder#*=}
        residual_outcome=${residual_outcome%%;*}
        case $residual_outcome in
          reject|defer|stale) ;;
          *) die "partial request $request_id has an invalid residual outcome" ;;
        esac
        local residual_prefix="$residual_subset=$residual_outcome; "
        [[ $residual_remainder = "$residual_prefix"* ]] ||
          die "partial request $request_id has malformed residual details"
        require_terminal_details \
          "${residual_remainder#"$residual_prefix"}" "$residual_outcome" \
          "residual $request_id/$residual_subset"
      done <<<"$residual_values"
    else
      [[ $accepted_count -eq 0 && $residual_count -eq 0 ]] ||
        die "non-partial request $request_id must not have subset records"
    fi
  done
  [[ $accounted_accepted -eq $global_accepted && \
    $accounted_residual -eq $global_residual ]] ||
    die 'subset trailers include an undeclared request ID'

  local duplicate_subset
  duplicate_subset=$(printf '%s\n' "$parsed" | awk -F ': ' '
    $1 == "Fragment-Accepted-Subset" {
      value=$2; sub(/;.*/, "", value)
      if (++seen[value] > 1) print value
    }
    $1 == "Fragment-Residual-Disposition" {
      value=$2; sub(/=.*/, "", value)
      if (++seen[value] > 1) print value
    }
  ')
  [[ -z $duplicate_subset ]] || die "duplicate subset trailer: $duplicate_subset"
}

print_command() {
  printf 'DRY-RUN:'
  printf ' %q' "$@"
  printf '\n'
}
