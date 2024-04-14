import json
from langchain_community.document_loaders import UnstructuredFileLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

def file_load(files=[], chunk_size=1000, chunk_overlap=10):
    loader = UnstructuredFileLoader(files)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        is_separator_regex=False
    )
    docs = loader.load_and_split(splitter)
    return docs

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Load files")
    parser.add_argument("files", type=str, nargs='?', help='Files to load')
    parser.add_argument('-s', '--chunk_size', type=int, default=1000, help='Size of each chunk')
    parser.add_argument('-o', '--chunk_overlap', type=int, default=10, help='Number of characters that overlap between chunks')
    args = parser.parse_args()

    files = json.loads(args.files)

    docs = file_load(files, args.chunk_size, args.chunk_overlap)

    docs_list = []
    for doc in docs:
        docs_list.append({
            "page_content": doc.page_content,
            "metadata": doc.metadata,
        })

    print(json.dumps(docs_list, indent=2))


if __name__ == "__main__":
    main()
