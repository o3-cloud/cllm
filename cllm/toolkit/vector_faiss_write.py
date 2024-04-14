import json
import sys
import os
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

AI_CLI_DIR = os.getenv("CLLM_DIR", f"{os.getcwd()}/.cllm")


def faiss_save(data, index_name):
    # Data to be added to FAISS
    data = json.loads(data)

    index_path = f"{AI_CLI_DIR}/rag/{index_name}"

    # Create documents from data
    documents = [
        Document(page_content=item.get("page_content"), metadata=item.get("metadata")) for item in data
    ]

    # Create embeddings
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    # Check if FAISS index exists

    if os.path.exists(index_path):
        db = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
        db.add_documents(documents)
    else:
        # Create FAISS index from documents
        db = FAISS.from_documents(documents, embeddings)
    
    print(f"Number of documents in the index: {db.index.ntotal}")

    # Save FAISS index locally
    db.save_local(index_path)
    print("FAISS index saved locally.")

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Save data to FAISS index")
    parser.add_argument('-i', '--index', type=str, default="faiss_index", help='Path to save the FAISS index')
    parser.add_argument("data", nargs='?', default=None)
    args = parser.parse_args()
    # Get data from stdin
    input_data = sys.stdin.read()

    faiss_save(input_data, args.index)

if __name__ == "__main__":
    main()