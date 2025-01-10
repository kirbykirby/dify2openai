import time
from typing import List
from models import Message


def build_chat_request(
    messages: List[Message], input_variable: str = None, user_id: str = None
) -> dict:
    return {
        "messages": [{"role": msg.role, "content": msg.content} for msg in messages],
        "query": messages[-1].content,
        "response_mode": "streaming",
        # "conversation_id": user_id or "",
        "user": user_id or "apiuser",
        "context": {  # 添加上下文信息
            "conversation_history": [
                {"role": msg.role, "content": msg.content, "timestamp": time.time()}
                for msg in messages[:-1]  # 不包含最后一条消息，因为它已经在query中
            ]
        },
        "auto_generate_name": False,
        "inputs": {input_variable: messages[-1].content} if input_variable else {},
    }


def build_completion_request(
    messages: List[Message], input_variable: str = None
) -> dict:
    conversation_history = " ".join([msg.content for msg in messages])
    return {
        "inputs": {input_variable: messages[-1].content} if input_variable else {},
        "query": messages[-1].content,
        "context": conversation_history,
        "response_mode": "streaming",
        "conversation_id": "",
        "user": "apiuser",
        "auto_generate_name": False,
    }
