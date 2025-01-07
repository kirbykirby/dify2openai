# Dify2OpenAI

[**English**](README.md) | **简体中文**

## 简介
Dify2OpenAI允许你使用OpenAI兼容的客户端来访问Dify的API接口。

## 特性
- 将 Dify API 格式转换为 OpenAI 格式
- 配置和部署简单
- 支持对话补全接口
- 最小化配置要求

## 快速开始
1. 克隆仓库
```bash
git clone https://github.com/kirbykirby/dify2openai.git
cd dify2openai
```

2. 创建 .env 文件并填写 Dify API URL:
```bash
DIFY_API_URL=your_dify_api_url_here
```

3. 运行服务:
```bash
uv run main.py
```
服务将默认在 http://localhost:3000 上运行。

## 使用方法
启动服务后，你可以向 API 接口发送请求。以下是 Python 示例代码：
localhost:3000/v1/chat/completions
```python
import requests

# API 接口地址
url = "http://localhost:3000/v1/chat/completions"

# 对话示例
messages = [
    {"role": "user", "content": "Hi"}
]

# 请求数据
data = {
    "model": "dify",
    "messages": messages
}

# 你的Dify App密钥
bearer_token = "your_dify_app_key_here"

# 发送 POST 请求
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {bearer_token}"
}

response = requests.post(url, headers=headers, json=data)

# 打印响应
if response.status_code == 200:
    result = response.json()
    assistant_message = result['choices'][0]['message']['content']
    print("助手:", assistant_message)
else:
    print("错误:", response.status_code)
    print(response.text)
```
响应格式将匹配 OpenAI 的 API 响应结构：
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
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 10,
        "completion_tokens": 20,
        "total_tokens": 30
    }
}
```

## 系统要求
1. Python 3.8+
2. uv 包管理器
