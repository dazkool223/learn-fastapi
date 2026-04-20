"""
Service for handling LLM function calling with tools.
Integrates tool execution with conversation flow.
"""
import json
import logging
from typing import Any, Optional
from sqlmodel import Session
from langchain_core.messages import AIMessage, ToolMessage
from langchain_openai import ChatOpenAI

from schemas.chat import ChatMessage
from services.tools.tool_definitions import LIBRARY_TOOLS, validate_tool_definitions
from services.tools.tool_executor import ToolExecutor
from services.storage import StorageService
from core.config import settings

logger = logging.getLogger(__name__)


class ToolCallingService:
    """Handles LLM interactions with function calling enabled."""

    def __init__(
        self,
        session: Session,
        storage: StorageService,
        enabled_tools: Optional[list[str]] = None,
    ):
        self.session = session
        self.storage = storage
        self.tool_executor = ToolExecutor(session, storage)
        self.enabled_tools = enabled_tools or []

        # Validate that tool definitions match executor registry
        validate_tool_definitions(self.tool_executor.get_available_tools())

        # Validate enabled_tools exist in executor
        if self.enabled_tools:
            available = set(self.tool_executor.get_available_tools())
            invalid = set(self.enabled_tools) - available
            if invalid:
                raise ValueError(f"Invalid tools requested: {invalid}. Available: {available}")

    def get_available_tools(self) -> list[dict]:
        """Filter tools based on enabled_tools list."""
        if not self.enabled_tools:
            return []

        return [
            tool
            for tool in LIBRARY_TOOLS
            if tool["function"]["name"] in self.enabled_tools
        ]

    async def complete_with_tools(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> tuple[str, Optional[list[dict]]]:
        """
        Complete a chat request with tool calling enabled.

        Returns:
            tuple: (response_content, tool_calls_metadata)
        """
        available_tools = self.get_available_tools()

        if not available_tools:
            logger.warning("Tool calling requested but no tools are enabled")
            return await self._complete_without_tools(messages, model, temperature, max_tokens)

        # Build LangChain ChatOpenAI with tools
        llm = self._build_llm(model, temperature, max_tokens)
        llm_with_tools = llm.bind_tools(available_tools)

        # Convert to LangChain messages
        lc_messages = self._to_langchain_messages(messages)

        # Initial LLM call
        ai_message: AIMessage = await llm_with_tools.ainvoke(lc_messages)

        # Check if LLM wants to call tools
        if not ai_message.tool_calls:
            # No tools called, return response directly
            return str(ai_message.content), None

        # Execute tool calls
        tool_call_metadata = []
        lc_messages.append(ai_message)

        for tool_call in ai_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_call_id = tool_call["id"]

            logger.info(f"Executing tool: {tool_name} with args: {tool_args}")

            # Execute the tool
            result_json = self.tool_executor.execute(tool_name, tool_args)

            # Store metadata for response
            tool_call_metadata.append({
                "tool": tool_name,
                "arguments": tool_args,
                "result": json.loads(result_json),
            })

            # Add tool result to conversation
            tool_message = ToolMessage(
                content=result_json,
                tool_call_id=tool_call_id,
            )
            lc_messages.append(tool_message)

        # Second LLM call with tool results
        final_response: AIMessage = await llm_with_tools.ainvoke(lc_messages)

        return str(final_response.content), tool_call_metadata

    async def _complete_without_tools(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> tuple[str, None]:
        """Fallback to regular completion without tools."""
        llm = self._build_llm(model, temperature, max_tokens)
        lc_messages = self._to_langchain_messages(messages)
        ai_message = await llm.ainvoke(lc_messages)
        return str(ai_message.content), None

    def _build_llm(
        self,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> ChatOpenAI:
        """Build ChatOpenAI instance with configuration."""
        from pydantic import SecretStr

        model_name = model or settings.LLM_MODEL
        temp = temperature if temperature is not None else settings.LLM_TEMPERATURE
        max_tok = max_tokens if max_tokens is not None else settings.LLM_MAX_TOKENS

        # Determine base URL for OpenRouter
        base_url = None
        if settings.LLM_PROVIDER.lower() == "openrouter":
            base_url = settings.LLM_BASE_URL

        return ChatOpenAI(
            model=model_name,
            api_key=SecretStr(settings.LLM_API_KEY),
            base_url=base_url,
            temperature=temp,
            max_completion_tokens=max_tok,
            max_retries=settings.LLM_MAX_RETRIES,
            timeout=settings.LLM_REQUEST_TIMEOUT,
        )

    def _to_langchain_messages(self, messages: list[ChatMessage]):
        """Convert ChatMessage to LangChain messages."""
        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

        mapping = {
            "system": SystemMessage,
            "user": HumanMessage,
            "assistant": AIMessage,
        }
        return [mapping[m.role](content=m.content) for m in messages]
