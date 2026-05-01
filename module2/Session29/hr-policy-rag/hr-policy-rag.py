from chromadb.config import Settings
from typing import List, Dict, Any
from openai import OpenAI
import chromadb
import os


POLICY_DOCUMENTS = [
    {
        "id": "leave_policy_v1",
        "text": (
            "Employees receive 18 days of paid annual leave in each calendar year, credited on a pro-rated basis for new joiners. "
            "Unused annual leave can be carried forward up to 5 days into the next year, and any balance above that limit expires unless a written exception is approved by HR. "
            "Employees must submit planned leave requests through the HR portal at least 3 working days in advance whenever possible. "
            "The company also provides up to 8 days of paid sick leave per year, and sick leave of 2 or more consecutive days may require a medical certificate."
        ),
        "metadata": {"category": "Leave Policy", "source": "HR Handbook 2026"},
    },
    {
        "id": "wfh_policy_v1",
        "text": (
            "Eligible full-time employees may work from home up to 2 days per week after successful completion of their probation period. "
            "Work-from-home arrangements are subject to role suitability, performance standing, and business needs determined by the reporting manager. "
            "Employees must request work-from-home days in advance and obtain manager approval before finalizing their weekly schedule. "
            "Team members are expected to remain reachable during core working hours and attend critical meetings on-site when specifically asked to do so."
        ),
        "metadata": {"category": "Work From Home Policy", "source": "Flexible Work Guidelines 2026"},
    },
    {
        "id": "appraisal_policy_v1",
        "text": (
            "The company conducts its formal appraisal cycle once every year between January and March. "
            "Managers evaluate employees on a 5-point rating scale that measures goal achievement, collaboration, skill growth, and role effectiveness. "
            "Salary increments and performance bonuses are linked to the final rating as well as company budget and business performance for the year. "
            "Employees receive a review discussion with their manager before compensation outcomes are finalized and communicated by HR."
        ),
        "metadata": {"category": "Appraisal Policy", "source": "Performance Management Policy 2026"},
    },
    {
        "id": "conduct_policy_v1",
        "text": (
            "All employees are expected to maintain respectful, professional behavior and must not engage in harassment, discrimination, or intimidation in any work setting. "
            "Confidential company information and employee data must be accessed only for legitimate business purposes and handled according to approved privacy controls. "
            "Employees must disclose any personal, financial, or family interest that could influence business decisions or create a conflict of interest. "
            "Violations of the code of conduct may lead to disciplinary action, including formal warnings, suspension, or termination depending on severity."
        ),
        "metadata": {"category": "Code of Conduct", "source": "Employee Code of Conduct 2026"},
    },
]


EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"
PERSIST_DIRECTORY = "./chroma_store"
COLLECTION_NAME = "hr_policy_collection"

client = OpenAI()

def create_embeddings(texts: List[str]) -> List[List[float]]:
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [item.embedding for item in response.data]


def setup_vector_database():
    client = chromadb.PersistentClient(path=PERSIST_DIRECTORY)
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine", "description": "HR policy RAG collection"},
    )
    return collection


def index_hr_documents(collection) -> None:
    documents = [doc["text"] for doc in POLICY_DOCUMENTS]
    embeddings = create_embeddings(documents)
    ids = [doc["id"] for doc in POLICY_DOCUMENTS]
    metadatas = [doc["metadata"] for doc in POLICY_DOCUMENTS]

    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings,
    )


def retrieve_hr_content(collection, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    query_embedding = create_embeddings([query])[0]
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    for idx in range(len(results["ids"][0])):
        chunks.append(
            {
                "id": results["ids"][0][idx],
                "text": results["documents"][0][idx],
                "metadata": results["metadatas"][0][idx],
                "distance": results["distances"][0][idx],
            }
        )
    return chunks


def build_grounded_prompt(query: str, chunks: List[Dict[str, Any]]) -> str:
    context_blocks = []
    for i, chunk in enumerate(chunks, start=1):
        context_blocks.append(
            f"Context {i}:\n"
            f"Category: {chunk['metadata'].get('category')}\n"
            f"Source: {chunk['metadata'].get('source')}\n"
            f"Policy Text: {chunk['text']}"
        )

    context = "\n\n".join(context_blocks) if context_blocks else "No policy context retrieved."

    return f"""
You are an HR Policy Assistant for InnoTech Solutions.
Answer the employee's question using only the policy context below.
If the answer is not stated or cannot be supported by the context, say: "I could not find that information in the provided HR policy documents."
Do not guess, invent policies, or rely on outside knowledge.
Be concise, clear, and policy-grounded.

Employee Question:
{query}

Policy Context:
{context}
""".strip()


def generate_answer(query: str, chunks: List[Dict[str, Any]]) -> str:
    prompt = build_grounded_prompt(query, chunks)
    response = client.chat.completions.create(
        model=CHAT_MODEL,
        temperature=0.2,
        messages=[
            {"role": "system", "content": "You provide grounded HR policy answers."},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content.strip()


def generate_answer_without_retrieval(query: str) -> str:
    response = client.chat.completions.create(
        model=CHAT_MODEL,
        temperature=0.6,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a general AI assistant answering an HR question without access to company policies. "
                    "Respond based on general knowledge and clearly state assumptions when needed."
                ),
            },
            {"role": "user", "content": query},
        ],
    )
    return response.choices[0].message.content.strip()


def answer_with_rag(collection, query: str, top_k: int = 3) -> str:
    chunks = retrieve_hr_content(collection, query, top_k=top_k)
    print("\n" + "=" * 100)
    print(f"EMPLOYEE QUERY: {query}")
    print("-" * 100)
    print("RETRIEVED POLICY CHUNKS:")
    for i, chunk in enumerate(chunks, start=1):
        print(f"\nChunk {i}")
        print(f"ID       : {chunk['id']}")
        print(f"Category : {chunk['metadata'].get('category')}")
        print(f"Source   : {chunk['metadata'].get('source')}")
        print(f"Distance : {chunk['distance']:.4f}")
        print(f"Text     : {chunk['text']}")

    answer = generate_answer(query, chunks)
    print("\nFINAL RAG ANSWER:")
    print(answer)
    return answer


def main() -> None:
    collection = setup_vector_database()
    index_hr_documents(collection)

    sample_queries = [
        "How many days of annual leave am I entitled to per year, and can I carry any forward?",
        "Do I need manager approval before working from home, and how many WFH days are allowed each week?",
        "When is the appraisal cycle conducted and how is the increment decided?",
    ]

    for query in sample_queries:
        answer_with_rag(collection, query, top_k=3)

    comparison_query = "Do I need manager approval before working from home?"
    print("\n" + "=" * 100)
    print("SIDE-BY-SIDE COMPARISON")
    print("=" * 100)
    print(f"Query: {comparison_query}\n")

    print("ANSWER WITHOUT RAG:")
    print(generate_answer_without_retrieval(comparison_query))

    print("\nANSWER WITH RAG:")
    rag_chunks = retrieve_hr_content(collection, comparison_query, top_k=3)
    print(generate_answer(comparison_query, rag_chunks))


if __name__ == "__main__":
    main()