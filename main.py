import time
import traceback
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
import os
import requests
import uvicorn
from config import DIFY_API_URL, BOT_TYPE, INPUT_VARIABLE, API_PATHS, CORS_HEADERS
from models import ChatResponse, Choice, Message, Usage, ChatRequest
from request_builder import build_completion_request, build_chat_request
from stream_processor import StreamProcessor
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
    try:
        token = validate_auth_token(request)
        data = await request.json()
        request_data = ChatRequest(**data)
        request_body = (
            build_chat_request(
                request_data.messages, INPUT_VARIABLE, request_data.user_id, request_data.conversation_id
            )
            if BOT_TYPE == "Chat"
            else build_completion_request(request_data.messages, INPUT_VARIABLE)
        )

        resp = requests.post(
            DIFY_API_URL + API_PATHS[BOT_TYPE],
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
            json=request_body,
        )

        if request_data.stream:
            return StreamingResponse(
                resp.iter_content(chunk_size=1024), media_type="text/event-stream"
            )

        processor = StreamProcessor()
        for chunk in resp.iter_content(chunk_size=1024):
            processor.process_chunk(chunk)
            if processor.has_error:
                raise HTTPException(
                    status_code=500,
                    detail="An error occurred while processing the request.",
                )
        if not processor.message_ended:
            raise HTTPException(status_code=500, detail="Unexpected end of stream.")
        return ChatResponse(
            id=f"chatcmpl-{generate_id()}",
            created=int(time.time()),
            model=request_data.model,
            choices=[
                Choice(
                    index=0,
                    message=Message(role="assistant", content=processor.result.strip()),
                )
            ],
            usage=Usage(**processor.usage_data),
            conversation_id=processor.conversation_id,
            dialogue_count=processor.dialogue_count,
        )
    except Exception as e:
        print(f"traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3000)
