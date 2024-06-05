import json
import sys
import os
import logging
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

# Configure logging
logging.basicConfig(level=os.getenv("CLLM_LOGLEVEL"))

# Load configuration from environment variables or use defaults
CLLM_DIR = os.getenv("CLLM_DIR", f"{os.getcwd()}/.cllm")

def faiss_save(data: str, index_name: str, model_name: str) -> None:
    try:
        # Parse input data
        data = json.loads(data)
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON data: {e}")
        return

    index_path = f"{CLLM_DIR}/rag/{index_name}"

    # Create documents from data
    documents = [
        Document(page_content=item.get("page_content"), metadata=item.get("metadata")) for item in data
    ]

    # Create embeddings
    embeddings = OpenAIEmbeddings(model=model_name)

    # Check if FAISS index exists
    if os.path.exists(index_path):
        db = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
        db.add_documents(documents)
    else:
        # Create FAISS index from documents
        db = FAISS.from_documents(documents, embeddings)
    
    logging.info(f"Number of documents in the index: {db.index.ntotal}")

    # Save FAISS index locally
    db.save_local(index_path)
    logging.info("FAISS index saved locally.")

def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Save data to FAISS index")
    parser.add_argument('-i', '--index', type=str, default="faiss_index", help='Path to save the FAISS index')
    parser.add_argument('-m', '--model', type=str, default="text-embedding-3-small", help='Name of the OpenAI embedding model to use')
    parser.add_argument("data", nargs='?', default=None)
    args = parser.parse_args()

    # Get data from stdin
    input_data = sys.stdin.read()

    faiss_save(input_data, args.index, args.model)

if __name__ == "__main__":
    main()
