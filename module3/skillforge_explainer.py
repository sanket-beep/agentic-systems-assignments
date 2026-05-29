from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser


REQUIRED_KEYS = {"topic", "audience", "tone", "limit"}


prompt = PromptTemplate(
    input_variables=["topic", "audience", "tone", "limit"],
    template=(
        "Explain {topic} to {audience} in a {tone} tone.\n"
        "Include one real-life analogy.\n"
        "Stay within {limit} words."
    ),
)


llm = ChatOpenAI(model="gpt-4o-mini")
output_parser = StrOutputParser()

chain = prompt | llm | output_parser


def validate_brief(brief):
    missing_keys = REQUIRED_KEYS - set(brief.keys())

    if missing_keys:
        raise ValueError(f"Missing required key(s): {', '.join(sorted(missing_keys))}")

    if not isinstance(brief["limit"], str) or not brief["limit"].isdigit():
        raise ValueError("limit must be a digit string, for example '120'")


LESSON_BRIEFS = [
    {
        "topic": "SQL indexes",
        "audience": "beginners",
        "tone": "simple",
        "limit": "120",
    },
    {
        "topic": "FastAPI dependency injection",
        "audience": "intermediate developers",
        "tone": "technical",
        "limit": "180",
    },
    {
        "topic": "LangChain PromptTemplate",
        "audience": "product managers",
        "tone": "friendly",
        "limit": "100",
    },
]


if __name__ == "__main__":
    for brief in LESSON_BRIEFS:
        print(f"=== Lesson: {brief['topic']} ===")

        validate_brief(brief)

        result = chain.invoke(brief)

        print(result)
        print(f"Length: {len(result)} chars")
        print()