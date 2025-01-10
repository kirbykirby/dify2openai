from typing import List
from models import Message


def build_request(
    messages: List[Message],
    user_id: str = None,
    conversation_id=None,
) -> dict:
    return {
        "inputs": [{"role": msg.role, "content": msg.content} for msg in messages],
        "query": messages[-1].content,
        "response_mode": "streaming",
        "conversation_id": conversation_id,
        "user": user_id,
    }
