from functools import lru_cache

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel

from app.config import settings


@lru_cache
def get_llm() -> BaseChatModel:
    """Provider-agnostic chat model (created lazily so imports never need an API key)."""
    return init_chat_model(
        settings.llm_model,
        model_provider=settings.llm_provider,
        temperature=settings.llm_temperature,
    )
