#!/bin/bash

RAG=promptingguide
URL="https://www.promptingguide.ai/"
K=5

RAG_DIR=${CLLM_DIR}/rag/${RAG}

mkdir -p tmp

if [ ! -d "${RAG_DIR}" ]; then
    echo "Scraper URL: ${URL}"
    cllm-load-sitemap -u "${URL}" > tmp/${RAG}-sitemap.json
    cat tmp/${RAG}-sitemap.json | cllm-load-webpager > tmp/${RAG}-scrape.json

    echo "Adding text to RAG store ${RAG}"
    cat tmp/${RAG}-scrape.json | cllm-splitter-docs > tmp/${RAG}-split.json
    cat tmp/${RAG}-split.json | cllm-vector-faiss-write -i "${RAG}"
fi


echo "When done, type 'exit' to quit"
while true; do
    read -p "You: " input
    if [ "$input" == "exit" ]; then
        break
    fi
    echo ""
    res="$(cllm-vector-faiss-load -k ${K} -i ${RAG} "${input}")"
    echo "Bot: $(cllm -pc "${res}" -t rag-qa gpt/4o "${input}")"
    echo ""
done