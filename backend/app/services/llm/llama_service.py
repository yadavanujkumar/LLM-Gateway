from typing import AsyncGenerator, Dict, Any, List
import json

from openai import AsyncOpenAI

from app.config import settings
from app.schemas.chat import ChatCompletionRequest

client = AsyncOpenAI(
    api_key=settings.TOGETHER_API_KEY,
    base_url=settings.TOGETHER_BASE_URL,
)

LLAMA_MODELS = [
    "llama-3-8b",
    "llama-3-70b",
    "llama-3.1-8b-instruct",
    "llama-3.1-70b-instruct",
    "llama-3.2-3b-instruct",
    "llama-3.2-11b-vision-instruct",
    "codellama-34b-instruct",
]

# Map our model IDs to Together AI model IDs
MODEL_MAP = {
    "llama-3-8b": "meta-llama/Llama-3-8b-chat-hf",
    "llama-3-70b": "meta-llama/Llama-3-70b-chat-hf",
    "llama-3.1-8b-instruct": "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
    "llama-3.1-70b-instruct": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
    "llama-3.2-3b-instruct": "meta-llama/Llama-3.2-3B-Instruct-Turbo",
    "llama-3.2-11b-vision-instruct": "meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo",
    "codellama-34b-instruct": "togethercomputer/CodeLlama-34b-Instruct",
}


def resolve_model(model: str) -> str:
    return MODEL_MAP.get(model, model)


async def chat_completion(request: ChatCompletionRequest) -> Dict[str, Any]:
    messages = [{"role": m.role.value, "content": m.content} for m in request.messages]
    resolved_model = resolve_model(request.model)
    kwargs = {
        "model": resolved_model,
        "messages": messages,
        "temperature": request.temperature,
        "top_p": request.top_p,
    }
    if request.max_tokens:
        kwargs["max_tokens"] = request.max_tokens

    response = await client.chat.completions.create(**kwargs)
    return {
        "id": response.id,
        "object": "chat.completion",
        "created": response.created,
        "model": request.model,  # return our model ID
        "choices": [
            {
                "index": c.index,
                "message": {"role": c.message.role, "content": c.message.content},
                "finish_reason": c.finish_reason,
            }
            for c in response.choices
        ],
        "usage": {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        },
    }


async def chat_completion_stream(
    request: ChatCompletionRequest,
) -> AsyncGenerator[str, None]:
    messages = [{"role": m.role.value, "content": m.content} for m in request.messages]
    resolved_model = resolve_model(request.model)
    kwargs = {
        "model": resolved_model,
        "messages": messages,
        "temperature": request.temperature,
        "stream": True,
    }
    if request.max_tokens:
        kwargs["max_tokens"] = request.max_tokens

    stream = await client.chat.completions.create(**kwargs)
    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            yield f"data: {{'choices': [{{'delta': {{'content': {repr(content)}}}, 'index': 0}}]}}\n\n"
    yield "data: [DONE]\n\n"
