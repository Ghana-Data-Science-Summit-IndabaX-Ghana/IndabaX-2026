"""
agent/groq.py
─────────────────────────────────────────────────────────────────────────────
Thin wrapper around the Groq API.

Groq exposes an OpenAI-compatible API so the same client works
for many models (Claude, Gemini, Llama, Mistral, etc.).

You do NOT need to edit this file for the required exercises.
It is provided as working infrastructure.

Relevant docs: https://console.groq.com/docs/api-reference#chat-create
─────────────────────────────────────────────────────────────────────────────
"""

import os
import httpx
import json
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


DEFAULT_MODEL = os.getenv("DEFAULT_MODEL")
MODEL_BASE_URL = os.getenv("MODEL_BASE_URL")


@dataclass
class ToolCall:
    """Represents a single tool call requested by the model."""
    id: str
    function_name: str
    function_arguments: str  # raw JSON string

    class _FunctionAccessor:
        def __init__(self, name, arguments):
            self.name = name
            self.arguments = arguments

    @property
    def function(self):
        return self._FunctionAccessor(self.function_name, self.function_arguments)

    def to_dict(self) -> dict:
        """Convert the custom ToolCall object into the standard API dictionary format."""
        return {
            "id": self.id,
            "type": "function",
            "function": {
                "name": self.function_name,
                "arguments": self.function_arguments
            }
        }


@dataclass
class ChatResponse:
    """Normalised response from the LLM."""
    content: str | None           # text response, if no tool calls
    tool_calls: list[ToolCall] | None = field(default=None)
    model: str = ""
    usage: dict = field(default_factory=dict)


def chat(
    messages: list[dict],
    tools: list[dict] | None = None,
    system_prompt: str | None = None,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.2,
    max_tokens: int = 1024,
) -> ChatResponse:
    """
    Send a list of messages to Groq and return a normalised response.

    Parameters
    ----------
    messages      : Conversation history in OpenAI format.
    tools         : List of tool schemas (function-calling format).
    system_prompt : If provided, prepended as the first system message.
                    Use this OR include system in messages — not both.
    model         : Any Groq model string.
    temperature   : Lower = more deterministic (0.2 recommended for triage).
    max_tokens    : Maximum tokens in the response.

    Returns
    -------
    ChatResponse with .content (str) or .tool_calls (list[ToolCall]).
    Exactly one of these will be non-None per response.

    Raises
    ------
    ValueError    : If GROQ_API_KEY is not set.
    httpx.HTTPStatusError : On API errors (4xx / 5xx).
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY environment variable is not set.\n"
            "Get a free key at https://console.groq.com/home and add it to your .env file."
        )

    # Build the message list
    full_messages = []
    if system_prompt:
        full_messages.append({"role": "system", "content": system_prompt})
    full_messages.extend(messages)

    payload: dict = {
        "model": model,
        "messages": full_messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-Title": "AMA Health Agent Workshop",
    }

    print(f"Sending request to {MODEL_BASE_URL}/chat/completions with payload:", payload)

    response = httpx.post(
        f"{MODEL_BASE_URL}/chat/completions",
        json=payload,
        headers=headers,
        timeout=60.0,
    )
    response.raise_for_status()
    data = response.json()

    choice = data["choices"][0]
    message = choice["message"]

    # Parse tool calls if present
    tool_calls = None
    if message.get("tool_calls"):
        tool_calls = [
            ToolCall(
                id=tc["id"],
                function_name=tc["function"]["name"],
                function_arguments=tc["function"]["arguments"],
            )
            for tc in message["tool_calls"]
        ]

    return ChatResponse(
        content=message.get("content"),
        tool_calls=tool_calls,
        model=data.get("model", model),
        usage=data.get("usage", {}),
    )
