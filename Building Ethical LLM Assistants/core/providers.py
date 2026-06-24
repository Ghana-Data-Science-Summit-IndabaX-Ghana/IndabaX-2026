from abc import ABC, abstractmethod
from core.config import ANTHROPIC_API_KEY, GOOGLE_API_KEY, OPENROUTER_API_KEY
import os


class LLMProvider(ABC):
    model: str = ""

    @abstractmethod
    def complete(self, system: str, messages: list[dict]) -> str:
        """Send messages to the model and return the reply text."""


class AnthropicProvider(LLMProvider):
    model = "claude-haiku-4-5"

    def __init__(self):
        import anthropic
        self._client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    def complete(self, system: str, messages: list[dict]) -> str:
        response = self._client.messages.create(
            model=self.model,
            max_tokens=1000,
            system=system,
            messages=messages,
        )
        return response.content[0].text


class GemmaProvider(LLMProvider):
    """
    Google Gemma adapter via the google-genai SDK.

    Model id: The Gemini API lists Gemma 4 as free-tier on the pricing page but
    it did not appear in the models API at build time (2026-06-15). We use the
    most recent confirmed Gemma model available via the Gemini API
    (gemma-3-27b-it) and make it configurable via GEMMA_MODEL_ID.

    Update GEMMA_MODEL_ID in your .env to switch to a newer Gemma model
    when one becomes available (e.g. "gemma-4-27b-it" or similar).

    Teaching note: Gemma has no native system role — the adapter prepends
    the system prompt to the first user turn as "System: ...\n\nUser: ...".
    This is why the same system prompt may be adhered to differently across
    providers — a real representation/faithfulness teaching point for Module 2.
    """
    model: str  # set in __init__ from env or default

    DEFAULT_MODEL = "gemini-2.0-flash"  # gemma-3-27b-it removed from API; use Gemini Flash

    def __init__(self):
        self.model = os.getenv("GEMMA_MODEL_ID", self.DEFAULT_MODEL)
        self._client = None  # lazy-initialized on first complete() call

    def _get_client(self):
        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=GOOGLE_API_KEY)
        return self._client

    def complete(self, system: str, messages: list[dict]) -> str:
        # Prepend system prompt to the first user message — Gemma has no system role
        prepended_messages = list(messages)
        if prepended_messages and prepended_messages[0]["role"] == "user":
            first_content = prepended_messages[0]["content"]
            prepended_messages[0] = {
                "role": "user",
                "content": f"System: {system}\n\nUser: {first_content}",
            }
        elif system:
            prepended_messages.insert(0, {
                "role": "user",
                "content": f"System: {system}",
            })

        # Convert to google-genai format
        contents = [
            {"role": msg["role"], "parts": [{"text": msg["content"]}]}
            for msg in prepended_messages
        ]

        response = self._get_client().models.generate_content(
            model=self.model,
            contents=contents,
        )
        return response.text


class OpenRouterProvider(LLMProvider):
    """
    OpenRouter adapter — OpenAI-compatible proxy giving access to 200+ models
    (Claude, Gemini, Llama, Mistral, etc.) through a single API key.

    Set OPENROUTER_MODEL in your .env to pick a model, or pass model= to
    get_provider(). Defaults to Llama 3.3 70B (free tier).

    Examples:
        "meta-llama/llama-3.3-70b-instruct:free"  — free, good reasoning
        "anthropic/claude-haiku-4-5"               — fast, cheap
        "anthropic/claude-sonnet-4-5"              — more capable
        "google/gemini-2.0-flash"                  — Google via OpenRouter

    Teaching note: OpenRouter normalises all models to the OpenAI chat format,
    so system prompts work the same way regardless of the underlying model.
    This is the key difference from calling Gemma directly (see GemmaProvider).
    """

    DEFAULT_MODEL = "meta-llama/llama-3.3-70b-instruct:free"
    BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, model: str | None = None):
        self.model = model or os.getenv("OPENROUTER_MODEL", self.DEFAULT_MODEL)
        if not OPENROUTER_API_KEY:
            raise ValueError(
                "OPENROUTER_API_KEY is not set. "
                "Get a free key at https://openrouter.ai and add it to your .env file."
            )

    def complete(self, system: str, messages: list[dict]) -> str:
        import httpx
        import time

        full_messages = [{"role": "system", "content": system}] + list(messages)
        payload = {"model": self.model, "messages": full_messages, "max_tokens": 1000}
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }

        for attempt in range(3):
            response = httpx.post(self.BASE_URL, json=payload, headers=headers, timeout=60.0)
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 2 ** attempt))
                time.sleep(retry_after)
                continue
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]

        raise RuntimeError(
            f"OpenRouter rate limit exceeded for model '{self.model}'. "
            "Consider switching to a paid model or reducing request frequency."
        )


def get_provider(name: str, model: str | None = None) -> LLMProvider:
    name = (name or "anthropic").lower()
    if name == "anthropic":
        return AnthropicProvider()
    if name == "gemma":
        return GemmaProvider()
    if name == "openrouter":
        return OpenRouterProvider(model=model)
    raise ValueError(f"Unknown provider: {name!r}. Choose 'anthropic', 'gemma', or 'openrouter'.")
