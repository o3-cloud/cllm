#!/bin/bash

CHAT_CONTEXT="chat-voice"

while true; do
    echo -ne "Listening...\r"
    AUDIO_FILE="$(cllm-listen)"
    echo -ne "Thinking...\r"
    screencapture -x screenshot.png
    RESPONSE="$(cllm-speech-text -f "${AUDIO_FILE}" | cllm -i 'screenshot.png' -c "chat-voice" gpt/4)"
    echo -ne "Talking...\r"
    echo $RESPONSE | say
    rm -rf "${AUDIO_FILE}"
done