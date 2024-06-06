#!/bin/bash

cllm gpt/4o \
-pr "You are a graphic designer" \
-pc "A logo for an Open Source project" \
-pi "Describe a picture of a cute clam. This clam like to dress like differet types of people." \
-po "A text to image prompt describe. The image should be a simple vector logo. Keep the prompt short and concise." \
-pe "A cute clam dressed like a princess, logo, vector, simple design" | cllm-gen-dalle \
| jq -r '.[0]' | xargs open