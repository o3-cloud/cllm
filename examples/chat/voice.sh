#!/bin/bash

CHAT_CONTEXT="chat-voice"

while true; do
    echo -ne "Listening...\r"
    AUDIO_FILE="$(cllm-listen)"
    echo -ne "Thinking...\r"
    RESPONSE="$(cllm-speech-text -f "${AUDIO_FILE}" | cllm -c "chat-voice" groq/llama)"
    echo -ne "Talking...\r"
    echo "${RESPONSE}" | say
    rm -rf "${AUDIO_FILE}"
done