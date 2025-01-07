import time
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
import os
import requests
import json
import uvicorn
from starlette.requests import Request
from config import DIFY_API_URL, BOT_TYPE, INPUT_VARIABLE, OUTPUT_VARIABLE, API_PATHS, CORS_HEADERS
from utils import generate_id, validate_auth_token

app = FastAPI()


@app.middleware("http")
async def set_cors_headers(request: Request, call_next):
    response = await call_next(request)
    for key, value in CORS_HEADERS.items():
        response.headers[key] = value
    return response


@app.get("/")
async def root():
    return {"message": "Dify2OpenAI, Deployed!"}


@app.get("/v1/models")
async def get_models():
    return {
        "object": "list",
        "data": [
            {
                "id": os.getenv("MODELS_NAME", "dify"),
                "object": "model",
                "owned_by": "dify",
                "permission": None,
            }
        ],
    }


@app.post("/v1/chat/completions")
async def post_chat_completions(request: Request):
    auth_header = request.headers.get("authorization") or request.headers.get(
        "Authorization"
    )
    token = validate_auth_token(auth_header)

    try:
        data = await request.json()
        messages = data.get("messages", [])
        stream = data.get("stream", False)

        if BOT_TYPE == "Chat":
            request_body = {
                "messages": messages,  # 保留完整对话历史
                "query": messages[-1]["content"],
                "response_mode": "streaming",
                "conversation_id": "",
                "user": "apiuser",
                "auto_generate_name": False,
                "inputs": {},
            }
            if INPUT_VARIABLE:
                # 只在需要时使用最后一条消息
                request_body["inputs"] = {INPUT_VARIABLE: messages[-1]["content"]}
        elif BOT_TYPE in ("Completion", "Workflow"):
            # 保留历史消息用于上下文
            conversation_history = " ".join([msg["content"] for msg in messages])
            request_body = {
                "inputs": {INPUT_VARIABLE: messages[-1]["content"]}
                if INPUT_VARIABLE
                else {},
                "query": messages[-1]["content"],
                "context": conversation_history,  # 添加历史上下文
                "response_mode": "streaming",
                "conversation_id": "",
                "user": "apiuser",
                "auto_generate_name": False,
            }

        resp = requests.post(
            DIFY_API_URL + API_PATHS[BOT_TYPE],
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
            json=request_body,
        )

        if stream:
            return StreamingResponse(
                resp.iter_content(chunk_size=1024), media_type="text/event-stream"
            )
        else:
            result = ""
            usage_data = ""
            has_error = False
            message_ended = False
            buffer = ""
            skip_workflow_finished = False

            for chunk in resp.iter_content(chunk_size=1024):
                buffer += chunk.decode()
                lines = buffer.split("\n")

                for line in lines[:-1]:
                    cleaned_line = line.replace("data: ", "").strip()
                    if not cleaned_line:
                        continue

                    try:
                        chunk_obj = json.loads(cleaned_line)
                    except json.JSONDecodeError:
                        continue

                    if (
                        chunk_obj["event"] == "message"
                        or chunk_obj["event"] == "agent_message"
                    ):
                        result += chunk_obj["answer"]
                        skip_workflow_finished = True
                    elif chunk_obj["event"] == "message_end":
                        message_ended = True
                        usage_data = {
                            "prompt_tokens": chunk_obj["metadata"]["usage"][
                                "prompt_tokens"
                            ]
                            or 100,
                            "completion_tokens": chunk_obj["metadata"]["usage"][
                                "completion_tokens"
                            ]
                            or 10,
                            "total_tokens": chunk_obj["metadata"]["usage"][
                                "total_tokens"
                            ]
                            or 110,
                        }
                    elif (
                        chunk_obj["event"] == "workflow_finished"
                        and not skip_workflow_finished
                    ):
                        message_ended = True
                        outputs = chunk_obj["data"]["outputs"]
                        if OUTPUT_VARIABLE:
                            result = outputs[OUTPUT_VARIABLE]
                        else:
                            result = outputs
                        result = str(result)
                        usage_data = {
                            "prompt_tokens": chunk_obj["metadata"]["usage"][
                                "prompt_tokens"
                            ]
                            or 100,
                            "completion_tokens": chunk_obj["metadata"]["usage"][
                                "completion_tokens"
                            ]
                            or 10,
                            "total_tokens": chunk_obj["data"]["total_tokens"] or 110,
                        }
                    elif chunk_obj["event"] == "error":
                        print(f"Error: {chunk_obj['code']}, {chunk_obj['message']}")
                        has_error = True
                        break

                buffer = lines[-1]

            if has_error:
                raise HTTPException(
                    status_code=500,
                    detail="An error occurred while processing the request.",
                )
            elif message_ended:
                return {
                    "id": f"chatcmpl-{generate_id()}",
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": data["model"],
                    "choices": [
                        {
                            "index": 0,
                            "message": {"role": "assistant", "content": result.strip()},
                            "logprobs": None,
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": usage_data,
                    "system_fingerprint": "fp_2f57f81c11",
                }
            else:
                raise HTTPException(status_code=500, detail="Unexpected end of stream.")
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3000)
