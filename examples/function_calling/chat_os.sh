#!/bin/bash

SCRIPT_DIR=$(dirname "$0")

echo "To exit, type 'exit'"
while true; do
    read -p "You: " input
    if [ "$input" == "exit" ]; then
        break
    fi
    availableFunctions=$(bash ${SCRIPT_DIR}/os_functions.sh -l)
    callFunction=$(cllm -pp "${availableFunctions}" -s function gpt/4o "${input}")
    functionResult=$(echo "$callFunction" | bash ${SCRIPT_DIR}/os_functions.sh)
    echo "Bot: $(cllm -pc "${functionResult}" gpt/4o "${input}")"
done