import os
import re
import uuid
from pathlib import Path
from typing import Dict, List
from typing import cast
from chromadb.api.types import EmbeddingFunction, Embeddable
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
import chromadb
from chromadb.config import Settings
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from openai import OpenAI
from pypdf import PdfReader

PROJECT_DIR = Path(__file__).resolve().parent
POLICY_DIR = PROJECT_DIR / "policy_documents"
CHROMA_DIR = PROJECT_DIR / "chroma_db"
COLLECTION_NAME = "campus_policies"
EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"
DEFAULT_CHUNK_WORDS = 140
DEFAULT_OVERLAP_WORDS = 20


def infer_policy_type(filename: str) -> str:
    name = filename.lower()
    if "hostel" in name:
        return "hostel"
    if "refund" in name:
        return "refund"
    if "library" in name:
        return "library"
    if "withdraw" in name:
        return "course_withdrawal"
    return "general"


def clean_text(text: str) -> str:
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def load_all_pdfs(folder_path: Path) -> List[Dict]:
    documents = []
    pdf_files = sorted(folder_path.glob("*.pdf"))
    if not pdf_files:
        raise FileNotFoundError(f"No PDF files found in: {folder_path}")

    for pdf_path in pdf_files:
        reader = PdfReader(str(pdf_path))
        print(f"Loaded {len(reader.pages)} pages from: {pdf_path.name}")
        for page_number, page in enumerate(reader.pages, start=1):
            raw_text = page.extract_text() or ""
            cleaned = clean_text(raw_text)
            if cleaned:
                documents.append(
                    {
                        "text": cleaned,
                        "source_file": pdf_path.name,
                        "page_number": page_number,
                        "policy_type": infer_policy_type(pdf_path.name),
                    }
                )
    return documents


def split_into_chunks(text: str, chunk_size: int = DEFAULT_CHUNK_WORDS, overlap: int = DEFAULT_OVERLAP_WORDS) -> List[str]:
    words = text.split()
    if not words:
        return []
    if overlap >= chunk_size:
        raise ValueError("Overlap must be smaller than chunk size.")

    chunks = []
    step = chunk_size - overlap
    for start in range(0, len(words), step):
        end = start + chunk_size
        chunk_words = words[start:end]
        if not chunk_words:
            continue
        chunks.append(" ".join(chunk_words))
        if end >= len(words):
            break
    return chunks


def get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("OPENAI_API_KEY is not set. Export it before running the script.")
    return OpenAI(api_key=api_key)


def get_collection():
    if not os.getenv("OPENAI_API_KEY"):
        raise EnvironmentError("OPENAI_API_KEY is not set. Export it before running the script.")

    raw_embedding_function = OpenAIEmbeddingFunction(
        api_key_env_var="OPENAI_API_KEY",
        model_name=EMBEDDING_MODEL,
    )

    embedding_function = cast(
        EmbeddingFunction[Embeddable],
        raw_embedding_function,
    )

    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR),
        settings=Settings(anonymized_telemetry=False),
    )

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "Campus policy RAG store"},
        embedding_function=embedding_function,
    )
    print(f"Vector DB ready. Collection: {COLLECTION_NAME}")
    return collection

def build_knowledge_base():
    collection = get_collection()
    existing_ids = collection.get(include=[]).get("ids", [])
    if existing_ids:
        collection.delete(ids=existing_ids)

    documents = load_all_pdfs(POLICY_DIR)

    all_chunk_texts = []
    all_metadatas = []
    all_ids = []

    for doc in documents:
        chunks = split_into_chunks(doc["text"])
        for index, chunk in enumerate(chunks, start=1):
            all_chunk_texts.append(chunk)
            all_metadatas.append(
                {
                    "source_file": doc["source_file"],
                    "page_number": doc["page_number"],
                    "policy_type": doc["policy_type"],
                    "chunk_index": index,
                }
            )
            all_ids.append(str(uuid.uuid4()))

    print(f"Total chunks created: {len(all_chunk_texts)}")
    collection.add(ids=all_ids, documents=all_chunk_texts, metadatas=all_metadatas)
    print(f"Successfully stored {len(all_chunk_texts)} chunks in vector database.")
    return collection


def retrieve_relevant_chunks(collection, question: str, top_k: int = 3) -> List[Dict]:
    results = collection.query(query_texts=[question], n_results=top_k)
    retrieved = []
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0] if results.get("distances") else [None] * len(docs)
    for doc, meta, distance in zip(docs, metas, distances):
        retrieved.append({"chunk": doc, "metadata": meta, "distance": distance})
    print(f"Retrieved {len(retrieved)} relevant chunks.")
    return retrieved


def build_prompt(question: str, retrieved_chunks: List[Dict]) -> str:
    context_blocks = []
    for item in retrieved_chunks:
        meta = item["metadata"]
        context_blocks.append(
            f"Source: {meta['source_file']} | Page: {meta['page_number']} | Policy: {meta['policy_type']}\n"
            f"Context: {item['chunk']}"
        )
    context_text = "\n\n".join(context_blocks)
    return f"""
You are a campus policy assistant.
Answer only from the retrieved policy context below.
If the answer is not present in the context, say: I don't have that information.
Keep the answer simple and student-friendly.
Do not use outside knowledge.

Student question: {question}

Retrieved policy context:
{context_text}
""".strip()


def generate_answer(question: str, retrieved_chunks: List[Dict]) -> str:
    client = get_openai_client()
    prompt = build_prompt(question, retrieved_chunks)
    response = client.responses.create(
        model=CHAT_MODEL,
        input=[
            {"role": "system", "content": "You answer only from retrieved campus policy context."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )
    return response.output_text.strip()


def answer_question(collection, question: str) -> str:
    retrieved_chunks = retrieve_relevant_chunks(collection, question, top_k=3)
    return generate_answer(question, retrieved_chunks)


if __name__ == "__main__":
    collection = build_knowledge_base()

    test_queries = [
        "Can I get a refund after dropping a course?",
        "What is the deadline for returning a library book?",
        "Are hostel visitors allowed on weekends?",
    ]

    for query in test_queries:
        print(f"\nUser Query: {query}")
        answer = answer_question(collection, query)
        print(f"Answer: {answer}")
