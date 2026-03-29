from typing import AsyncGenerator, Dict, Any, List
import asyncio
import datetime

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import settings
from app.schemas.chat import ChatCompletionRequest, EmbeddingRequest
from app.services.llm import openai_service, llama_service, mistral_service
from app.services.llm import anthropic_service, groq_service, gemini_service
from app.services.llm.openai_service import OPENAI_MODELS
from app.services.llm.llama_service import LLAMA_MODELS
from app.services.llm.mistral_service import MISTRAL_MODELS
from app.services.llm.anthropic_service import ANTHROPIC_MODELS
from app.services.llm.groq_service import GROQ_MODELS
from app.services.llm.gemini_service import GEMINI_MODELS

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
} | {
    model: {"provider": "anthropic", "service": anthropic_service}
    for model in ANTHROPIC_MODELS
} | {
    model: {"provider": "groq", "service": groq_service}
    for model in GROQ_MODELS
} | {
    model: {"provider": "google", "service": gemini_service}
    for model in GEMINI_MODELS
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
    if request.model in GEMINI_MODELS:
        return await gemini_service.create_embeddings(request)
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

    anthropic_model_info = {
        "claude-3-haiku-20240307": {"description": "Claude 3 Haiku – fastest Claude 3 model",
                                    "context_window": 200000,
                                    "pricing": {"input": 0.00025, "output": 0.00125}},
        "claude-3-sonnet-20240229": {"description": "Claude 3 Sonnet – balanced performance",
                                     "context_window": 200000,
                                     "pricing": {"input": 0.003, "output": 0.015}},
        "claude-3-opus-20240229": {"description": "Claude 3 Opus – most capable Claude 3",
                                   "context_window": 200000,
                                   "pricing": {"input": 0.015, "output": 0.075}},
        "claude-3-5-sonnet-20240620": {"description": "Claude 3.5 Sonnet – improved Sonnet",
                                        "context_window": 200000,
                                        "pricing": {"input": 0.003, "output": 0.015}},
        "claude-3-5-haiku-20241022": {"description": "Claude 3.5 Haiku – fast and affordable",
                                       "context_window": 200000,
                                       "pricing": {"input": 0.001, "output": 0.005}},
        "claude-3-7-sonnet-20250219": {"description": "Claude 3.7 Sonnet – latest Sonnet generation",
                                       "context_window": 200000,
                                       "pricing": {"input": 0.003, "output": 0.015}},
    }

    for model_id in ANTHROPIC_MODELS:
        info = anthropic_model_info.get(model_id, {})
        models.append({
            "id": model_id,
            "object": "model",
            "created": base_time,
            "owned_by": "anthropic",
            "description": info.get("description", f"Anthropic model {model_id}"),
            "context_window": info.get("context_window"),
            "pricing": info.get("pricing"),
        })

    groq_model_info = {
        "llama3-8b-8192": {"description": "Llama 3 8B (via Groq)", "context_window": 8192,
                           "pricing": {"input": 0.00005, "output": 0.00008}},
        "llama3-70b-8192": {"description": "Llama 3 70B (via Groq)", "context_window": 8192,
                            "pricing": {"input": 0.00059, "output": 0.00079}},
        "llama-3.1-8b-instant": {"description": "Llama 3.1 8B Instant (via Groq)", "context_window": 131072,
                                  "pricing": {"input": 0.00005, "output": 0.00008}},
        "llama-3.1-70b-versatile": {"description": "Llama 3.1 70B Versatile (via Groq)", "context_window": 131072,
                                     "pricing": {"input": 0.00059, "output": 0.00079}},
        "llama-3.3-70b-versatile": {"description": "Llama 3.3 70B Versatile (via Groq)", "context_window": 131072,
                                     "pricing": {"input": 0.00059, "output": 0.00079}},
        "llama-3.2-90b-vision-preview": {"description": "Llama 3.2 90B Vision Preview (via Groq)", "context_window": 8192,
                                          "pricing": {"input": 0.0009, "output": 0.0009}},
        "qwen-2.5-32b": {"description": "Qwen 2.5 32B (via Groq)", "context_window": 32768,
                         "pricing": {"input": 0.00029, "output": 0.00039}},
        "mixtral-8x7b-32768": {"description": "Mixtral 8x7B (via Groq)", "context_window": 32768,
                                 "pricing": {"input": 0.00024, "output": 0.00024}},
        "deepseek-r1-distill-llama-70b": {"description": "DeepSeek R1 Distill Llama 70B (via Groq)", "context_window": 32768,
                                           "pricing": {"input": 0.00099, "output": 0.00099}},
        "gemma-7b-it": {"description": "Gemma 7B Instruct (via Groq)", "context_window": 8192,
                         "pricing": {"input": 0.00007, "output": 0.00007}},
        "gemma2-9b-it": {"description": "Gemma 2 9B Instruct (via Groq)", "context_window": 8192,
                         "pricing": {"input": 0.0002, "output": 0.0002}},
    }

    for model_id in GROQ_MODELS:
        info = groq_model_info.get(model_id, {})
        models.append({
            "id": model_id,
            "object": "model",
            "created": base_time,
            "owned_by": "groq",
            "description": info.get("description", f"Groq model {model_id}"),
            "context_window": info.get("context_window"),
            "pricing": info.get("pricing"),
        })

    gemini_model_info = {
        "gemini-1.5-pro": {"description": "Gemini 1.5 Pro", "context_window": 2097152,
                           "pricing": {"input": 0.0035, "output": 0.0105}},
        "gemini-1.5-flash": {"description": "Gemini 1.5 Flash – fast and efficient",
                             "context_window": 1048576,
                             "pricing": {"input": 0.000075, "output": 0.0003}},
        "gemini-1.0-pro": {"description": "Gemini 1.0 Pro", "context_window": 32760,
                           "pricing": {"input": 0.0005, "output": 0.0015}},
        "gemini-1.5-pro-latest": {"description": "Gemini 1.5 Pro (latest alias)",
                                  "context_window": 2097152,
                                  "pricing": {"input": 0.0035, "output": 0.0105}},
        "gemini-1.5-flash-latest": {"description": "Gemini 1.5 Flash (latest alias)",
                                     "context_window": 1048576,
                                     "pricing": {"input": 0.000075, "output": 0.0003}},
        "gemini-2.0-flash": {"description": "Gemini 2.0 Flash", "context_window": 1048576,
                             "pricing": {"input": 0.0001, "output": 0.0004}},
        "gemini-2.0-flash-lite": {"description": "Gemini 2.0 Flash Lite", "context_window": 1048576,
                                  "pricing": {"input": 0.000075, "output": 0.0003}},
        "gemini-2.5-pro": {"description": "Gemini 2.5 Pro", "context_window": 2097152,
                           "pricing": {"input": 0.0035, "output": 0.0105}},
        "gemini-2.5-flash": {"description": "Gemini 2.5 Flash", "context_window": 1048576,
                             "pricing": {"input": 0.00015, "output": 0.0006}},
    }

    for model_id in GEMINI_MODELS:
        info = gemini_model_info.get(model_id, {})
        models.append({
            "id": model_id,
            "object": "model",
            "created": base_time,
            "owned_by": "google",
            "description": info.get("description", f"Google Gemini model {model_id}"),
            "context_window": info.get("context_window"),
            "pricing": info.get("pricing"),
        })

    return models
