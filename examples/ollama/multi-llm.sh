#!/bin/bash

cllm l/llama "Write a story about a dog" | \
cllm gpt/3.5 "Summerize"