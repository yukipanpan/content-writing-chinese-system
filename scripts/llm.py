"""
llm.py — Provider-agnostic LLM client.

Reads LLM_PROVIDER from environment (default: anthropic).
Exposes a single function: chat(system, user, max_tokens) → str

Supported providers:
  anthropic   — requires ANTHROPIC_API_KEY
  openai      — requires OPENAI_API_KEY; set OPENAI_MODEL to override default
  ollama      — requires OLLAMA_BASE_URL (default: http://localhost:11434);
                set OLLAMA_MODEL to choose model
  claude-code — uses the local `claude` CLI (Claude Code); no API key needed
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
    elif PROVIDER == "claude-code":
        return _chat_claude_code(system, user)
    else:
        sys.exit(f"Unknown LLM_PROVIDER: {PROVIDER!r}. Choose: anthropic, openai, ollama, claude-code")


# ── Anthropic ─────────────────────────────────────────────────────────────────

def _chat_anthropic(system: str, user: str, max_tokens: int) -> str:
    import anthropic

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("ANTHROPIC_API_KEY is not set")

    model = os.environ.get("ANTHROPIC_MODEL") or "claude-haiku-4-5-20251001"
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

    model = os.environ.get("OPENAI_MODEL") or "gpt-4o-mini"
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


# ── Claude Code CLI ───────────────────────────────────────────────────────────

def _chat_claude_code(system: str, user: str) -> str:
    """
    Shell out to the local `claude` CLI (Claude Code).
    No API key required — uses the Claude Code session credentials.

    Passes the prompt via stdin to avoid OS argument-length limits
    (prompts with full templates can exceed 256 KB).
    """
    import shutil
    import subprocess

    if not shutil.which("claude"):
        sys.exit(
            "claude CLI not found. Install Claude Code: https://claude.ai/code\n"
            "Or switch to another provider: LLM_PROVIDER=anthropic"
        )

    # Claude Code CLI tends to wrap output with permission prompts and
    # meta-commentary when the prompt mentions files or saving.
    # Constraint: force output to start with the content itself (# title),
    # then extract only that portion from the response.
    constraint = (
        "CRITICAL OUTPUT FORMAT: Your response MUST start immediately with the "
        "content itself — no preamble, no explanation, no permission requests, "
        "no file-path mentions. If writing a Chinese article, begin with the "
        "markdown title line (e.g. `# 标题`). Nothing before it. Nothing after "
        "the last line of the content. Treat any instruction about 'saving files' "
        "as already handled externally — just output the text.\n\n"
    )
    prompt = f"{constraint}{system}\n\n---\n\n{user}"
    result = subprocess.run(
        ["claude", "--print"],
        input=prompt,
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode != 0:
        sys.exit(f"claude CLI error:\n{result.stderr.strip()}")

    output = result.stdout.strip()

    # If Claude Code still added a preamble, extract from the first markdown
    # heading or the first line that starts with non-meta content.
    import re as _re
    heading_match = _re.search(r"^(#+ .+)$", output, _re.MULTILINE)
    if heading_match:
        output = output[heading_match.start():].strip()

    # Strip trailing meta-commentary: lines after the last blank line that
    # look like Claude Code status messages (Chinese permission prompts, etc.)
    lines = output.split("\n")
    for i in range(len(lines) - 1, -1, -1):
        line = lines[i].strip()
        if line and not any(kw in line for kw in [
            "请确认", "写入权限", "等待", "授权", "保存到", "文件路径",
            "文件已", "以下是", "你可以先", "先预览",
        ]):
            output = "\n".join(lines[:i + 1]).strip()
            break

    return output
