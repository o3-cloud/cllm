import json
import os
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

AI_CLI_DIR = os.getenv("CLLM_DIR", f"{os.getcwd()}/.cllm")

def faiss_read(faiss_index_name, query, results=5):
    # Load the FAISS index
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    faiss_index = f"{AI_CLI_DIR}/rag/{faiss_index_name}"
    db = FAISS.load_local(faiss_index, embeddings, allow_dangerous_deserialization=True)

    # Perform the similarity search
    docs = db.similarity_search(query, results)

    # Print the top document content
    chucks = []
    if docs:
        for doc in docs:
           chucks.append({"page_content": doc.page_content, "metadata": doc.metadata})
        print(json.dumps(chucks))
    else:
        print("No documents found.")

def main():
    import argparse

    parser = argparse.ArgumentParser(description="FAISS index search")
    parser.add_argument('-i', '--index', type=str, required=True, help='Path to the FAISS index')
    parser.add_argument('-k', '--results', type=int, help='Number of docs to return', default=5)
    parser.add_argument("query", nargs='?', default=None)

    args = parser.parse_args()
    faiss_index = args.index
    query = args.query
    results = args.results

    faiss_read(faiss_index, query, results)

if __name__ == "__main__":
    main()