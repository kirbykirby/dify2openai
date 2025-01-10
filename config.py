import os
from dotenv import load_dotenv


load_dotenv()
DIFY_API_URL = os.getenv("DIFY_API_URL")
if not DIFY_API_URL:
    raise ValueError("You need a DIFY API URL, dude.")
BOT_TYPE = os.getenv("BOT_TYPE", "Chat")
OUTPUT_VARIABLE = os.getenv("OUTPUT_VARIABLE", "")
API_PATHS = {
    "chat": "/chat-messages",
    "completion": "/completion-messages",
    "workflow": "/workflows/run",
}
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization",
    "Access-Control-Max-Age": "86400",
}
