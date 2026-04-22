# Content Writing Chinese System — Project Guide

A structured workflow for writing high-quality Chinese articles from English sources. The core product is a set of prompt templates in `skills/assets/templates/`. The scripts are optional automation. Any AI assistant can use this system by reading `skills/SKILL.MD` and the relevant template.

Works with Claude Code, Cursor, Copilot, ChatGPT, or any AI. No API key required for the template-only (Layer 0) path.

---

## Three-step workflow

```
Step 1 — Feed sources          Step 2 — Review outline     Step 3 — Generate article
──────────────────────────     ─────────────────────────   ──────────────────────────
URLs or pasted text            English outline in           Approve → Chinese article
  → fetch content              pr_body.md                   saved to output/
  → save snippets to KB        ← edit angle / sections
  → infer article type         ← adjust thesis
  → draft English outline
```

The three steps map to these commands:
- Step 1: `/phase1` or `python3 scripts/run_skill.py phase1 ...`
- Step 3: `/generate` or `python3 scripts/run_skill.py phase2 ...`
- Monthly: `/monthly-recap` or `python3 scripts/run_skill.py monthly-recap ...`

---

## Directory structure

```
skills/
  SKILL.MD                    Router: which template to use, zero-config usage guide
  assets/styles/_base.md      Base writing style (voice, tone, critical perspective)
  assets/styles/monthly-recap.md
  assets/templates/           One template file per article type

scripts/
  run_skill.py                Main orchestrator — entry point for all CLI commands
  fetcher.py                  URL content extraction: web / YouTube / Twitter/X
  llm.py                      Provider-agnostic LLM client (Anthropic / OpenAI / Ollama)
  snippets.py                 Snippet generation, deduplication, update

references/snippets/          Knowledge base — accumulated source records
output/                       Generated articles (analysis/, tutorials/, etc.)
examples/                     Sample snippet, outline, and article files
.claude/commands/             Claude Code custom slash commands
```

---

## Source routing

The system infers the right template from the URL type and intent. When routing manually, follow this table:

| Input | Template | Output folder |
|-------|----------|---------------|
| Any webpage / blog | `web-remix-to-csdn.md` | `output/analysis/` |
| YouTube link | `youtube-remix-to-csdn.md` | `output/science-pop/` |
| Twitter/X thread | `web-remix-to-csdn.md` | `output/analysis/` |
| Official docs URL | `polkadot-docs-to-csdn.md` | `output/tutorials/` |
| Wiki / knowledge base | `wiki-to-csdn.md` | `output/explainers/` |
| GitHub repo/PR/issue | `github-digest.md` | `references/GitHub理解/` |
| Month (YYYY-MM) | `monthly-recap.md` | `output/monthly-recap/` |
| Event experience | `event-review.md` | (see template) |
| Existing text, remove AI traces | `humanizer-zh.md` | (original path) |
| Any source, quick record | `snippet.md` | `references/snippets/` |

See `skills/SKILL.MD` for the full routing decision tree.

---

## Supported source types

| Source | Extraction method | Works locally | Works in GitHub Actions CI |
|--------|------------------|---------------|---------------------------|
| Any webpage / blog | requests + BeautifulSoup | Yes | Yes |
| YouTube video | youtube-transcript-api | Yes | No — blocked by YouTube |
| Twitter / X thread | ADHX API (no key required) | Yes | No — blocked by platform DNS |

For YouTube and Twitter/X in a CI context: run the fetch locally with Layer 2 scripts, then paste the extracted content into the workflow.

---

## Running the scripts

Requires: `pip install -r requirements.txt` and a `.env` file with `LLM_PROVIDER` + API key.

```bash
# Phase 1: fetch sources, generate snippets, produce English outline
python3 scripts/run_skill.py phase1 \
  --urls "https://example.com/post, https://youtu.be/VIDEO_ID" \
  --intent "analytical piece on staking economics for Chinese Web3 developers" \
  --generate-snippets \
  --pr-body-file pr_body.md

# Phase 2: generate Chinese article from the outline in pr_body.md
python3 scripts/run_skill.py phase2 \
  --pr-body-file pr_body.md

# Monthly recap: synthesise all snippets from a given month
python3 scripts/run_skill.py monthly-recap --month 2026-04
```

LLM provider config via `.env`:

| Variable | Default | Notes |
|----------|---------|-------|
| `LLM_PROVIDER` | `anthropic` | `anthropic` \| `openai` \| `ollama` |
| `ANTHROPIC_API_KEY` | — | Required for Anthropic |
| `OPENAI_API_KEY` | — | Required for OpenAI |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Local Ollama only |

---

## Knowledge base: how snippets work

Each call to Phase 1 with `--generate-snippets` saves one snippet file per source URL into `references/snippets/`. A snippet records:
- Source URL and title
- Key claims extracted from the content
- A one-line Chinese summary

Snippet IDs use the format `S-YYYYMMDD-XXXX`. If the same URL is fetched again, the existing snippet is updated (not duplicated). The monthly recap command reads all snippets from `references/snippets/` for the target month and synthesises them into a single recap article.

---

## Writing style

All article output must follow `skills/assets/styles/_base.md`. Key points:
- Voice: cold, critical analyst — not marketing copy
- Perspective: Chinese Web3 developer audience
- No filler phrases, no hype language
- Monthly recap additionally follows `skills/assets/styles/monthly-recap.md`

When generating articles, read the style file before writing.
