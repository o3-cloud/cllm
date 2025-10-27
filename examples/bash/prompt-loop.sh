#!/usr/bin/env bash
# Interactive prompt loop that maintains a named conversation.
# Usage: ./prompt-loop.sh [conversation_id]
# Environment overrides:
#   CLLM_CONVERSATION   - Conversation ID (default: first arg or prompt-loop-YYYYMMDD)
#   CLLM_MODEL          - Model to use (default: gpt-3.5-turbo)
#   CLLM_EXTRA_FLAGS    - Extra flags passed to cllm (e.g., "--json-schema-file path")
#   CLLM_EXAMPLE_DRY_RUN=1 skips calling cllm and logs the would-be command.

set -euo pipefail

if ! command -v cllm >/dev/null 2>&1; then
  echo "Error: cllm command not found on PATH. Activate the environment where CLLM is installed." >&2
  exit 1
fi

conversation_id="${1:-"${CLLM_CONVERSATION:-"prompt-loop-$(date +%Y%m%d)"}"}"
model="${CLLM_MODEL:-gpt-5-mini}"

extra_flags=()
if [[ -n "${CLLM_EXTRA_FLAGS:-}" ]]; then
  # shellcheck disable=SC2206
  extra_flags=(${CLLM_EXTRA_FLAGS})
fi

echo "Starting conversation '${conversation_id}' (model: ${model}). Type ':quit' to exit."

while true; do
  printf "> "
  if ! IFS= read -r prompt; then
    echo
    break
  fi

  [[ -z "${prompt}" ]] && continue
  [[ "${prompt}" == ":quit" || "${prompt}" == ":exit" ]] && break

  if [[ "${CLLM_EXAMPLE_DRY_RUN:-0}" == "1" ]]; then
    printf "[dry-run] cllm %q --conversation %q --model %q" "${prompt}" "${conversation_id}" "${model}"
    if ((${#extra_flags[@]} > 0)); then
      printf ' %s' "${extra_flags[@]}"
    fi
    printf "\n"
    continue
  fi

  if ((${#extra_flags[@]} > 0)); then
    cllm "${prompt}" --conversation "${conversation_id}" --model "${model}" "${extra_flags[@]}"
  else
    cllm "${prompt}" --conversation "${conversation_id}" --model "${model}"
  fi
  echo
done

echo "Conversation '${conversation_id}' closed."
