#!/bin/bash

SCRIPT_DIR=$(dirname "$0")
MODEL="gpt/4"

echo "To exit, type 'exit'"
while true; do
    read -p "$(tput setaf 2)You: $(tput sgr0)" input
    echo ""
    if [ "$input" == "exit" ]; then
        break
    fi
    availableFunctions=$(bash ${SCRIPT_DIR}/os_functions.sh -l)
    callFunction=$(cllm -pp "${availableFunctions}" -s function ${MODEL} "${input}")
    functionResult=$(echo "$callFunction" | bash ${SCRIPT_DIR}/os_functions.sh)
    echo -n "$(tput setaf 4)Bot: $(tput sgr0)"
    cllm --streaming -pc "${functionResult}" ${MODEL} "${input}"
    echo ""
done