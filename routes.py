import time
import traceback
import requests
from fastapi import HTTPException, Request, FastAPI
from fastapi.responses import StreamingResponse
from config import DIFY_API_URL, BOT_TYPE, API_PATHS
from models import ChatResponse, Choice, Message, Usage, ChatRequest
from request_builder import build_request
from stream_processor import StreamProcessor
from utils import generate_id, validate_auth_token


async def root():
    return {"message": "Dify2OpenAI, Deployed!"}


async def get_models():
    return {
        "object": "list",
        "data": [
            {
                "id": "dify",
                "object": "model",
                "owned_by": "dify",
                "permission": None,
            }
        ],
    }


async def post_chat_completions(request: Request):
    try:
        token = validate_auth_token(request)
        data = await request.json()
        request_data = ChatRequest(**data)
        request_body = build_request(
            request_data.messages,
            request_data.user_id,
            request_data.conversation_id,
        )

        resp = requests.post(
            DIFY_API_URL + API_PATHS[BOT_TYPE.lower()],
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
    except Exception:
        print(f"traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error")


def setup_routes(app: FastAPI):
    app.get("/")(root)
    app.get("/v1/models")(get_models)
    app.post("/v1/chat/completions")(post_chat_completions)
