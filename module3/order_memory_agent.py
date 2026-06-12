"""
order_memory_agent.py

A small e-commerce support desk bot that uses:
- LangChain tool-calling agent runtime
- One order-status tool
- Module-level conversational memory via chat_history

Demo:
Turn 1: User shares an order ID.
Turn 2: User asks a vague follow-up.
The agent should use chat_history to resolve the order ID.
"""

import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool

try:
    from langchain.agents import AgentExecutor, create_tool_calling_agent
except ImportError:
    # Some newer LangChain installations expose the classic agent runtime here.
    from langchain_classic.agents import AgentExecutor, create_tool_calling_agent


load_dotenv()


orders_db = {
    "ORD101": {
        "order_id": "ORD101",
        "status": "out for delivery",
        "item": "Laptop Stand",
    },
    "ORD102": {
        "order_id": "ORD102",
        "status": "cancelled",
        "item": "Wireless Keyboard",
    },
}


@tool
def get_order_status(order_id: str) -> str:
    """Fetch the current status of an order using the order ID."""
    normalized_order_id = order_id.strip().upper()
    order = orders_db.get(normalized_order_id)

    if not order:
        return f"Sorry, I could not find any order with ID {normalized_order_id}."

    return (
        f"Order {order['order_id']} for {order['item']} is currently "
        f"{order['status']}."
    )


tools = [get_order_status]


model = init_chat_model(
    os.getenv("CHAT_MODEL", "openai:gpt-4o-mini"),
    temperature=0,
)


prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful e-commerce support assistant. "
            "Remember order IDs mentioned earlier in the conversation and use them for follow-up questions. "
            "Use the order status tool whenever the user asks about an order status. "
            "Keep answers short and friendly.",
        ),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
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
    verbose=True,
)


chat_history = []


def ask_agent(user_input: str) -> str:
    result = agent_executor.invoke(
        {
            "input": user_input,
            "chat_history": chat_history,
        }
    )

    ai_text = result["output"]

    chat_history.append(HumanMessage(content=user_input))
    chat_history.append(AIMessage(content=ai_text))

    return ai_text


if __name__ == "__main__":
    turn_1_user = "Hi, my order ID is ORD102."
    turn_2_user = "What is the status of it?"

    print("Turn 1 user:")
    print(turn_1_user)
    print("Turn 1 assistant:")
    print(ask_agent(turn_1_user))

    print("=" * 60)

    print("Turn 2 user:")
    print(turn_2_user)
    print("Turn 2 assistant:")
    print(ask_agent(turn_2_user))

    print("=" * 60)

    print("len(chat_history):")
    print(len(chat_history))
