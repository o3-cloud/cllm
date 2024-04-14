#!/bin/bash

TMP_PATH=tmp

mkdir -p ${TMP_PATH}

cllm \
--prompt-output "markdown format" \
--prompt-example "$(cat << EOF
# Title

Paragraph1

Paragraph2

Paragraph3
EOF
)" \
--prompt-instructions "Write a story"  \
gpt/4o > ${TMP_PATH}/my-story.md

cat ${TMP_PATH}/my-story.md | cllm \
--schema graph \
gpt/4o > ${TMP_PATH}/story-graph.json

cat ${TMP_PATH}/story-python.json | cllm \
--schema python \
--prompt-instructions "Write a program that takes this json graph data in from stdin and visualizes it" \
gpt/4o > ${TMP_PATH}/story-python.json

cat ${TMP_PATH}/story-python.json | \
cllm-output-code > ${TMP_PATH}/story-graph.py

cat ${TMP_PATH}/story-graph.json | python3 ${TMP_PATH}/story-graph.py