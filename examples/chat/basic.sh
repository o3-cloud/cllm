#!/bin/bash

CHAT_CONTEXT="chat-basic"

echo "When you are done chatting type 'exit' to exit."
while true; do
    read -p "$(tput setaf 2)You: $(tput sgr0)" input
    if [ "$input" == "exit" ]; then
        break
    fi
    echo -n "$(tput setaf 4)Bot: $(tput sgr0)"
    cllm --streaming -c ${CHAT_CONTEXT} gpt/4o "${input}"
    echo ""
done