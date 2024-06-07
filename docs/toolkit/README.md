# Toolkit

This toolkit consists of several command-line tools designed to assist with various tasks such as text splitting, website scraping, FAISS indexing, code output, document splitting, file loading, image generation, and more. Below is a brief overview of each tool:

## Tools

[cllm-splitter-text](cllm-splitter-text.md): A tool for splitting text into chunks using the RecursiveCharacterTextSplitter.

cllm-load-website: A tool for scraping webpages and outputting their content in either text or HTML format.

cllm-vector-faiss-write: A script for saving data to a FAISS index using OpenAI embeddings.

cllm-output-code: A tool for processing and optionally installing dependencies for code provided via standard input.

cllm-splitter-docs: A tool for splitting text documents into smaller chunks using the RecursiveCharacterTextSplitter.

cllm-load-files: A tool for loading and splitting files into chunks.

cllm-vector-faiss-load: A tool for performing similarity searches on a FAISS index using OpenAI embeddings.

cllm-gen-dalle: A tool for generating images using OpenAI's DALL-E model.

cllm-repeater: A tool for processing a list of data items by repeatedly invoking the cllm command with specified arguments.

cllm-load-dir: A tool for loading files from a specified directory, splitting them into chunks, and optionally saving the processed data as a JSON file.

cllm-load-sitemap: A script for generating a sitemap from a given URL using Selenium WebDriver.

cllm-load-search-google: A tool for scraping Google search results based on specified queries and parameters.
For detailed usage instructions and examples, please refer to the individual documentation files for each tool.