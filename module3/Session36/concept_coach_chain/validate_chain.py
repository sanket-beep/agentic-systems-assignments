"""
validate_chain.py

Runs Concept Coach across multiple inputs and validates generated responses.
"""

from build_chain import build_chain


def is_response_valid(response: str) -> tuple[bool, list[str]]:
    """
    Validates an LLM response before showing it in a demo.

    Checks:
    - Response must be a string.
    - Response must not be empty after trimming spaces.
    - Response must not be more than 100 words.
    """

    errors: list[str] = []

    if not isinstance(response, str):
        errors.append("Response must be a string.")
        return False, errors

    trimmed_response = response.strip()

    if not trimmed_response:
        errors.append("Response must not be empty.")

    word_count = len(trimmed_response.split())

    if word_count > 100:
        errors.append("Response must not be more than 100 words.")

    return len(errors) == 0, errors


def run_tests() -> None:
    chain = build_chain()

    test_cases = [
        {
            "topic": "LangChain Expression Language",
            "analogy_domain": "school assembly line",
        },
        {
            "topic": "Prompt Templates",
            "analogy_domain": "wedding invitation cards",
        },
        {
            "topic": "Output Parsers",
            "analogy_domain": "food delivery packaging",
        },
    ]

    for index, input_dict in enumerate(test_cases, start=1):
        print("=" * 60)
        print(f"Test Case {index}")
        print("=" * 60)

        print("Input dictionary:")
        print(input_dict)

        try:
            response = chain.invoke(input_dict)
        except Exception as exc:
            response = ""
            print("\nGenerated response:")
            print(response)
            print("\nValidation result:")
            print(False)
            print("\nValidation errors:")
            print([f"Chain execution failed: {exc}"])
            continue

        is_valid, errors = is_response_valid(response)

        print("\nGenerated response:")
        print(response)

        print("\nValidation result:")
        print(is_valid)

        if errors:
            print("\nValidation errors:")
            print(errors)
        else:
            print("\nValidation errors:")
            print("None")


if __name__ == "__main__":
    run_tests()
