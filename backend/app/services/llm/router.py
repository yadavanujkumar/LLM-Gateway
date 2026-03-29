from typing import AsyncGenerator, Dict, Any, List
import asyncio
import datetime

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import settings
from app.schemas.chat import ChatCompletionRequest, EmbeddingRequest
from app.services.llm import openai_service, llama_service, mistral_service
from app.services.llm.openai_service import OPENAI_MODELS
from app.services.llm.llama_service import LLAMA_MODELS
from app.services.llm.mistral_service import MISTRAL_MODELS

# Epoch timestamp for Jan 1, 2024 (used as a static "created" timestamp for model listings)
_MODEL_CATALOG_TIMESTAMP = int(datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc).timestamp())


AVAILABLE_MODELS = {
    model: {"provider": "openai", "service": openai_service}
    for model in OPENAI_MODELS
} | {
    model: {"provider": "together", "service": llama_service}
    for model in LLAMA_MODELS
} | {
    model: {"provider": "mistral", "service": mistral_service}
    for model in MISTRAL_MODELS
}


def get_provider(model: str) -> str:
    info = AVAILABLE_MODELS.get(model)
    if not info:
        return "openai"  # default
    return info["provider"]


def get_service(model: str):
    info = AVAILABLE_MODELS.get(model)
    if not info:
        return openai_service
    return info["service"]


def get_fallback_models(model: str) -> List[str]:
    """Get fallback models from the fallback order, excluding the current model."""
    return [m for m in settings.FALLBACK_ORDER if m != model]


async def route_chat_completion(
    request: ChatCompletionRequest,
) -> Dict[str, Any]:
    """Route chat completion with automatic fallback."""
    last_error = None
    models_to_try = [request.model] + get_fallback_models(request.model)

    for model in models_to_try:
        try:
            req = request.model_copy(update={"model": model})
            service = get_service(model)
            result = await service.chat_completion(req)
            # Tag with the actual model used if fallback occurred
            if model != request.model:
                result["fallback_from"] = request.model
            return result
        except Exception as e:
            last_error = e
            continue

    raise last_error or RuntimeError("All models failed")


async def route_chat_stream(
    request: ChatCompletionRequest,
) -> AsyncGenerator[str, None]:
    """Route streaming chat completion with fallback."""
    service = get_service(request.model)
    async for chunk in service.chat_completion_stream(request):
        yield chunk


async def route_embeddings(request: EmbeddingRequest) -> Dict[str, Any]:
    """Route embeddings request."""
    if request.model in MISTRAL_MODELS:
        return await mistral_service.create_embeddings(request)
    # Default to OpenAI for embeddings
    return await openai_service.create_embeddings(request)


def get_all_models() -> List[Dict[str, Any]]:
    """Return list of all available models with metadata."""
    base_time = _MODEL_CATALOG_TIMESTAMP

    models = []

    openai_model_info = {
        "gpt-4": {"description": "Most capable GPT-4 model", "context_window": 8192,
                  "pricing": {"input": 0.03, "output": 0.06}},
        "gpt-4-turbo": {"description": "GPT-4 Turbo with vision", "context_window": 128000,
                        "pricing": {"input": 0.01, "output": 0.03}},
        "gpt-3.5-turbo": {"description": "Fast and efficient GPT-3.5", "context_window": 16385,
                          "pricing": {"input": 0.0005, "output": 0.0015}},
        "text-embedding-ada-002": {"description": "OpenAI embedding model", "context_window": 8191,
                                   "pricing": {"input": 0.0001, "output": 0.0}},
        "text-embedding-3-small": {"description": "Smaller embedding model", "context_window": 8191,
                                   "pricing": {"input": 0.00002, "output": 0.0}},
        "text-embedding-3-large": {"description": "Larger embedding model", "context_window": 8191,
                                   "pricing": {"input": 0.00013, "output": 0.0}},
    }

    for model_id in OPENAI_MODELS:
        info = openai_model_info.get(model_id, {})
        models.append({
            "id": model_id,
            "object": "model",
            "created": base_time,
            "owned_by": "openai",
            "description": info.get("description", ""),
            "context_window": info.get("context_window"),
            "pricing": info.get("pricing"),
        })

    llama_info = {
        "llama-3-8b": {"description": "Llama 3 8B (via Together AI)", "context_window": 8192,
                       "pricing": {"input": 0.0002, "output": 0.0002}},
        "llama-3-70b": {"description": "Llama 3 70B (via Together AI)", "context_window": 8192,
                        "pricing": {"input": 0.0009, "output": 0.0009}},
        "llama-3.1-8b-instruct": {"description": "Llama 3.1 8B Instruct", "context_window": 131072,
                                   "pricing": {"input": 0.0002, "output": 0.0002}},
        "llama-3.1-70b-instruct": {"description": "Llama 3.1 70B Instruct", "context_window": 131072,
                                    "pricing": {"input": 0.0009, "output": 0.0009}},
    }

    for model_id in LLAMA_MODELS:
        info = llama_info.get(model_id, {})
        models.append({
            "id": model_id,
            "object": "model",
            "created": base_time,
            "owned_by": "meta",
            "description": info.get("description", f"Llama model {model_id}"),
            "context_window": info.get("context_window"),
            "pricing": info.get("pricing"),
        })

    mistral_info = {
        "mistral-small": {"description": "Mistral Small", "context_window": 32000,
                          "pricing": {"input": 0.002, "output": 0.006}},
        "mistral-medium": {"description": "Mistral Medium", "context_window": 32000,
                           "pricing": {"input": 0.0027, "output": 0.0081}},
        "mistral-large": {"description": "Mistral Large", "context_window": 32000,
                          "pricing": {"input": 0.008, "output": 0.024}},
    }

    for model_id in MISTRAL_MODELS:
        info = mistral_info.get(model_id, {})
        models.append({
            "id": model_id,
            "object": "model",
            "created": base_time,
            "owned_by": "mistral-ai",
            "description": info.get("description", f"Mistral model {model_id}"),
            "context_window": info.get("context_window"),
            "pricing": info.get("pricing"),
        })

    return models
