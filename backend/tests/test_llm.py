"""Unit tests for the LLM Gateway."""

from typing import Any

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from backend.app.core.config import Settings
from backend.app.services.llm import (
    LLMConfigurationError,
    LLMGateway,
    LLMProviderError,
)


class FakeChatModel:
    """Minimal fake model for offline gateway tests."""

    def __init__(
        self,
        response: AIMessage | None = None,
        error: Exception | None = None,
    ) -> None:
        self.response = response or AIMessage(content="Fake response")
        self.error = error
        self.received_messages: list[Any] | None = None

    def invoke(self, messages: list[Any]) -> AIMessage:
        self.received_messages = messages

        if self.error:
            raise self.error

        return self.response

    async def ainvoke(self, messages: list[Any]) -> AIMessage:
        self.received_messages = messages

        if self.error:
            raise self.error

        return self.response


def test_gateway_invoke_returns_ai_message() -> None:
    """Test synchronous invocation with an injected fake model."""

    fake_model = FakeChatModel(response=AIMessage(content="Root cause identified."))
    gateway = LLMGateway(
        settings=Settings(groq_api_key=""),
        model=fake_model,  # type: ignore[arg-type]
    )

    response = gateway.invoke([HumanMessage(content="Analyze this bug.")])

    assert response.content == "Root cause identified."
    assert fake_model.received_messages is not None
    assert len(fake_model.received_messages) == 1


@pytest.mark.asyncio
async def test_gateway_ainvoke_returns_ai_message() -> None:
    """Test asynchronous invocation with an injected fake model."""

    fake_model = FakeChatModel(response=AIMessage(content="Patch proposal ready."))
    gateway = LLMGateway(
        settings=Settings(groq_api_key=""),
        model=fake_model,  # type: ignore[arg-type]
    )

    response = await gateway.ainvoke([HumanMessage(content="Propose a fix.")])

    assert response.content == "Patch proposal ready."


def test_gateway_requires_api_key_without_injected_model() -> None:
    """Test that real provider initialization requires an API key."""

    with pytest.raises(LLMConfigurationError, match="GROQ_API_KEY"):
        LLMGateway(settings=Settings(groq_api_key=""))


def test_gateway_wraps_provider_failure() -> None:
    """Test that provider failures use a consistent exception."""

    fake_model = FakeChatModel(error=RuntimeError("provider unavailable"))
    gateway = LLMGateway(
        settings=Settings(groq_api_key=""),
        model=fake_model,  # type: ignore[arg-type]
    )

    with pytest.raises(LLMProviderError, match="provider request failed"):
        gateway.invoke([HumanMessage(content="Test failure handling.")])
