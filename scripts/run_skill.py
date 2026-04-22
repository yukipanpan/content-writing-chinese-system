"""
run_skill.py — Two-phase article generation orchestrator.

Phase 1 (generate.yml calls this):
  fetch URLs → generate snippets → infer article type → English outline → PR metadata

Phase 2 (on-generate-comment.yml calls this):
  read outline + metadata from PR → generate Chinese article

Usage:
  # Phase 1
  python3 scripts/run_skill.py phase1 \
    --urls "https://a.com, https://youtu.be/xyz" \
    --intent "write a tutorial on XCM for Ethereum devs" \
    --generate-snippets \
    --pr-body-file pr_body.md

  # Phase 2
  python3 scripts/run_skill.py phase2 \
    --pr-body-file pr_body.md \
    --output-dir output/polkadot-hype-articles
"""

import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

# Load .env if present (local development)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import llm

from fetcher import fetch_all, FetchResult
from snippets import process_all, SNIPPET_DIR

# ── Paths ────────────────────────────────────────────────────────────────────

SKILL_ROOT = Path(__file__).parent.parent / "skills"
STYLE_BASE = SKILL_ROOT / "assets/styles/_base.md"
ROUTER     = SKILL_ROOT / "SKILL.MD"

TEMPLATE_MAP = {
    "analytical":         SKILL_ROOT / "assets/templates/web-remix-to-csdn.md",
    "tutorial":           SKILL_ROOT / "assets/templates/polkadot-docs-to-csdn.md",
    "concept-explainer":  SKILL_ROOT / "assets/templates/wiki-to-csdn.md",
    "video-summary":      SKILL_ROOT / "assets/templates/youtube-remix-to-csdn.md",
    "monthly-recap":      SKILL_ROOT / "assets/templates/monthly-recap.md",
}

OUTPUT_DIRS = {
    "analytical":         Path("output/analysis"),        # 分析 / 观点文章
    "tutorial":           Path("output/tutorials"),       # 操作教程
    "concept-explainer":  Path("output/explainers"),      # 机制解析 / 科普
    "video-summary":      Path("output/science-pop"),     # 视频改编科普
    "monthly-recap":      Path("output/monthly-recap"),   # 月度回顾
}

# Marker used to embed machine-readable metadata inside the PR description
METADATA_MARKER = "<!-- CONTENT_METADATA"


# ── Article type inference ───────────────────────────────────────────────────

