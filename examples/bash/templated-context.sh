#!/usr/bin/env bash
# Showcase templated context commands with --var overrides.
# Usage: ./templated-context.sh <file-path> [--branch BRANCH] [--verbose]
#
# Examples:
#   ./templated-context.sh README.md
#   ./templated-context.sh src/cllm/cli.py --branch main --verbose
#
# Environment overrides:
#   CLLM_MODEL             - Model to use (default: gpt-4)
#   CLLM_TEMPLATE_PROMPT   - Custom prompt for the review
#   CLLM_TEMPLATE_BRANCH   - Default comparison branch (default: main)
#   CLLM_EXTRA_FLAGS       - Extra flags passed to cllm
#   CLLM_EXAMPLE_DRY_RUN=1 - Skip cllm invocation and print the command

set -euo pipefail

usage() {
  cat <<EOF
Usage: $(basename "$0") <file-path> [--branch BRANCH] [--verbose]

Variables inside context commands are rendered with Jinja2 templates using
the CLI's --var flags. The script injects:
  - ls -lh {{ FILE_PATH }}
  - cat {{ FILE_PATH }} (numbered when --verbose is set)
  - git diff {{ BRANCH }}..HEAD -- {{ FILE_PATH }} with optional --stat
EOF
  exit 1
}

if [[ $# -eq 0 ]]; then
  usage
fi

file_path=""
branch="${CLLM_TEMPLATE_BRANCH:-main}"
verbose=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --branch)
      if [[ $# -lt 2 ]]; then
        echo "Error: --branch requires a value." >&2
        usage
      fi
      branch="$2"
      shift 2
      ;;
    --verbose)
      verbose=true
      shift
      ;;
    -h|--help)
      usage
      ;;
    --*)
      echo "Error: Unknown option '$1'." >&2
      usage
      ;;
    *)
      if [[ -z "${file_path}" ]]; then
        file_path="$1"
        shift
      else
        echo "Error: Unexpected argument '$1'." >&2
        usage
      fi
      ;;
  esac
done

if [[ -z "${file_path}" ]]; then
  echo "Error: file path is required." >&2
  usage
fi

if [[ ! -f "${file_path}" ]]; then
  echo "Error: '${file_path}' does not exist or is not a regular file." >&2
  exit 1
fi

if ! command -v cllm >/dev/null 2>&1; then
  echo "Error: cllm command not found on PATH. Activate the environment where CLLM is installed." >&2
  exit 1
fi

if ! git rev-parse --show-toplevel >/dev/null 2>&1; then
  echo "Error: not inside a git repository." >&2
  exit 1
fi

model="${CLLM_MODEL:-gpt-4}"
prompt="${CLLM_TEMPLATE_PROMPT:-"Review ${file_path} and highlight risks, missing tests, and refactor opportunities."}"

extra_flags=()
if [[ -n "${CLLM_EXTRA_FLAGS:-}" ]]; then
  # shellcheck disable=SC2206
  extra_flags=(${CLLM_EXTRA_FLAGS})
fi

verbose_value="false"
if [[ "${verbose}" == "true" ]]; then
  verbose_value="true"
fi

template_vars=(
  --var "FILE_PATH=${file_path}"
  --var "BRANCH=${branch}"
  --var "VERBOSE=${verbose_value}"
)

context_exec=(
  --exec "ls -lh {{ FILE_PATH | shellquote }}"
  --exec "cat {{ FILE_PATH | shellquote }} {% if VERBOSE %}| nl{% endif %}"
  --exec "git diff {{ BRANCH | shellquote }}..HEAD -- {{ FILE_PATH | shellquote }} {% if VERBOSE %}--stat{% endif %}"
)

cmd=(cllm "${prompt}" --model "${model}")

if ((${#extra_flags[@]} > 0)); then
  cmd+=("${extra_flags[@]}")
fi

cmd+=("${template_vars[@]}")
cmd+=("${context_exec[@]}")

if [[ "${CLLM_EXAMPLE_DRY_RUN:-0}" == "1" ]]; then
  printf "[dry-run]"
  for arg in "${cmd[@]}"; do
    printf " %q" "${arg}"
  done
  printf "\n"
  exit 0
fi

"${cmd[@]}"
