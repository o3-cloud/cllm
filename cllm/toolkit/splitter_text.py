import json
import sys
from langchain_text_splitters import RecursiveCharacterTextSplitter

def split_text_into_chunks(text, chunk_size=100, chunk_overlap=20, metadata=None):
    """
    Splits the given text into chunks using RecursiveCharacterTextSplitter.

    Parameters:
    - text (str): The text to be split into chunks.
    - chunk_size (int): The maximum size of each chunk.
    - chunk_overlap (int): The number of characters that overlap between chunks.
    - metadata (dict): Metadata to be associated with each chunk.

    Returns:
    - List[dict]: A list of dictionaries, each containing chunked text and metadata.
    """
    if metadata is None:
        metadata = {}
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        is_separator_regex=False
    )
    
    texts = text_splitter.split_text(text)

    return [{"page_content": c, "metadata": metadata} for c in texts]

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Split text into chunks")
    parser.add_argument('-s', '--chunk_size', type=int, default=100, help='Size of each chunk')
    parser.add_argument('-o', '--chunk_overlap', type=int, default=20, help='Number of characters that overlap between chunks')
    parser.add_argument('-m', '--metadata', type=json.loads, help='Associated metadata', default='{}')
    args = parser.parse_args()

    # Read text from stdin
    text = sys.stdin.read()
    
    # Split the text into chunks
    chunks = split_text_into_chunks(text, 
                                    chunk_size=args.chunk_size, 
                                    chunk_overlap=args.chunk_overlap,
                                    metadata=args.metadata)
    
    # Print the chunks
    print(json.dumps(chunks))
    
if __name__ == "__main__":
    main()