def infer_article_type(intent: str, urls: list[str]) -> str:
    """
    Ask the LLM to pick the best article type from the user's free-text intent.
    Returns one of the TEMPLATE_MAP keys.
    """
    system = (
        "You classify content requests into one of four article types:\n"
        "- analytical: opinion/analysis, multi-source commentary\n"
        "- tutorial: step-by-step how-to guide, usually from official docs\n"
        "- concept-explainer: explains a mechanism or concept in depth, usually from wiki\n"
        "- video-summary: pop-science article based on a YouTube video\n\n"
        "Reply with JSON only: {\"type\": \"<one of the four>\", \"reason\": \"<1 sentence>\"}"
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
        print(f"  ⚠ type inference failed, defaulting to analytical", file=sys.stderr)
        return "analytical"


# ── Outline generation (Phase 1) ─────────────────────────────────────────────

OUTLINE_SYSTEM = """
You are a content strategist producing an English article outline.
The full article will be written in Chinese later — this outline is for an
English-speaking editor to review and approve the direction before writing begins.
Keep the outline in English. Be specific and opinionated.
"""

OUTLINE_PROMPT = """
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
    prompt = OUTLINE_PROMPT.format(
        article_type=article_type,
        intent=intent,
        source_content=source_content[:12000],
    )
    raw = llm.chat(OUTLINE_SYSTEM, prompt, max_tokens=1500)
    m = re.search(r"<outline>(.*?)</outline>", raw, re.DOTALL)
    return m.group(1).strip() if m else raw


# ── Article generation (Phase 2) ─────────────────────────────────────────────

def generate_article(outline: str, source_content: str, article_type: str, intent: str) -> str:
    template = TEMPLATE_MAP[article_type].read_text()
    style    = STYLE_BASE.read_text()
    router   = ROUTER.read_text()

    system = (
        f"You are a content specialist writing in Chinese (中文).\n\n"
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


# ── PR body builder ───────────────────────────────────────────────────────────

def build_pr_body(
    urls: list[str],
    snippet_results: list,
    article_type: str,
    intent: str,
    outline: str,
    metadata: dict,
) -> str:
    source_lines = "\n".join(f"- {u}" for u in urls)

    snippet_lines = "_(snippets not generated)_"
    if snippet_results:
        snippet_lines = "\n".join(
            f"- `{r.filename}` — **{r.action}**" for r in snippet_results
        )

    meta_json = json.dumps(metadata, ensure_ascii=False, indent=2)

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


# ── PR body parser (Phase 2) ──────────────────────────────────────────────────

def parse_pr_body(pr_body: str) -> tuple[str, dict]:
    """
    Extract outline and metadata from a PR description.
    Returns (outline_text, metadata_dict).
    """
    # Extract metadata JSON
    meta_match = re.search(
        rf"{re.escape(METADATA_MARKER)}\s*(.*?)\s*-->",
        pr_body, re.DOTALL
    )
    metadata = {}
    if meta_match:
        try:
            metadata = json.loads(meta_match.group(1))
        except json.JSONDecodeError:
            pass

    # Extract outline — everything between the outline section header and the hr
    outline_match = re.search(
        r"## ✏️ Outline.*?\n\n(.*?)\n---",
        pr_body, re.DOTALL
    )
    if outline_match:
        # Strip the blockquote instructions at the top
        raw = outline_match.group(1)
        raw = re.sub(r"^>.*\n?", "", raw, flags=re.MULTILINE).strip()
        outline = raw
    else:
        outline = pr_body  # fallback: use full body

    return outline, metadata


# ── Output helpers ────────────────────────────────────────────────────────────

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


# ── Phase 1 ───────────────────────────────────────────────────────────────────

def phase1(args):
    urls = parse_urls(args.urls)
    if not urls:
        sys.exit("--urls is required for phase1")

    # 1. Fetch all URLs
    print(f"\n[1/4] Fetching {len(urls)} URL(s)…", file=sys.stderr)
    source_content, fetch_warnings = fetch_all(urls)
    for w in fetch_warnings:
        print(f"  {w}", file=sys.stderr)

    # 2. Generate snippets (optional)
    snippet_results = []
    if args.generate_snippets:
        print(f"\n[2/4] Generating & deduplicating snippets…", file=sys.stderr)
        fetched_pairs = [(url, source_content) for url in urls]
        snippet_results = process_all(fetched_pairs, SNIPPET_DIR)

    # 3. Infer article type
    print(f"\n[3/4] Inferring article type from intent…", file=sys.stderr)
    article_type = infer_article_type(args.intent, urls)

    # 4. Generate English outline
    print(f"\n[4/4] Generating English outline…", file=sys.stderr)
    outline = generate_outline(source_content, article_type, args.intent)

    # Build metadata (embedded in PR for Phase 2 to read)
    metadata = {
        "source_urls":   urls,
        "article_type":  article_type,
        "intent":        args.intent,
        "snippet_files": [r.filename for r in snippet_results],
    }

    # Write PR body file
    pr_body = build_pr_body(urls, snippet_results, article_type, args.intent, outline, metadata)
    Path(args.pr_body_file).write_text(pr_body)
    print(f"\n  PR body written → {args.pr_body_file}", file=sys.stderr)

    # Write snippet-commit flag for Actions to detect
    if snippet_results:
        Path("snippet_changes.txt").write_text(
            "\n".join(r.filename for r in snippet_results)
        )


# ── Phase 2 ───────────────────────────────────────────────────────────────────

def phase2(args):
    pr_body = Path(args.pr_body_file).read_text()
    outline, metadata = parse_pr_body(pr_body)

    urls         = metadata.get("source_urls", [])
    article_type = metadata.get("article_type", "analytical")
    intent       = metadata.get("intent", "")

    print(f"\n[1/2] Re-fetching source content for article generation…", file=sys.stderr)
    source_content, _ = fetch_all(urls)

    print(f"\n[2/2] Generating Chinese article ({article_type})…", file=sys.stderr)
    article = generate_article(outline, source_content, article_type, intent)

    save_article(article, article_type, urls, args.output_dir)


# ── Monthly recap (standalone) ────────────────────────────────────────────────

def monthly_recap(args):
    template = (SKILL_ROOT / "assets/templates/monthly-recap.md").read_text()
    style    = STYLE_BASE.read_text()

    snippets_path = SNIPPET_DIR
    prefix = args.month.replace("-", "")
    matched = sorted(snippets_path.glob(f"{prefix}*.md"))

    if not matched:
        sys.exit(f"No snippets found for {args.month} in {snippets_path}")

    print(f"  {len(matched)} snippets found for {args.month}", file=sys.stderr)

    snippet_contents = "\n\n---\n\n".join(
        f"### {f.stem}\n\n{f.read_text(errors='ignore')}" for f in matched
    )

    system = (
        f"You are a monthly recap writer. Write in Chinese (中文).\n\n"
        f"## Writing Style\n{style}\n\n"
        f"## Monthly Recap Template\n{template}"
    )
    user = (
        f"Generate the monthly recap for {args.month}.\n\n"
        f"Snippets ({len(matched)} total):\n\n{snippet_contents}"
    )

    article = llm.chat(system, user, max_tokens=8192)

    out = Path("output/monthly-recap")
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{args.month}.md"
    path.write_text(article)
    print(f"  saved → {path}", file=sys.stderr)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="mode", required=True)

    # phase1
    p1 = sub.add_parser("phase1")
    p1.add_argument("--urls",            required=True)
    p1.add_argument("--intent",          required=True)
    p1.add_argument("--generate-snippets", action="store_true")
    p1.add_argument("--pr-body-file",    default="pr_body.md")

    # phase2
    p2 = sub.add_parser("phase2")
    p2.add_argument("--pr-body-file",    required=True)
    p2.add_argument("--output-dir",      default=None)

    # monthly-recap
    pm = sub.add_parser("monthly-recap")
    pm.add_argument("--month",           required=True)

    args = parser.parse_args()

    if args.mode == "phase1":
        phase1(args)
    elif args.mode == "phase2":
        phase2(args)
    elif args.mode == "monthly-recap":
        monthly_recap(args)


if __name__ == "__main__":
    main()
