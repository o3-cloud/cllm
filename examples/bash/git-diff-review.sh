#!/usr/bin/env bash
# Generate a code review from a git diff using cllm.
# Usage: ./git-diff-review.sh [<git-diff-args>...]
# Examples:
#   ./git-diff-review.sh             # reviews staged changes (git diff --cached)
#   ./git-diff-review.sh main..HEAD  # reviews changes vs. main
# Environment overrides:
#   CLLM_MODEL               - Model to use (default: gpt-4)
#   CLLM_REVIEW_CONVERSATION - Conversation ID (default: code-review)
#   CLLM_REVIEW_PROMPT       - Custom instruction prefix
#   CLLM_EXTRA_FLAGS         - Extra flags passed to cllm
#   CLLM_EXAMPLE_DRY_RUN=1   - Skip cllm invocation and log command instead

set -euo pipefail

if ! command -v git >/dev/null 2>&1; then
  echo "Error: git command not found; run from within a git repository." >&2
  exit 1
fi

if ! git rev-parse --show-toplevel >/dev/null 2>&1; then
  echo "Error: not inside a git repository." >&2
  exit 1
fi

if ! command -v cllm >/dev/null 2>&1; then
  echo "Error: cllm command not found on PATH. Activate the environment where CLLM is installed." >&2
  exit 1
fi

if [[ "$#" -eq 0 ]]; then
  diff_args=(--cached)
else
  diff_args=("$@")
fi

diff_output="$(git diff "${diff_args[@]}")"

if [[ -z "${diff_output}" ]]; then
  echo "No changes detected for git diff ${diff_args[*]}."
  exit 0
fi

model="${CLLM_MODEL:-gpt-4}"
conversation="${CLLM_REVIEW_CONVERSATION:-code-review}"
review_prompt="${CLLM_REVIEW_PROMPT:-"You are reviewing a git diff. Highlight bugs, risky changes, missing tests, and refactoring opportunities. Provide actionable feedback in markdown."}"
extra_flags=()
if [[ -n "${CLLM_EXTRA_FLAGS:-}" ]]; then
  # shellcheck disable=SC2206
  extra_flags=(${CLLM_EXTRA_FLAGS})
fi

payload=$(printf "%s\n\n```diff\n%s\n```\n" "${review_prompt}" "${diff_output}")

if [[ "${CLLM_EXAMPLE_DRY_RUN:-0}" == "1" ]]; then
  printf "[dry-run] cllm --conversation %q --model %q" "${conversation}" "${model}"
  if ((${#extra_flags[@]} > 0)); then
    printf ' %s' "${extra_flags[@]}"
  fi
  printf " <<EOF\n%s\nEOF\n" "${payload}"
  exit 0
fi

cmd=(cllm --conversation "${conversation}" --model "${model}")
if ((${#extra_flags[@]} > 0)); then
  cmd+=("${extra_flags[@]}")
fi

printf "%s" "${payload}" | "${cmd[@]}"
