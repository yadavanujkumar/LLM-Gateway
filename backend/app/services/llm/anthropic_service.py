from typing import AsyncGenerator, Dict, Any
import time
import uuid

import anthropic

from app.config import settings
from app.schemas.chat import ChatCompletionRequest

client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

ANTHROPIC_MODELS = [
    "claude-3-haiku-20240307",
    "claude-3-sonnet-20240229",
    "claude-3-opus-20240229",
    "claude-3-5-sonnet-20240620",
    "claude-3-5-haiku-20241022",
    "claude-3-7-sonnet-20250219",
]

# Default max_tokens when the caller doesn't specify one (Anthropic requires it)
_DEFAULT_MAX_TOKENS = 1024


def _extract_system_and_messages(request: ChatCompletionRequest):
    """Split messages into an optional system prompt and a user/assistant turn list."""
    system_prompt = None
    turns = []
    for m in request.messages:
        if m.role.value == "system":
            system_prompt = m.content
        else:
            turns.append({"role": m.role.value, "content": m.content})
    return system_prompt, turns


async def chat_completion(request: ChatCompletionRequest) -> Dict[str, Any]:
    system_prompt, turns = _extract_system_and_messages(request)
    kwargs: Dict[str, Any] = {
        "model": request.model,
        "max_tokens": request.max_tokens or _DEFAULT_MAX_TOKENS,
        "messages": turns,
        "temperature": request.temperature,
        "top_p": request.top_p,
    }
    if system_prompt:
        kwargs["system"] = system_prompt

    response = await client.messages.create(**kwargs)
    content_text = response.content[0].text if response.content else ""
    return {
        "id": response.id,
        "object": "chat.completion",
        "created": int(time.time()),
        "model": response.model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content_text},
                "finish_reason": response.stop_reason,
            }
        ],
        "usage": {
            "prompt_tokens": response.usage.input_tokens,
            "completion_tokens": response.usage.output_tokens,
            "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
        },
    }


async def chat_completion_stream(
    request: ChatCompletionRequest,
) -> AsyncGenerator[str, None]:
    system_prompt, turns = _extract_system_and_messages(request)
    kwargs: Dict[str, Any] = {
        "model": request.model,
        "max_tokens": request.max_tokens or _DEFAULT_MAX_TOKENS,
        "messages": turns,
        "temperature": request.temperature,
    }
    if system_prompt:
        kwargs["system"] = system_prompt

    async with client.messages.stream(**kwargs) as stream:
        async for text in stream.text_stream:
            yield f"data: {{'choices': [{{'delta': {{'content': {repr(text)}}}, 'index': 0}}]}}\n\n"
    yield "data: [DONE]\n\n"
