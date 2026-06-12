import json
import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.messages import ToolMessage
from langchain.tools import tool
from pydantic import BaseModel, Field

load_dotenv()

ORDERS_DB = {
    "CC2001": {
        "order_id": "CC2001",
        "item": "Hoodie — Batch 2026",
        "status": "shipped",
        "eta_days": 3,
    },
}


class OrderStatusInput(BaseModel):
    order_id: str = Field(description="Campus Crate order ID to look up, for example CC2001.")


@tool(args_schema=OrderStatusInput)
def get_order_status(order_id: str) -> str:
    """Use this when the user asks about order status or delivery."""
    normalized_order_id = order_id.strip().upper()
    order = ORDERS_DB.get(normalized_order_id)

    if order:
        return json.dumps({"ok": True, "order": order})

    return json.dumps({"ok": False, "message": "Order not found"})


model = init_chat_model(
    os.getenv("CHAT_MODEL", "openai:gpt-4o-mini"),
    temperature=0,
)

model_with_tools = model.bind_tools([get_order_status])


def _message_text(message) -> str:
    """Convert a LangChain message content field into plain text."""
    content = message.content

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, dict) and "text" in item:
                text_parts.append(item["text"])
            else:
                text_parts.append(str(item))
        return "\n".join(text_parts)

    return str(content)


def run_order_help(user_query: str) -> str:
    messages = [
        ("system", "use the order tool when the user asks about an order"),
        ("human", user_query),
    ]

    first_reply = model_with_tools.invoke(messages)
    messages.append(first_reply)

    if not first_reply.tool_calls:
        return _message_text(first_reply)

    for tool_call in first_reply.tool_calls:
        tool_result = get_order_status.invoke(tool_call["args"])

        messages.append(
            ToolMessage(
                content=tool_result,
                tool_call_id=tool_call["id"],
            )
        )

    final_reply = model_with_tools.invoke(messages)
    return _message_text(final_reply)


if __name__ == "__main__":
    queries = [
        "Where is my order CC2001?",
        "What is Python?",
    ]

    for index, query in enumerate(queries):
        if index > 0:
            print("=" * 60)

        print(run_order_help(query))
