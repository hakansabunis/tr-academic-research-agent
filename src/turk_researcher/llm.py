from __future__ import annotations

from langchain_openai import ChatOpenAI

from .config import Settings, load_settings

_LOCAL_HINTS = ("localhost", "127.0.0.1", "0.0.0.0", "host.docker.internal")


def build_llm(settings: Settings | None = None, *, temperature: float = 0.2, **kwargs) -> ChatOpenAI:
    """Provider-independent chat model over any OpenAI-compatible endpoint.

    Configured via LLM_* env (falls back to DEEPSEEK_* — existing setups
    unchanged):

      Cloud:  LLM_BASE_URL / LLM_API_KEY / LLM_MODEL
              e.g. OpenRouter, OpenAI, Groq, Together, DeepSeek (default)
      Local:  LLM_BASE_URL=http://localhost:11434/v1  (Ollama / vLLM /
              LM Studio) — no key needed, fully offline, no DeepSeek.

    Note: the pipeline uses tool/function-calling for structured output, so
    pick a tool-calling-capable model (most cloud models; for Ollama use a
    tools-capable model such as qwen2.5/llama3.1).
    """
    s = settings or load_settings()
    base_url = s.llm_base_url
    api_key = s.llm_api_key
    is_local = any(h in (base_url or "") for h in _LOCAL_HINTS)

    if not api_key:
        if is_local:
            api_key = "sk-noauth"          # local servers ignore the key
        else:
            raise RuntimeError(
                "No LLM credentials. Set LLM_API_KEY (+ LLM_BASE_URL / "
                "LLM_MODEL) for any OpenAI-compatible provider, or "
                "DEEPSEEK_API_KEY for the default. For a local model set "
                "LLM_BASE_URL=http://localhost:11434/v1 (no key needed)."
            )

    return ChatOpenAI(
        api_key=api_key,
        base_url=base_url,
        model=s.llm_model,
        temperature=temperature,
        **kwargs,
    )
