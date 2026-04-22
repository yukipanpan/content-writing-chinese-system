"""
pipeline.py — Business logic for phase1, phase2, and monthly-recap.

Imported by run_skill.py (CLI entry point). Can also be imported directly
by other tools or tests.
"""

import json
import re
import sys
from datetime import date
from pathlib import Path

import llm
from fetcher import fetch_all
from snippets import process_all, SNIPPET_DIR
from discover import discover_urls
from validate import validate_phase1, validate_phase2, validate_month

# ── Paths ────────────────────────────────────────────────────────────────────

SKILL_ROOT = Path(__file__).parent.parent / "skills"
STYLE_BASE = SKILL_ROOT / "assets/styles/_base.md"
ROUTER     = SKILL_ROOT / "SKILL.MD"

TEMPLATE_MAP = {
    "analytical":        SKILL_ROOT / "assets/templates/web-remix-to-csdn.md",
    "tutorial":          SKILL_ROOT / "assets/templates/polkadot-docs-to-csdn.md",
    "concept-explainer": SKILL_ROOT / "assets/templates/wiki-to-csdn.md",
    "video-summary":     SKILL_ROOT / "assets/templates/youtube-remix-to-csdn.md",
    "monthly-recap":     SKILL_ROOT / "assets/templates/monthly-recap.md",
}

OUTPUT_DIRS = {
    "analytical":        Path("output/analysis"),
    "tutorial":          Path("output/tutorials"),
    "concept-explainer": Path("output/explainers"),
    "video-summary":     Path("output/science-pop"),
    "monthly-recap":     Path("output/monthly-recap"),
}

METADATA_MARKER = "<!-- CONTENT_METADATA"


# ── Article type inference ────────────────────────────────────────────────────

def infer_article_type(intent: str, urls: list[str]) -> str:
    system = (
        "You classify content requests into one of four article types:\n"
        "- analytical: opinion/analysis, multi-source commentary\n"
        "- tutorial: step-by-step how-to guide, usually from official docs\n"
        "- concept-explainer: explains a mechanism or concept in depth, usually from wiki\n"
        "- video-summary: pop-science article based on a YouTube video\n\n"
        'Reply with JSON only: {"type": "<one of the four>", "reason": "<1 sentence>"}'
    )
    url_hint = "\n".join(urls)
    user = f"User intent: {intent}\n\nSource URLs:\n{url_hint}"

    raw = llm.chat(system, user, max_tokens=128)
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()
    try:
        result = json.loads(raw)
        article_type = result.get("type", "analytical")
        reason = result.get("reason", "")
        if article_type not in TEMPLATE_MAP:
            article_type = "analytical"
        print(f"  inferred type: {article_type} — {reason}", file=sys.stderr)
        return article_type
    except json.JSONDecodeError:
        print("  ⚠ type inference failed, defaulting to analytical", file=sys.stderr)
        return "analytical"


# ── Outline generation ────────────────────────────────────────────────────────

_OUTLINE_SYSTEM = """
You are a content strategist producing an English article outline.
The full article will be written in Chinese later — this outline is for an
English-speaking editor to review and approve the direction before writing begins.
Keep the outline in English. Be specific and opinionated.
"""

_OUTLINE_PROMPT = """
Based on the source material below, produce a structured English outline.

Output ONLY this format (no text outside the tags):

<outline>
**Working title:** [specific, opinionated title — not generic]

**Type:** {article_type}

**Thesis / angle:** [1-2 sentences — the unique perspective this article takes]

**Sections:**
1. [Section title] — [what this section covers and why it matters]
2. [Section title] — [what this covers]
3. [Section title] — [what this covers]
4. [Section title] — [what this covers]
(add or remove sections as needed)

**Key claims to make:**
- [claim 1]
- [claim 2]
- [claim 3]

**Sources used:** [list URLs that will be cited]
**KB references:** [any existing snippets/articles to blend in, or "none"]
</outline>

User's intent: {intent}

Source material:
{source_content}
"""


def generate_outline(source_content: str, article_type: str, intent: str) -> str:
    prompt = _OUTLINE_PROMPT.format(
        article_type=article_type,
        intent=intent,
        source_content=source_content[:12000],
    )
    raw = llm.chat(_OUTLINE_SYSTEM, prompt, max_tokens=1500)
    m = re.search(r"<outline>(.*?)</outline>", raw, re.DOTALL)
    return m.group(1).strip() if m else raw


# ── Article generation ────────────────────────────────────────────────────────

