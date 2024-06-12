import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any
from langchain_community.document_loaders import DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

def directory_load(directory: str, glob_pattern: str = "**/*", chunk_size: int = 1000, chunk_overlap: int = 10, use_multithreading: bool = True) -> List[Dict[str, Any]]:
    if not Path(directory).exists():
        logging.error(f"Directory {directory} does not exist.")
        return []
    
    loader = DirectoryLoader(directory, glob=glob_pattern, use_multithreading=use_multithreading, silent_errors=True)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        is_separator_regex=False
    )
    documents = loader.load_and_split(splitter)
    if not documents:
        logging.warning(f"No documents found in directory {directory}.")
    return documents

def convert_docs_to_json(documents: List[Dict[str, Any]]) -> str:
    docs_list = []
    for doc in documents:
        docs_list.append({
            "page_content": doc.page_content,
            "metadata": doc.metadata,
        })
    return json.dumps(docs_list, indent=2)

def save_json_to_file(json_data: str, output_file: str) -> None:
    with open(output_file, 'w') as f:
        f.write(json_data)
    logging.info(f"JSON data saved to {output_file}")

def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Load files from a directory")
    parser.add_argument('-d', '--directory', type=str, required=True, help='Directory to load files from')
    parser.add_argument('-g', '--glob_pattern', type=str, default="**/*", help='Glob pattern to match files')
    parser.add_argument('-s', '--chunk_size', type=int, default=1000, help='Size of each chunk')
    parser.add_argument('-o', '--chunk_overlap', type=int, default=10, help='Number of characters that overlap between chunks')
    parser.add_argument('-m', '--use_multithreading', type=bool, default=True, help='Use multithreading for loading files')
    parser.add_argument('-f', '--output_file', type=str, help='Output file for the JSON data')
    args = parser.parse_args()

    logging.basicConfig(level=os.environ.get("CLLM_LOGLEVEL"))

    documents = directory_load(args.directory, args.glob_pattern, args.chunk_size, args.chunk_overlap, args.use_multithreading)
    json_data = convert_docs_to_json(documents)

    if args.output_file:
        save_json_to_file(json_data, args.output_file)

    print(json_data)

if __name__ == "__main__":
    main()
