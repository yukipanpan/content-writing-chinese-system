"""
llm.py — Provider-agnostic LLM client.

Reads LLM_PROVIDER from environment (default: anthropic).
Exposes a single function: chat(system, user, max_tokens) → str

Supported providers:
  anthropic  — requires ANTHROPIC_API_KEY
  openai     — requires OPENAI_API_KEY; set OPENAI_MODEL to override default
  ollama     — requires OLLAMA_BASE_URL (default: http://localhost:11434);
               set OLLAMA_MODEL to choose model
"""

import os
import sys

PROVIDER = os.environ.get("LLM_PROVIDER", "anthropic").lower()


def chat(system: str, user: str, max_tokens: int = 2048) -> str:
    if PROVIDER == "anthropic":
        return _chat_anthropic(system, user, max_tokens)
    elif PROVIDER == "openai":
        return _chat_openai(system, user, max_tokens)
    elif PROVIDER == "ollama":
        return _chat_ollama(system, user, max_tokens)
    else:
        sys.exit(f"Unknown LLM_PROVIDER: {PROVIDER!r}. Choose: anthropic, openai, ollama")


# ── Anthropic ─────────────────────────────────────────────────────────────────

def _chat_anthropic(system: str, user: str, max_tokens: int) -> str:
    import anthropic

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("ANTHROPIC_API_KEY is not set")

    model = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
    client = anthropic.Anthropic(api_key=api_key)
    resp = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return resp.content[0].text.strip()


# ── OpenAI ────────────────────────────────────────────────────────────────────

def _chat_openai(system: str, user: str, max_tokens: int) -> str:
    try:
        from openai import OpenAI
    except ImportError:
        sys.exit("openai package is not installed. Run: pip install openai")

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        sys.exit("OPENAI_API_KEY is not set")

    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
    )
    return resp.choices[0].message.content.strip()


# ── Ollama ────────────────────────────────────────────────────────────────────

def _chat_ollama(system: str, user: str, max_tokens: int) -> str:
    try:
        import requests
    except ImportError:
        sys.exit("requests package is not installed. Run: pip install requests")

    base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    model    = os.environ.get("OLLAMA_MODEL", "llama3")

    payload = {
        "model":  model,
        "stream": False,
        "options": {"num_predict": max_tokens},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
    }
    resp = requests.post(f"{base_url}/api/chat", json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json()["message"]["content"].strip()
