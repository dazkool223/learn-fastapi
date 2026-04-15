"""
Chat service — orchestrates conversations between users and the LLM.
"""
import logging
import uuid
from typing import AsyncIterator

from schemas.chat import ChatMessage, ChatRequest, ChatResponse, TokenUsage
from services.langchain_llm_provider import LangChainLLMProvider, build_llm_provider

logger = logging.getLogger(__name__)


class ChatService:
    """Thin orchestrator that delegates to an LLMProvider."""

    def __init__(self, provider: LangChainLLMProvider):
        self._provider = provider

    def complete(self, request: ChatRequest) -> ChatResponse:
        ai_message = self._provider.invoke(request.messages)

        usage = _extract_usage(ai_message)
        return ChatResponse(
            id=_make_id(),
            model=self._provider.model_name,
            provider=self._provider.provider_name,
            message=ChatMessage(role="assistant", content=str(ai_message.content)),
            usage=usage,
        )

    async def acomplete(self, request: ChatRequest) -> ChatResponse:
        ai_message = await self._provider.ainvoke(request.messages)

        usage = _extract_usage(ai_message)
        return ChatResponse(
            id=_make_id(),
            model=self._provider.model_name,
            provider=self._provider.provider_name,
            message=ChatMessage(role="assistant", content=str(ai_message.content)),
            usage=usage,
        )

    async def astream(self, request: ChatRequest) -> AsyncIterator[str]:
        """
        Yields text chunks as they arrive from the LLM.
        Each chunk is formatted as a Server-Sent Event.
        """
        async for token in self._provider.astream(request.messages):
            yield f"data: {token}\n\n"
        yield "data: [DONE]\n\n"

def _make_id() -> str:
    return f"chat-{uuid.uuid4().hex[:12]}"


def _extract_usage(ai_message) -> TokenUsage | None:
    """Try to pull token counts from the LangChain response metadata."""
    meta = getattr(ai_message, "response_metadata", {}) or {}
    usage_data = meta.get("token_usage") or meta.get("usage") or {}
    if not usage_data:
        return None
    return TokenUsage(
        prompt_tokens=usage_data.get("prompt_tokens") or usage_data.get("input_tokens"),
        completion_tokens=usage_data.get("completion_tokens") or usage_data.get("output_tokens"),
        total_tokens=usage_data.get("total_tokens"),
    )

def build_chat_service(
    provider: str | None = None,
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> ChatService:
    llm = build_llm_provider(
        provider=provider,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return ChatService(llm)
