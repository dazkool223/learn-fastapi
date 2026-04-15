import logging
from typing import AsyncIterator
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)
from core.config import settings
from core.exceptions import (
    LLMConfigurationException,
    LLMProviderException,
    LLMRateLimitException,
    LLMTimeoutException,
    UnsupportedLLMProviderException,
)
from schemas.chat import ChatMessage

logger = logging.getLogger(__name__)

class LangChainLLMProvider:
    """
    Thin wrapper around a LangChain BaseChatModel.
    """

    def __init__(self, chat_model: BaseChatModel, provider: str):
        self._model = chat_model
        self._provider = provider

    @property
    def model_name(self) -> str:
        return str(getattr(self._model, "model_name", "unknown"))

    @property
    def provider_name(self) -> str:
        return self._provider

    def invoke(self, messages: list[ChatMessage]) -> AIMessage:
        lc_msgs = _to_langchain_messages(messages)
        try:
            return self._model.invoke(lc_msgs)
        except Exception as exc:
            _raise_normalised(exc)

    async def ainvoke(self, messages: list[ChatMessage]) -> AIMessage:
        lc_msgs = _to_langchain_messages(messages)
        try:
            return await self._model.ainvoke(lc_msgs)
        except Exception as exc:
            _raise_normalised(exc)

    async def astream(self, messages: list[ChatMessage]) -> AsyncIterator[str]:
        lc_msgs = _to_langchain_messages(messages)
        try:
            async for chunk in self._model.astream(lc_msgs):
                if chunk.content:
                    yield chunk.content
        except Exception as exc:
            _raise_normalised(exc)

def build_llm_provider(
    provider: str | None = None,
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    api_key: str | None = None,
) -> LangChainLLMProvider:
    """
    Factory that returns a configured LangChainLLMProvider.

    Falls back to ``settings.*`` for every parameter that is not supplied.
    """
    provider = (provider or settings.LLM_PROVIDER).lower().strip()
    model = model or settings.LLM_MODEL
    temperature = temperature if temperature is not None else settings.LLM_TEMPERATURE
    max_tokens = max_tokens if max_tokens is not None else settings.LLM_MAX_TOKENS
    api_key = api_key or settings.LLM_API_KEY

    if not api_key:
        raise LLMConfigurationException(
            f"No API key configured for provider '{provider}'. "
            "Set LLM_API_KEY in .env or pass it in the request."
        )

    common_kwargs = dict(
        temperature=temperature,
        max_tokens=max_tokens,
        max_retries=settings.LLM_MAX_RETRIES,
        request_timeout=settings.LLM_REQUEST_TIMEOUT,
    )

    chat_model: BaseChatModel

    if provider in ("openai", "openrouter"):
        from langchain_openai import ChatOpenAI
        base_url = settings.LLM_BASE_URL if provider == "openrouter" else None
        chat_model = ChatOpenAI(
            model=model, api_key=api_key, base_url=base_url, **common_kwargs
        )
    else:
        raise UnsupportedLLMProviderException(
            f"Provider '{provider}' is not supported. Choose from: openrouter, openai"
        )

    return LangChainLLMProvider(chat_model, provider)

def _to_langchain_messages(messages: list[ChatMessage]) -> list[BaseMessage]:
    """Convert our schema messages to LangChain message objects."""
    mapping = {
        "system": SystemMessage,
        "user": HumanMessage,
        "assistant": AIMessage,
    }
    return [mapping[m.role](content=m.content) for m in messages]

def _raise_normalised(exc: Exception) -> None:
    """Map provider SDK errors to our exception hierarchy."""
    msg = str(exc).lower()
    logger.error("LLM provider error: %s", exc)

    if "rate" in msg or "429" in msg or "quota" in msg:
        raise LLMRateLimitException(str(exc))
    if "timeout" in msg or "timed out" in msg:
        raise LLMTimeoutException(str(exc))
    raise LLMProviderException(str(exc))