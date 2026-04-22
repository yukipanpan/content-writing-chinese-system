"""Input validation — fail fast with clear error messages."""

import re
import sys
from urllib.parse import urlparse


def validate_urls(urls: list[str]) -> None:
    for url in urls:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            sys.exit(
                f"❌ Invalid URL (must start with http:// or https://): {url!r}\n"
                "   Check for typos or missing protocol prefix."
            )
        if not parsed.netloc:
            sys.exit(
                f"❌ Invalid URL (missing domain): {url!r}"
            )


def validate_intent(intent: str) -> None:
    stripped = intent.strip()
    if len(stripped) < 10:
        sys.exit(
            f"❌ --intent is too short ({len(stripped)} chars). "
            "Describe what you want to write in at least one sentence.\n"
            f"   Got: {intent!r}"
        )
    if len(stripped) > 500:
        sys.exit(
            f"❌ --intent is too long ({len(stripped)} chars, max 500). "
            "Keep it to 1-3 sentences."
        )


def validate_month(month: str) -> None:
    if not re.fullmatch(r"\d{4}-(?:0[1-9]|1[0-2])", month):
        sys.exit(
            f"❌ --month must be in YYYY-MM format (e.g. 2026-04), got: {month!r}"
        )


def validate_phase1(urls: list[str], topic: str | None, intent: str) -> None:
    if not urls and not topic:
        sys.exit(
            "❌ Provide at least one of --urls or --topic.\n"
            "   --urls: comma-separated source URLs\n"
            "   --topic: keyword for auto-discovery (e.g. 'Polkadot JAM 2025')"
        )
    if urls:
        validate_urls(urls)
    validate_intent(intent)


def validate_phase2(pr_body_file: str) -> None:
    from pathlib import Path
    path = Path(pr_body_file)
    if not path.exists():
        sys.exit(
            f"❌ PR body file not found: {pr_body_file!r}\n"
            "   Run phase1 first to generate it."
        )
    if path.stat().st_size == 0:
        sys.exit(
            f"❌ PR body file is empty: {pr_body_file!r}\n"
            "   The phase1 run may have failed — check for errors above."
        )
