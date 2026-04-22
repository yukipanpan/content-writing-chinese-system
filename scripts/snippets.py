"""
snippets.py — Snippet generation, deduplication, and update logic.

Given fetched URL content, this module:
  1. Generates a candidate snippet via Claude
  2. Compares it against existing snippets to detect overlap
  3. Either creates a new snippet file or updates an existing one
"""

import json
import re
import sys
from datetime import date
from pathlib import Path

import llm


SNIPPET_DIR = Path("references/snippets")
SKILL_ROOT  = Path(__file__).parent.parent / "skills"
SNIPPET_TPL = SKILL_ROOT / "assets/templates/snippet.md"


# ── Existing snippet index ───────────────────────────────────────────────────

def build_snippet_index(snippet_dir: Path) -> list[dict]:
    """
    Read all existing snippets and extract lightweight metadata for dedup checks.
    Returns a list of dicts: {filename, title, summary, tags, topic}
    """
    index = []
    for f in sorted(snippet_dir.glob("*.md")):
        meta = _parse_frontmatter(f)
        index.append({
            "filename": f.name,
            "stem":     f.stem,
            "title":    _extract_heading(f),
            "summary":  meta.get("一句话总结", ""),
            "topic":    meta.get("topic", ""),
            "tags":     meta.get("tags", ""),
        })
    return index


def _parse_frontmatter(filepath: Path) -> dict:
    """Extract key-value pairs from a markdown snippet's body sections."""
    text = filepath.read_text(errors="ignore")
    result = {}
    # 一句话总结 is under a ## heading
    m = re.search(r"## 一句话总结\s*\n+([^\n#]+)", text)
    if m:
        result["一句话总结"] = m.group(1).strip()
    # topic / tags from YAML-like frontmatter block
    m = re.search(r"topic:\s*\n((?:\s*-\s*.+\n)+)", text)
    if m:
        result["topic"] = m.group(1).strip()
    m = re.search(r"tags:\s*\n((?:\s*-\s*.+\n)+)", text)
    if m:
        result["tags"] = m.group(1).strip()
    return result


def _extract_heading(filepath: Path) -> str:
    text = filepath.read_text(errors="ignore")
    m = re.search(r"^## (.+)$", text, re.MULTILINE)
    return m.group(1).strip() if m else filepath.stem


# ── Claude: generate candidate snippet ──────────────────────────────────────

def generate_candidate(url: str, source_content: str, today: str) -> str:
    """Ask the LLM to produce a snippet following the snippet.md template."""
    template = SNIPPET_TPL.read_text()

    system = (
        "You are a content analyst. "
        "Your task is to produce a structured snippet following the template exactly. "
        "Output ONLY the snippet markdown — no commentary before or after.\n\n"
        f"## Snippet Template\n\n{template}"
    )
    user = (
        f"Today's date: {today}\n"
        f"Source URL: {url}\n\n"
        f"Source content:\n\n{source_content}\n\n"
        "Generate a complete snippet for this content following the template. "
        "For the id field use: S-YYYYMMDD-AUTO (the workflow will assign the real XXXX). "
        "Set created and updated to today's date. "
        "Derive the file-name date from the source publication date, not today."
    )

    return llm.chat(system, user, max_tokens=2048)


# ── Claude: deduplication check ─────────────────────────────────────────────

def find_duplicate(candidate_snippet: str, index: list[dict]) -> str | None:
    """
    Ask Claude whether the candidate overlaps with any existing snippet.
    Returns the matching filename, or None if it's a new topic.
    """
    if not index:
        return None

    index_text = "\n".join(
        f"- {item['filename']}: {item['title']} | {item['summary']}"
        for item in index
    )

    system = (
        "You are a deduplication assistant for a Polkadot content knowledge base. "
        "Your job is to determine if a new snippet covers the same event or topic "
        "as an existing snippet. Be conservative: only flag a duplicate if they "
        "are clearly about the same real-world event, proposal, or announcement."
    )
    user = (
        f"## New snippet\n\n{candidate_snippet}\n\n"
        f"## Existing snippets index\n\n{index_text}\n\n"
        "Does the new snippet cover the same event or topic as any existing snippet?\n"
        "Reply with JSON only:\n"
        '{"is_duplicate": true, "matching_filename": "20260106-xxx.md", "reason": "..."}\n'
        "or\n"
        '{"is_duplicate": false}'
    )

    raw = llm.chat(system, user, max_tokens=256)
    # Strip markdown code fences if present
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()
    try:
        result = json.loads(raw)
        if result.get("is_duplicate") and result.get("matching_filename"):
            print(
                f"  ↩ duplicate detected → {result['matching_filename']} "
                f"({result.get('reason', '')})",
                file=sys.stderr,
            )
            return result["matching_filename"]
    except json.JSONDecodeError:
        print(f"  ⚠ dedup JSON parse failed: {raw[:120]}", file=sys.stderr)

    return None


