# Dify2OpenAI

**English** | [**简体中文**](README_ZH.MD)

## Introduction
Dify2OpenAI allows you to use Dify's API endpoints with OpenAI-compatible clients by providing a compatible interface.

## Features
- Converts Dify API format to OpenAI format
- Simple configuration and deployment
- Supports chat completions endpoint
- Minimal setup required

## Quick Start
1. Clone this repository
```bash
git clone https://github.com/kirbykirby/dify2openai.git
cd dify2openai
```

2. Create `.env` file with your Dify API URL:
```bash
DIFY_API_URL=your_dify_api_url_here
```

3. Run the service:
```bash
uv run main.py
```
The service will start running on http://localhost:3000 by default.

## Usage
After starting the service, you can send requests to the API endpoint. Here's a Python example:

```python
import requests

# API endpoint
url = "http://localhost:3000/v1/chat/completions"

# Example conversation
messages = [
    {"role": "user", "content": "Hi"}
]

# Request payload
data = {
    "model": "dify",
    "messages": messages
}

# Your Dify App key
bearer_token = "your_dify_app_key_here"

# Send POST request
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {bearer_token}"
}

response = requests.post(url, headers=headers, json=data)

# Print response
if response.status_code == 200:
    result = response.json()
    assistant_message = result['choices'][0]['message']['content']
    print("Assistant:", assistant_message)
else:
    print("Error:", response.status_code)
    print(response.text)
```

The response format will match OpenAI's API response structure:
```json
{
    "id": "chatcmpl-123",
    "object": "chat.completion",
    "created": 1700000000,
    "model": "dify",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "Hello! How can I help you today?"
            },
            "logprobs": null,
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 10,
        "completion_tokens": 20,
        "total_tokens": 30
    },
    "system_fingerprint": "fp_2f57f81c11"
}
```

## Requirements
1. Python 3.8+
2. uv package manager
