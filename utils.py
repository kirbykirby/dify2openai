import random
import string

from fastapi import HTTPException


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
