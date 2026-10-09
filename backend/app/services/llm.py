"""LLM Gateway for ForgePilot AI."""

import logging
from collections.abc import Sequence

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_groq import ChatGroq

from backend.app.core.config import Settings, get_settings

logger = logging.getLogger("forgepilot.llm")


class LLMConfigurationError(RuntimeError):
    """Raised when the LLM Gateway is not configured correctly."""


class LLMProviderError(RuntimeError):
    """Raised when the configured LLM provider fails."""


class LLMGateway:
    """Provide a unified interface to the configured chat model."""

    def __init__(
        self,
        settings: Settings | None = None,
        model: BaseChatModel | None = None,
    ) -> None:
        self.settings = settings or get_settings()

        if model is not None:
            self._model = model
            return

        if not self.settings.groq_api_key.strip():
            raise LLMConfigurationError(
                "GROQ_API_KEY is missing. Configure it in your environment."
            )

        self._model = ChatGroq(
            model=self.settings.groq_model,
            api_key=self.settings.groq_api_key,
            temperature=self.settings.groq_temperature,
            timeout=self.settings.groq_timeout_seconds,
            max_retries=self.settings.groq_max_retries,
        )

    def invoke(self, messages: Sequence[BaseMessage]) -> AIMessage:
        """Send messages to the provider and return its response."""

        try:
            response = self._model.invoke(list(messages))
        except Exception as exc:
            logger.warning(
                "Synchronous LLM request failed: %s",
                type(exc).__name__,
            )
            raise LLMProviderError("The LLM provider request failed.") from exc

        if not isinstance(response, AIMessage):
            raise LLMProviderError(
                "The LLM provider returned an unexpected response type."
            )

        return response

    async def ainvoke(
        self,
        messages: Sequence[BaseMessage],
    ) -> AIMessage:
        """Asynchronously send messages to the provider."""

        try:
            response = await self._model.ainvoke(list(messages))
        except Exception as exc:
            logger.warning(
                "Asynchronous LLM request failed: %s",
                type(exc).__name__,
            )
            raise LLMProviderError("The LLM provider request failed.") from exc

        if not isinstance(response, AIMessage):
            raise LLMProviderError(
                "The LLM provider returned an unexpected response type."
            )

        return response