# ── Claude: merge into existing snippet ──────────────────────────────────────

def merge_into_existing(
    existing_path: Path,
    candidate_snippet: str,
    new_url: str,
    today: str,
) -> tuple[str, str]:
    """
    Ask Claude to merge the new information into the existing snippet.
    Returns (updated_content, new_filename).
    """
    template = SNIPPET_TPL.read_text()
    existing = existing_path.read_text()

    system = (
        "You are updating a versioned Polkadot snippet. "
        "Follow the snippet template update rules exactly: "
        "append to sources, prepend to 更新日志, rewrite 核心要点 / 一句话总结 / 段落总结 "
        "to reflect the latest state, and update the filename date if needed.\n\n"
        f"## Snippet Template (for update rules)\n\n{template}"
    )
    user = (
        f"Today: {today}\n"
        f"New source URL: {new_url}\n\n"
        f"## Existing snippet\n\n{existing}\n\n"
        f"## New information (candidate snippet)\n\n{candidate_snippet}\n\n"
        "Produce the fully updated snippet. "
        "Also output the correct new filename on a line starting with 'FILENAME: '. "
        "Apply the date-rollback rule if the event status changed."
    )

    text = llm.chat(system, user, max_tokens=3000)

    # Extract filename if Claude provided one
    filename_match = re.search(r"^FILENAME:\s*(.+\.md)", text, re.MULTILINE)
    if filename_match:
        new_filename = filename_match.group(1).strip()
        content = re.sub(r"^FILENAME:\s*.+\n?", "", text, flags=re.MULTILINE).strip()
    else:
        new_filename = existing_path.name
        content = text

    return content, new_filename


# ── File operations ──────────────────────────────────────────────────────────

def save_snippet(content: str, filename: str, snippet_dir: Path) -> Path:
    snippet_dir.mkdir(parents=True, exist_ok=True)
    path = snippet_dir / filename
    # Avoid silently overwriting an unrelated existing snippet
    if path.exists():
        stem = Path(filename).stem
        suffix = Path(filename).suffix
        for i in range(2, 100):
            candidate = snippet_dir / f"{stem}-{i}{suffix}"
            if not candidate.exists():
                path = candidate
                print(f"  ⚠ filename collision, saving as {path.name}", file=sys.stderr)
                break
    path.write_text(content)
    return path


def derive_filename_from_candidate(candidate: str, today: str) -> str:
    """Guess a filename from the candidate snippet content."""
    # Try to find the heading title
    m = re.search(r"^## (.+)$", candidate, re.MULTILINE)
    title = m.group(1).strip() if m else "untitled"
    # Try to get source date from candidate frontmatter
    m = re.search(r"date:\s+['\"]?(\d{4}-\d{2}-\d{2})", candidate)
    if m:
        src_date = m.group(1).replace("-", "")
    else:
        src_date = today.replace("-", "")
    slug = re.sub(r"[^\w\u4e00-\u9fff-]", "-", title)[:40].strip("-")
    return f"{src_date}-{slug}.md"


# ── Public interface ─────────────────────────────────────────────────────────

class SnippetResult:
    def __init__(self, action: str, filename: str, path: Path):
        self.action   = action    # "created" | "updated"
        self.filename = filename
        self.path     = path

    def __str__(self):
        icon = "✨" if self.action == "created" else "↩"
        return f"{icon} [{self.action}] {self.filename}"


def process_url(
    url: str,
    source_content: str,
    snippet_dir: Path = SNIPPET_DIR,
) -> SnippetResult:
    """
    Full pipeline for one URL:
      generate candidate → dedup check → create or update.
    """
    today = date.today().isoformat()
    index = build_snippet_index(snippet_dir)

    print(f"  generating snippet for: {url}", file=sys.stderr)
    candidate = generate_candidate(url, source_content, today)

    duplicate_filename = find_duplicate(candidate, index)

    if duplicate_filename:
        existing_path = snippet_dir / duplicate_filename
        updated_content, new_filename = merge_into_existing(
            existing_path, candidate, url, today
        )
        new_path = snippet_dir / new_filename
        if new_path != existing_path:
            existing_path.unlink()
        new_path.write_text(updated_content)
        return SnippetResult("updated", new_filename, new_path)
    else:
        filename = derive_filename_from_candidate(candidate, today)
        path = save_snippet(candidate, filename, snippet_dir)
        return SnippetResult("created", filename, path)


def process_all(
    fetched: list[tuple[str, str]],  # list of (url, content)
    snippet_dir: Path = SNIPPET_DIR,
) -> list[SnippetResult]:
    """Process all fetched URLs. Returns list of SnippetResult."""
    results = []
    for url, content in fetched:
        result = process_url(url, content, snippet_dir)
        print(f"  {result}", file=sys.stderr)
        results.append(result)
    return results