def generate_article(outline: str, source_content: str, article_type: str, intent: str) -> str:
    template = TEMPLATE_MAP[article_type].read_text()
    style    = STYLE_BASE.read_text()
    router   = ROUTER.read_text()

    system = (
        "You are a content specialist writing in Chinese (中文).\n\n"
        f"## System Router\n{router}\n\n"
        f"## Writing Style\n{style}\n\n"
        f"## Active Template\n{template}\n\n"
        "IMPORTANT: Write the full article in Chinese. "
        "Follow the active template's rules for structure, quality checklist, and file format. "
        "Apply the humanizer-zh rules inline (do not output a comparison — just write naturally). "
        "The article must not read like AI output."
    )
    user = (
        f"User's intent: {intent}\n\n"
        f"## Approved English outline\n\n{outline}\n\n"
        f"## Source material\n\n{source_content[:10000]}\n\n"
        "Write the complete Chinese article now. Follow the outline's structure and thesis."
    )
    return llm.chat(system, user, max_tokens=8192)


# ── PR body ───────────────────────────────────────────────────────────────────

def build_pr_body(
    urls: list[str],
    snippet_results: list,
    article_type: str,
    intent: str,
    outline: str,
    metadata: dict,
    manual_urls: list[str] | None = None,
    discovered_urls: list[str] | None = None,
    kb_matches: dict[str, str] | None = None,
) -> str:
    manual_urls     = manual_urls     or []
    discovered_urls = discovered_urls or []
    kb_matches      = kb_matches      or {}

    source_sections = []
    if manual_urls:
        lines = "\n".join(f"- {u}" for u in manual_urls)
        source_sections.append(f"**Manual ({len(manual_urls)}):**\n{lines}")
    if discovered_urls:
        lines = "\n".join(f"- {u}" for u in discovered_urls)
        source_sections.append(f"**Auto-discovered ({len(discovered_urls)}):**\n{lines}")
    if kb_matches:
        lines = "\n".join(f"- `{v}` — {k}" for k, v in kb_matches.items())
        source_sections.append(f"**Loaded from knowledge base ({len(kb_matches)}):**\n{lines}")
    if not source_sections:
        source_sections.append("\n".join(f"- {u}" for u in urls))

    source_lines = "\n\n".join(source_sections)
    snippet_lines = "_(snippets not generated)_"
    if snippet_results:
        snippet_lines = "\n".join(f"- `{r.filename}` — **{r.action}**" for r in snippet_results)

    meta_json  = json.dumps(metadata, ensure_ascii=False, indent=2)
    output_dir = OUTPUT_DIRS.get(article_type, Path("output/analysis"))

    return f"""## 📋 Sources fetched

{source_lines}

## 📦 Snippets

{snippet_lines}

---

## ✏️ Outline — review and edit before approving

> **Edit this section directly** if you want to change the angle, add/remove sections, or adjust claims.
> When you're happy, comment `/generate` to produce the Chinese article.

**Inferred type:** `{article_type}`
**Output folder:** `{output_dir}/`
**Intent:** {intent}

{outline}

---

> ✅ Happy with the outline? Comment `/generate` below.
> ✏️ Want changes? Edit the outline above first, then comment `/generate`.

{METADATA_MARKER}
{meta_json}
-->"""


def parse_pr_body(pr_body: str) -> tuple[str, dict]:
    meta_match = re.search(
        rf"{re.escape(METADATA_MARKER)}\s*(.*?)\s*-->",
        pr_body, re.DOTALL
    )
    metadata: dict = {}
    if meta_match:
        try:
            metadata = json.loads(meta_match.group(1))
        except json.JSONDecodeError:
            pass

    outline_match = re.search(r"## ✏️ Outline.*?\n\n(.*?)\n---", pr_body, re.DOTALL)
    if outline_match:
        raw = outline_match.group(1)
        raw = re.sub(r"^>.*\n?", "", raw, flags=re.MULTILINE).strip()
        outline = raw
    else:
        outline = pr_body

    return outline, metadata


# ── KB deduplication ──────────────────────────────────────────────────────────

def find_kb_matches(urls: list[str], snippet_dir: Path) -> dict[str, str]:
    if not snippet_dir.exists():
        return {}
    url_index: dict[str, str] = {}
    for f in snippet_dir.glob("*.md"):
        text = f.read_text(errors="ignore")
        for match in re.finditer(r'url:\s*"([^"]+)"', text):
            url_index[match.group(1).strip()] = f.name
    return {url: url_index[url] for url in urls if url in url_index}


# ── Helpers ───────────────────────────────────────────────────────────────────

def parse_urls(raw: str) -> list[str]:
    return [u.strip() for u in re.split(r"[,\n]+", raw) if u.strip()]


def save_article(content: str, article_type: str, urls: list[str], output_dir: str | None) -> Path:
    out = Path(output_dir) if output_dir else OUTPUT_DIRS.get(article_type, Path("output"))
    out.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^\w-]", "", (urls[0] if urls else "article").split("/")[-1])[:40]
    filename = f"{date.today().strftime('%Y%m%d')}-{slug}.md"
    path = out / filename
    path.write_text(content)
    print(f"  article saved → {path}", file=sys.stderr)
    return path


# ── Phase runners ─────────────────────────────────────────────────────────────

