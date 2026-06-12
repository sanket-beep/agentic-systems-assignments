"""
ingest.py

Loads hostel policy markdown files, splits them, embeds them with OpenAI,
and stores them in a persistent Chroma database.
"""

import shutil
from pathlib import Path

from langchain_chroma import Chroma
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


DOCUMENTS_DIR = "documents"
CHROMA_DIR = "chroma_db"
COLLECTION_NAME = "hostel_policy_docs"


def ingest() -> None:
    chroma_path = Path(CHROMA_DIR)

    if chroma_path.exists():
        shutil.rmtree(chroma_path)

    loader = DirectoryLoader(
        DOCUMENTS_DIR,
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )

    documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=400,
        chunk_overlap=60,
        add_start_index=True,
    )

    chunks = splitter.split_documents(documents)

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=CHROMA_DIR,
    )

    print(f"Ingested {len(documents)} documents into {len(chunks)} chunks.")
    print(f"Chroma collection: {COLLECTION_NAME}")
    print(f"Persist directory: {CHROMA_DIR}")
    print(f"Stored vectors: {vector_store._collection.count()}")


if __name__ == "__main__":
    ingest()
