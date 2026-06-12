"""
mini_store_support_agent.py

A small LangChain tool-calling support assistant for order operations.

It demonstrates:
1. Three @tool functions
2. create_tool_calling_agent
3. AgentExecutor with intermediate steps
4. Four test queries:
   - Single-tool query
   - Multi-tool query
   - No-tool query
   - Invalid order ID query
"""

import os
from typing import Any

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import tool

try:
    from langchain.agents import AgentExecutor, create_tool_calling_agent
except ImportError:
    # Newer LangChain versions may expose the classic agent runtime here.
    from langchain_classic.agents import AgentExecutor, create_tool_calling_agent


load_dotenv()


orders_db = {
    "ORD1001": {
        "order_id": "ORD1001",
        "item": "Wireless Mouse",
        "status": "shipped",
        "eta_days": 3,
        "amount": 1299,
    },
    "ORD1002": {
        "order_id": "ORD1002",
        "item": "Bluetooth Speaker",
        "status": "cancelled",
        "eta_days": None,
        "amount": 2499,
    },
    "ORD1003": {
        "order_id": "ORD1003",
        "item": "USB-C Keyboard",
        "status": "delivered",
        "eta_days": 0,
        "amount": 3499,
    },
}


def normalize_order_id(order_id: str) -> str:
    return order_id.strip().upper()


def find_order(order_id: str) -> dict[str, Any] | None:
    return orders_db.get(normalize_order_id(order_id))


@tool
def get_order_status(order_id: str) -> str:
    """Fetch the current status of a customer order using its order ID."""
    order = find_order(order_id)

    if not order:
        return f"Order {normalize_order_id(order_id)} was not found."

    return (
        f"Order {order['order_id']} for {order['item']} is currently "
        f"{order['status']}."
    )


@tool
def estimate_delivery_timeline(order_id: str) -> str:
    """Estimate the delivery timeline for a customer order using its order ID."""
    order = find_order(order_id)

    if not order:
        return f"Order {normalize_order_id(order_id)} was not found."

    status = order["status"]

    if status == "shipped":
        return (
            f"Order {order['order_id']} is shipped and is expected to arrive "
            f"in {order['eta_days']} days."
        )

    if status == "delivered":
        return f"Order {order['order_id']} has already been delivered."

    if status == "cancelled":
        return f"Order {order['order_id']} was cancelled, so there is no delivery timeline."

    return f"Order {order['order_id']} has status '{status}', so delivery cannot be estimated."


@tool
def calculate_refund_amount(order_id: str) -> str:
    """Provide refund-related response for an order based on its current status."""
    order = find_order(order_id)

    if not order:
        return f"Order {normalize_order_id(order_id)} was not found."

    status = order["status"]
    amount = order["amount"]

    if status == "cancelled":
        return (
            f"Order {order['order_id']} is cancelled. The estimated refund amount "
            f"is ₹{amount}."
        )

    if status == "delivered":
        return (
            f"Order {order['order_id']} is delivered. A refund may be available "
            f"after return approval. Maximum refundable amount: ₹{amount}."
        )

    if status == "shipped":
        return (
            f"Order {order['order_id']} has already shipped. Refund is not available "
            f"right now unless the order is returned or cancelled successfully."
        )

    return f"Refund information is unavailable for order {order['order_id']}."


tools = [
    get_order_status,
    estimate_delivery_timeline,
    calculate_refund_amount,
]


model = init_chat_model(
    os.getenv("CHAT_MODEL", "openai:gpt-4o-mini"),
    temperature=0,
)


prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a friendly online store support assistant. "
            "Use the available tools for order status, delivery timeline, and refund questions. "
            "If the user asks a general non-order question, answer directly without tools. "
            "Keep final answers short and friendly.",
        ),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)


agent = create_tool_calling_agent(
    llm=model,
    tools=tools,
    prompt=prompt,
)


agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    max_iterations=3,
    handle_parsing_errors=True,
    return_intermediate_steps=True,
    verbose=False,
)


def print_intermediate_steps(intermediate_steps: list[tuple[Any, Any]]) -> None:
    if not intermediate_steps:
        print("Intermediate steps: None")
        return

    print("Intermediate steps:")

    for index, (action, observation) in enumerate(intermediate_steps, start=1):
        print(f"  Step {index}")
        print(f"    Tool selected: {action.tool}")
        print(f"    Tool input: {action.tool_input}")
        print(f"    Tool observation: {observation}")


def run_query(query: str) -> None:
    print(f"User query: {query}")

    result = agent_executor.invoke({"input": query})

    print("\nFinal output:")
    print(result["output"])

    print()
    print_intermediate_steps(result.get("intermediate_steps", []))


if __name__ == "__main__":
    test_queries = [
        # Single-tool query
        "What is the status of order ORD1001?",

        # Multi-tool query
        "For order ORD1001, tell me the status and when it will arrive.",

        # No-tool query
        "What is Python?",

        # Invalid order ID query
        "Can I get a refund for order ORD9999?",
    ]

    for query_index, query in enumerate(test_queries, start=1):
        if query_index > 1:
            print("=" * 80)

        run_query(query)