def run_phase1(args) -> None:
    manual_urls: list[str]     = parse_urls(args.urls or "")
    discovered_urls: list[str] = []

    validate_phase1(manual_urls, args.topic, args.intent)

    total_steps = 5 if args.topic else 4

    if args.topic:
        n = getattr(args, "top_n", 5)
        print(f"\n[1/{total_steps}] Discovering sources for topic: {args.topic!r}…", file=sys.stderr)
        discovered_urls = discover_urls(args.topic, args.intent, n=n)
        print(f"  found {len(discovered_urls)} URL(s)", file=sys.stderr)
    else:
        print("\n[Skipping auto-discovery — no --topic provided]", file=sys.stderr)

    seen: set[str] = set()
    all_urls: list[str] = []
    for url in manual_urls + discovered_urls:
        if url not in seen:
            seen.add(url)
            all_urls.append(url)

    step = 2 if args.topic else 1

    print(f"\n[{step}/{total_steps}] Checking knowledge base for cached sources…", file=sys.stderr)
    kb_matches = find_kb_matches(all_urls, SNIPPET_DIR)
    for url, fname in kb_matches.items():
        print(f"  ↩ KB hit: {fname} ← {url}", file=sys.stderr)
    step += 1

    urls_to_fetch = [u for u in all_urls if u not in kb_matches]
    print(f"\n[{step}/{total_steps}] Fetching {len(urls_to_fetch)} URL(s)…", file=sys.stderr)
    source_content, fetch_warnings = fetch_all(urls_to_fetch)
    for w in fetch_warnings:
        print(f"  {w}", file=sys.stderr)
    step += 1

    snippet_results = []
    if args.generate_snippets:
        print(f"\n[{step}/{total_steps}] Generating & deduplicating snippets…", file=sys.stderr)
        fetched_pairs = [(url, source_content) for url in urls_to_fetch]
        snippet_results = process_all(fetched_pairs, SNIPPET_DIR)
    step += 1

    print(f"\n[{step}/{total_steps}] Inferring article type & generating outline…", file=sys.stderr)
    article_type = infer_article_type(args.intent, all_urls)
    outline      = generate_outline(source_content, article_type, args.intent)

    metadata = {
        "source_urls":     all_urls,
        "manual_urls":     manual_urls,
        "discovered_urls": discovered_urls,
        "kb_matches":      kb_matches,
        "article_type":    article_type,
        "intent":          args.intent,
        "snippet_files":   [r.filename for r in snippet_results],
    }

    pr_body = build_pr_body(
        all_urls, snippet_results, article_type, args.intent, outline, metadata,
        manual_urls=manual_urls,
        discovered_urls=discovered_urls,
        kb_matches=kb_matches,
    )
    Path(args.pr_body_file).write_text(pr_body)
    print(f"\n  PR body written → {args.pr_body_file}", file=sys.stderr)

    if snippet_results:
        Path("snippet_changes.txt").write_text("\n".join(r.filename for r in snippet_results))


def run_phase2(args) -> None:
    validate_phase2(args.pr_body_file)
    pr_body = Path(args.pr_body_file).read_text()
    outline, metadata = parse_pr_body(pr_body)

    urls         = metadata.get("source_urls", [])
    article_type = metadata.get("article_type", "analytical")
    intent       = metadata.get("intent", "")

    print("\n[1/2] Re-fetching source content for article generation…", file=sys.stderr)
    source_content, _ = fetch_all(urls)

    print(f"\n[2/2] Generating Chinese article ({article_type})…", file=sys.stderr)
    article = generate_article(outline, source_content, article_type, intent)
    save_article(article, article_type, urls, args.output_dir)


def run_monthly_recap(args) -> None:
    validate_month(args.month)

    template = (SKILL_ROOT / "assets/templates/monthly-recap.md").read_text()
    style    = STYLE_BASE.read_text()

    prefix  = args.month.replace("-", "")
    matched = sorted(SNIPPET_DIR.glob(f"{prefix}*.md"))

    if not matched:
        sys.exit(f"No snippets found for {args.month} in {SNIPPET_DIR}")

    print(f"  {len(matched)} snippets found for {args.month}", file=sys.stderr)

    snippet_contents = "\n\n---\n\n".join(
        f"### {f.stem}\n\n{f.read_text(errors='ignore')}" for f in matched
    )
    system = (
        "You are a monthly recap writer. Write in Chinese (中文).\n\n"
        f"## Writing Style\n{style}\n\n"
        f"## Monthly Recap Template\n{template}"
    )
    user = f"Generate the monthly recap for {args.month}.\n\nSnippets ({len(matched)} total):\n\n{snippet_contents}"

    article = llm.chat(system, user, max_tokens=8192)

    out = Path("output/monthly-recap")
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{args.month}.md"
    path.write_text(article)
    print(f"  saved → {path}", file=sys.stderr)
