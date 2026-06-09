"""Thin OpenAI client wrapper. Keeps SDK details out of the agent logic."""

import json
import logging

from openai import OpenAI

logger = logging.getLogger(__name__)


class LLM:
    """Wraps the OpenAI chat client for tool-use loops and structured output."""

    def __init__(self, api_key: str, model: str) -> None:
        self._client = OpenAI(api_key=api_key)
        self._model = model

    def step(self, messages: list[dict], tools: list[dict]):
        """One model turn with tools available. Returns the assistant message."""
        response = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )
        return response.choices[0].message

    def structured(self, messages: list[dict], schema: dict) -> dict:
        """Final turn constrained to a JSON schema. Returns the parsed object."""
        response = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            response_format={"type": "json_schema", "json_schema": schema},
        )
        content = response.choices[0].message.content or "{}"
        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            logger.error("Model returned non-JSON structured output: %s", exc)
            raise
