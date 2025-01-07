import random
import string

from fastapi import HTTPException
from starlette.requests import Request

from config import CORS_HEADERS
from main import app


def generate_id(length=29):
    characters = string.ascii_letters + string.digits
    return "".join(random.choice(characters) for _ in range(length))


def validate_auth_token(auth_header: str | None) -> str:
    """验证认证token"""
    if not auth_header:
        raise HTTPException(status_code=401, detail="Unauthorized.")

    token = auth_header.split(" ")[1]
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized.")

    return token


@app.middleware("http")
async def set_cors_headers(request: Request, call_next):
    response = await call_next(request)
    for key, value in CORS_HEADERS.items():
        response.headers[key] = value
    return response
