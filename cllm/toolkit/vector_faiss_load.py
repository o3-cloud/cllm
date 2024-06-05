import json
import os
import logging
from typing import List, Dict, Any
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

# Configure logging
logging.basicConfig(level=os.getenv("CLLM_LOGLEVEL"))

# Environment variables for configuration
CLLM_DIR = os.getenv("CLLM_DIR", f"{os.getcwd()}/.cllm")

def load_faiss_index(faiss_index_name: str, model_name: str) -> FAISS:
    embeddings = OpenAIEmbeddings(model=model_name)
    faiss_index = f"{CLLM_DIR}/rag/{faiss_index_name}"
    
    if not os.path.exists(faiss_index):
        logging.error(f"FAISS index file {faiss_index} does not exist.")
        raise FileNotFoundError(f"FAISS index file {faiss_index} does not exist.")
    
    try:
        db = FAISS.load_local(faiss_index, embeddings, allow_dangerous_deserialization=True)
    except Exception as e:
        logging.error(f"Failed to load FAISS index: {e}")
        raise e
    
    return db

def perform_similarity_search(db: FAISS, query: str, results: int) -> List[Dict[str, Any]]:
    try:
        docs = db.similarity_search(query, results)
    except Exception as e:
        logging.error(f"Error during similarity search: {e}")
        raise e
    
    return [{"page_content": doc.page_content, "metadata": doc.metadata} for doc in docs]

def faiss_read(faiss_index_name: str, model_name: str, query: str, results: int = 5) -> None:
    db = load_faiss_index(faiss_index_name, model_name)
    docs = perform_similarity_search(db, query, results)
    
    if docs:
        print(json.dumps(docs))
    else:
        print("No documents found.")

def main() -> None:
    import argparse
    
    parser = argparse.ArgumentParser(description="FAISS index search tool")
    parser.add_argument('-i', '--index', type=str, required=True, help='Name of the FAISS index to search')
    parser.add_argument('-m', '--model', type=str, default="text-embedding-3-small", help='Name of the OpenAI embedding model to use')
    parser.add_argument('-k', '--results', type=int, default=5, help='Number of documents to return (default: 5)')
    parser.add_argument('query', type=str, help='Query string to search for')
    
    args = parser.parse_args()
    
    try:
        faiss_read(args.index, args.model, args.query, args.results)
    except Exception as e:
        logging.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
