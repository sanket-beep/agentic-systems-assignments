# HR Policy RAG Assistant

This project implements a Retrieval-Augmented Generation (RAG) assistant for internal HR policy questions using Python, ChromaDB, and the OpenAI API.

The assistant is designed for a company like InnoTech Solutions, where employees often ask repetitive HR questions that are already covered in policy documents. Instead of answering from memory, the assistant retrieves relevant policy content from a vector database and generates a grounded answer based only on that context.

## Features

- 4 original HR policy documents stored as Python dictionaries
- Embedding generation using the OpenAI API
- ChromaDB `PersistentClient` for persistent local vector storage
- Document indexing using `upsert`
- Retrieval of top matching policy chunks with similarity distance
- Grounded prompt construction with fallback behavior when the answer is not present
- LLM-based answer generation using retrieved policy context
- Side-by-side comparison of:
  - answer without RAG
  - answer with RAG

## Project Structure

```text
hr-policy-rag/
├── hr_policy_rag.py
├── README.md
└── requirements.txt
```
