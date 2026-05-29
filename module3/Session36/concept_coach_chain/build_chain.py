"""
build_chain.py

Reusable LCEL chain for Concept Coach.
"""

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama


def build_chain():
    """
    Builds and returns a reusable LangChain Expression Language chain.

    Chain flow:
    Prompt -> Ollama chat model -> String output parser
    """

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are Concept Coach, a beginner-friendly programming instructor. "
                "Explain programming concepts in simple language, avoid jargon, "
                "and keep answers clear and demo-ready.",
            ),
            (
                "human",
                "Explain {topic} using an analogy from {analogy_domain}. "
                "Keep the explanation within 100 words.",
            ),
        ]
    )

    llm = ChatOllama(
        model="qwen:1.8b",
        base_url="http://localhost:11434",
        temperature=1,
        num_predict=100,
    )

    parser = StrOutputParser()

    return prompt | llm | parser
