from __future__ import annotations

from langchain_openai import ChatOpenAI

from .config import Settings, load_settings


def build_llm(settings: Settings | None = None, *, temperature: float = 0.2, **kwargs) -> ChatOpenAI:
    """DeepSeek chat model via OpenAI-compatible endpoint.

    DeepSeek exposes an OpenAI-compatible /v1 surface, so langchain_openai
    routes there cleanly. Models: `deepseek-chat` (V3) for general work,
    `deepseek-reasoner` (R1) for chain-of-thought-heavy synthesis.
    """
    s = settings or load_settings()
    if not s.deepseek_api_key:
        raise RuntimeError(
            "DEEPSEEK_API_KEY env var is missing. Add it to your .env file."
        )
    return ChatOpenAI(
        api_key=s.deepseek_api_key,
        base_url=s.deepseek_base_url,
        model=s.deepseek_model,
        temperature=temperature,
        **kwargs,
    )
