import json
import sys
import argparse
from langchain_text_splitters import RecursiveCharacterTextSplitter

def split_text_into_chunks(documents, chunk_size=100, chunk_overlap=20):
    """
    Splits the given text into chunks using RecursiveCharacterTextSplitter.
    Parameters:
    - documents (List[Dict[str, Union[str, Dict]]]): The documents to be split into chunks.
    - chunk_size (int): The maximum size of each chunk.
    - chunk_overlap (int): The number of characters that overlap between chunks.

    Returns:
    - List[Dict[str, Union[str, Dict]]]: A list of documents with split text chunks.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        is_separator_regex=False
    )
    
    chunks = []
    
    for document in documents:
        text = document.get("page_content", "")
        metadata = document.get("metadata", {})
        texts = text_splitter.split_text(text)
        
        for c in texts:
            chunks.append({
                "page_content": c,
                "metadata": metadata
            })
    
    return chunks

def main():
    parser = argparse.ArgumentParser(description="Split text into chunks")
    parser.add_argument('-s', '--chunk_size', type=int, default=1000, help='Size of each chunk')
    parser.add_argument('-o', '--chunk_overlap', type=int, default=10, help='Number of characters that overlap between chunks')
    args = parser.parse_args()

    # Read text from stdin
    documents = json.loads(sys.stdin.read())
    
    # Split the text into chunks
    chunks = split_text_into_chunks(documents, 
                                    chunk_size=args.chunk_size, 
                                    chunk_overlap=args.chunk_overlap)
    
    # Print the chunks
    print(json.dumps(chunks, indent=2))
    
if __name__ == "__main__":
    main()
