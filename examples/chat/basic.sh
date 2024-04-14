#!/bin/bash

CHAT_CONTEXT="chat-basic"

echo "When you are done chatting type 'exit' to exit."
while true; do
    read -p "You: " input
    if [ "$input" == "exit" ]; then
        break
    fi
    response=$(cllm -c ${CHAT_CONTEXT} gpt/4o "${input}")
    echo "Bot: ${response}"
done