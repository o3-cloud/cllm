#!/usr/bin/env bash
# Create a daily digest using cllm. Intended for cron or scheduled jobs.
# Usage: ./cron-digest.sh [--dry-run] [output_file]
# Environment overrides:
#   CLLM_DIGEST_SOURCE_CMD  - Command producing digest input (default: git log --since="24 hours ago" --pretty=format:"- %s")
#   CLLM_DIGEST_TITLE       - Title included in the prompt (default: "Daily engineering digest")
#   CLLM_DIGEST_MODEL       - Model to use (default: gpt-3.5-turbo)
#   CLLM_DIGEST_CONVERSATION- Conversation ID for continuity (default: daily-digest)
#   CLLM_EXTRA_FLAGS        - Extra flags passed to cllm
#   CLLM_EXAMPLE_DRY_RUN=1  - Skip cllm invocation and log command instead
# The script exits early if the source command returns no data.

set -euo pipefail

if ! command -v cllm >/dev/null 2>&1; then
  echo "Error: cllm command not found on PATH. Activate the environment where CLLM is installed." >&2
  exit 1
fi

dry_run=0
output_path=""

while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --dry-run)
      dry_run=1
      shift
      ;;
    *)
      if [[ -n "${output_path}" ]]; then
        echo "Error: multiple output destinations provided." >&2
        exit 1
      fi
      output_path="$1"
      shift
      ;;
  esac
done

dry_run=$((dry_run | ${CLLM_EXAMPLE_DRY_RUN:-0}))

source_cmd=${CLLM_DIGEST_SOURCE_CMD:-'git log --since="24 hours ago" --pretty=format:"- %s"'}
digest_input=$(/usr/bin/env bash -lc "${source_cmd}" || true)

if [[ -z "${digest_input}" ]]; then
  echo "Digest source produced no entries; skipping summary."
  exit 0
fi

title="${CLLM_DIGEST_TITLE:-Daily engineering digest}"
model="${CLLM_DIGEST_MODEL:-gpt-3.5-turbo}"
conversation="${CLLM_DIGEST_CONVERSATION:-daily-digest}"
extra_flags=()
if [[ -n "${CLLM_EXTRA_FLAGS:-}" ]]; then
  # shellcheck disable=SC2206
  extra_flags=(${CLLM_EXTRA_FLAGS})
fi

prompt=$(cat <<EOF
Summarize the updates below into "${title}".
Group related work, call out blockers, and suggest next steps when obvious.
EOF
)

payload=$(printf "%s\n\n%s\n" "${prompt}" "${digest_input}")

if [[ "${dry_run}" -eq 1 ]]; then
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

if [[ -n "${output_path}" ]]; then
  mkdir -p "$(dirname "${output_path}")"
  printf "%s" "${payload}" | "${cmd[@]}" >"${output_path}"
  echo "Digest written to ${output_path}"
else
  printf "%s" "${payload}" | "${cmd[@]}"
fi
