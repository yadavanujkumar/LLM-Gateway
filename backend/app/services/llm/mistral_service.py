from typing import AsyncGenerator, Dict, Any
import json

from openai import AsyncOpenAI

from app.config import settings
from app.schemas.chat import ChatCompletionRequest, EmbeddingRequest

client = AsyncOpenAI(
    api_key=settings.MISTRAL_API_KEY,
    base_url=settings.MISTRAL_BASE_URL,
)

MISTRAL_MODELS = [
    "mistral-small",
    "mistral-medium",
    "mistral-large",
    "mistral-embed",
    "open-mistral-7b",
    "open-mixtral-8x7b",
    "open-mixtral-8x22b",
]


async def chat_completion(request: ChatCompletionRequest) -> Dict[str, Any]:
    messages = [{"role": m.role.value, "content": m.content} for m in request.messages]
    kwargs = {
        "model": request.model,
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
        "model": response.model,
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
    kwargs = {
        "model": request.model,
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


async def create_embeddings(request: EmbeddingRequest) -> Dict[str, Any]:
    inputs = request.input if isinstance(request.input, list) else [request.input]
    response = await client.embeddings.create(model="mistral-embed", input=inputs)
    return {
        "object": "list",
        "data": [
            {"object": "embedding", "embedding": e.embedding, "index": e.index}
            for e in response.data
        ],
        "model": "mistral-embed",
        "usage": {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": 0,
            "total_tokens": response.usage.total_tokens,
        },
    }
