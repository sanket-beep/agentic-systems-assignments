"""
rag_app.py

Reloads the persisted Chroma collection and answers hostel policy questions
using an LCEL RAG chain with guardrails.
"""

from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI, OpenAIEmbeddings


CHROMA_DIR = "chroma_db"
COLLECTION_NAME = "hostel_policy_docs"


def format_docs(docs) -> str:
    formatted_docs = []

    for doc in docs:
        source_path = doc.metadata.get("source", "unknown")
        source_name = Path(source_path).name

        formatted_docs.append(
            f"Source: {source_name}\n{doc.page_content}"
        )

    return "\n\n".join(formatted_docs)


def build_rag_chain():
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR,
    )

    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 2},
    )

    prompt = ChatPromptTemplate.from_template(
        """
You are a college hostel policy Q&A assistant.

Guardrails:
- Use only the retrieved context below.
- If the answer is missing from the retrieved context, say exactly:
  I don't know based on the provided documents.
- Mention the source file name when possible.
- Keep the answer concise.

Retrieved context:
{context}

Question:
{question}

Answer:
"""
    )

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
    )

    rag_chain = (
        {
            "context": retriever | format_docs,
            "question": RunnablePassthrough(),
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain


def main() -> None:
    rag_chain = build_rag_chain()

    queries = [
        ("Q1", "What are the quiet hours on weekdays?"),
        ("Q2", "What is the scholarship amount for hostel residents?"),
    ]

    for label, question in queries:
        print("=" * 80)
        print(f"{label}: {question}")
        print("-" * 80)
        answer = rag_chain.invoke(question)
        print(answer)


if __name__ == "__main__":
    main()
