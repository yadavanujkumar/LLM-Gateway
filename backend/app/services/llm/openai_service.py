from typing import AsyncGenerator, Dict, Any, List
import time
import uuid

from openai import AsyncOpenAI
from openai import APIError, RateLimitError, APIConnectionError

from app.config import settings
from app.schemas.chat import ChatCompletionRequest, EmbeddingRequest

client = AsyncOpenAI(
    api_key=settings.OPENAI_API_KEY,
    organization=settings.OPENAI_ORG_ID or None,
)

OPENAI_MODELS = [
    "gpt-4",
    "gpt-4-turbo",
    "gpt-4-turbo-preview",
    "gpt-3.5-turbo",
    "gpt-3.5-turbo-16k",
    "text-embedding-ada-002",
    "text-embedding-3-small",
    "text-embedding-3-large",
]


async def chat_completion(request: ChatCompletionRequest) -> Dict[str, Any]:
    messages = [{"role": m.role.value, "content": m.content} for m in request.messages]
    kwargs = {
        "model": request.model,
        "messages": messages,
        "temperature": request.temperature,
        "top_p": request.top_p,
        "frequency_penalty": request.frequency_penalty,
        "presence_penalty": request.presence_penalty,
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

    async with client.chat.completions.stream(**kwargs) as stream:
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                yield f"data: {{'choices': [{{'delta': {{'content': {repr(content)}}}, 'index': 0}}]}}\n\n"
        yield "data: [DONE]\n\n"


async def create_embeddings(request: EmbeddingRequest) -> Dict[str, Any]:
    inputs = request.input if isinstance(request.input, list) else [request.input]
    response = await client.embeddings.create(model=request.model, input=inputs)
    return {
        "object": "list",
        "data": [
            {"object": "embedding", "embedding": e.embedding, "index": e.index}
            for e in response.data
        ],
        "model": response.model,
        "usage": {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": 0,
            "total_tokens": response.usage.total_tokens,
        },
    }
