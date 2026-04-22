# Content Writing System

Turn any English source into a polished Chinese article — with any AI, no API key required to get started.

A structured three-step workflow: feed sources (web pages, YouTube videos, Twitter/X threads) → review an English outline → generate the Chinese article. Works with Claude Code, Cursor, Copilot, ChatGPT, or any AI chat interface. Scripts and GitHub Actions are optional automation layers on top of the same templates.

---

## The workflow

```
Step 1 — Feed sources          Step 2 — Review outline     Step 3 — Generate article
──────────────────────────     ─────────────────────────   ──────────────────────────
URLs or pasted text            English outline appears     Approve → Chinese article
  → fetch content              ← edit angle / sections     saved to output/
  → save snippets to KB        ← adjust thesis
  → infer article type
  → draft English outline
```

The same three steps run whether you are pasting text into ChatGPT, running `/phase1` in Claude Code, executing a CLI command, or triggering a GitHub Actions workflow.

---

## Supported sources

| Source | What you get | Local | GitHub Actions CI |
|--------|-------------|-------|-------------------|
| Any webpage / blog | Full article body via BeautifulSoup | Yes | Yes |
| YouTube video | Full transcript via youtube-transcript-api | Yes | Blocked by YouTube |
| Twitter / X thread | Full post content via ADHX API (no key needed) | Yes | Blocked by platform DNS |

**YouTube and Twitter/X are first-class sources.** They work in every local environment. GitHub Actions CI runners are blocked by both platforms — this is a platform-level restriction, not a missing feature. Use Layer 2 CLI scripts or Layer 1 coding AI for these sources.

---

## Example outputs

### Snippet — a source record saved to the knowledge base

Snippets are the building blocks of the knowledge base. Each one captures a source, its key claims, and a one-liner summary — structured so Claude can reference them later when writing articles or monthly recaps.

```markdown
## Polkadot JAM Upgrade — Roadmap and Developer Impact

**id:** S-20260115-0042  |  **created:** 2026-01-15  |  **updated:** 2026-03-08

## 一句话总结
JAM 是 Polkadot 对 Relay Chain 的根本性重构：用「积累-汇聚」计算模型替代现有的
平行链插槽机制，目标是让任意计算（不限于区块链）都能在共享安全下运行。

## 核心要点
- JAM 不是「新链」，是现有 Relay Chain 的替代执行层，兼容 XCMP 和现有平行链
- 核心原语：Service（服务单元）、Work Package（工作包）、Accumulate + Refine 双阶段执行
- Web3 Foundation 设置 1000 万美元实现者奖金，奖励非 Parity 团队的独立 JAM 实现
- 主网部署时间未定；2026 Q3 前至少需要 3 个独立客户端通过兼容性测试
```

→ [Full snippet example](examples/example-snippet.md)

---

### Outline — what appears for review after Step 1

The outline is in English so anyone on the team can read and edit it before the Chinese article is written.

```
**Working title:** JAM Is Not a Blockchain — And That's the Point

**Type:** analytical

**Thesis / angle:** Ethereum developers evaluating Polkadot are still thinking in terms
of "chains" and "slots." JAM erases that mental model entirely: it's a shared computation
substrate where the concept of a parachain becomes one possible service among many.

**Sections:**
1. The problem JAM is solving — Why the relay chain model created artificial constraints
2. What JAM actually is — The Refine / Accumulate model explained without jargon
3. The timeline that matters — Why the Q3 2026 client milestone is the real signal
4. What this means for Ethereum developers — Honest tradeoffs vs. staying on L2s
5. The open question — Whether JAM's abstraction is a superpower or a coordination trap

**Key claims to make:**
- JAM's 10M prize is a hedge against client monoculture, not a development bounty
- EVM on JAM will exist as a "service," not a native assumption — bigger shift than docs suggest
- Q3 2026 milestone is the earliest meaningful signal; anything before is vaporware risk
```

→ [Full outline example](examples/example-outline.md)

---

### Article — the Chinese output (Step 3)

Saved to `output/analysis/`. Written in the voice of a cold, critical analyst — not marketing copy.

```markdown
# JAM 不是区块链——这才是重点

如果你是一个 Ethereum 开发者，正在重新评估 Polkadot 的价值，你大概率还在用
「链」「插槽」「平行链」这套词汇思考问题。这很正常，因为 Polkadot 过去五年的
营销材料就是这么写的。

但 JAM 发布之后，这套词汇就过时了。

Gavin Wood 在 GrayPaper 里说得很直接：「JAM 不是区块链，它是一个碰巧具有类区块链
属性的计算模型。」这句话不是在玩文字游戏。它意味着，Polkadot 下一代执行层的设计
前提，是把「区块链」这个概念当作一种特殊情况——而不是基础假设。

对于从 Ethereum 生态迁移过来的开发者，这个转变比技术文档暗示的要大得多。
…
```

→ [Full article example](examples/example-article.md)

---

## Getting started

### Fastest path — no setup required

1. Clone the repo (or just download `skills/SKILL.MD` and the template files)
2. Open `skills/SKILL.MD` in any AI chat window (ChatGPT, Claude.ai, Gemini, etc.)
3. Paste your source content and describe what you want to write
4. The AI routes to the right template and runs the three-step workflow

**No API key needed. No installation needed.** The templates are the product.

For YouTube videos: paste the transcript text directly. For Twitter/X threads: paste the thread text directly. Or use Layer 2 scripts to fetch these automatically.

---

### Layer 0 — Templates only (any AI, zero config)

Open `skills/SKILL.MD` in any AI assistant alongside the relevant template file from `skills/assets/templates/`. Tell the AI your source content and intent. It handles the rest.

This works in ChatGPT, Claude.ai, Gemini, Copilot Chat, or any other AI chat interface — no coding environment required.

See `skills/SKILL.MD` for the zero-config usage guide and routing table.

---

### Layer 1 — With a coding AI (Claude Code, Cursor, Copilot)

```bash
git clone https://github.com/yourorg/content-writing-chinese-system.git
cd content-writing-chinese-system
```

Open the repo in your coding AI. `CLAUDE.md` is auto-loaded by Claude Code; Cursor and Copilot read it as project context too.

Use slash commands (Claude Code):

```
/phase1 https://example.com/article analytical piece on staking economics
/generate
/monthly-recap 2026-04
```

Or just describe what you want in natural language — the AI reads `CLAUDE.md` and knows the workflow.

---

### Layer 2 — With automation scripts

Install dependencies and configure your LLM provider:

```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env: set LLM_PROVIDER and your API key
```

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `anthropic` | Choose: `anthropic` \| `openai` \| `ollama` |
| `ANTHROPIC_API_KEY` | — | Required for Anthropic |
| `ANTHROPIC_MODEL` | `claude-haiku-4-5-20251001` | Optional model override |
| `OPENAI_API_KEY` | — | Required for OpenAI |
| `OPENAI_MODEL` | `gpt-4o-mini` | Optional model override |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama endpoint |
| `OLLAMA_MODEL` | `llama3` | Ollama model name |

Run the pipeline:

```bash
# Phase 1: fetch sources, generate snippets, produce English outline
python3 scripts/run_skill.py phase1 \
  --urls "https://example.com/post, https://youtu.be/xyz" \
  --intent "analytical piece on staking economics" \
  --generate-snippets \
  --pr-body-file pr_body.md

# Review pr_body.md, edit the outline section, then:

# Phase 2: generate Chinese article from the approved outline
python3 scripts/run_skill.py phase2 \
  --pr-body-file pr_body.md

# Monthly recap: summarise all snippets from a given month
python3 scripts/run_skill.py monthly-recap --month 2026-04
```

Layer 2 enables: automatic YouTube transcript extraction, automatic Twitter/X fetching (ADHX API, no key needed), and snippet knowledge base management with deduplication.

---

### Layer 3 — GitHub Actions (team async workflow)

Go to **Actions → Generate Content (Phase 1 — Outline) → Run workflow**:

| Field | What to enter |
|-------|--------------|
| `source_urls` | One or more URLs, one per line or comma-separated. Web pages and blog posts work in CI. YouTube and Twitter/X must be run locally. |
| `intent` | What you want to write — free text. |
| `generate_snippets` | `yes` to save sources into the knowledge base. |

A pull request opens with the English outline in the description. Review it, edit if needed, then comment `/generate` on the PR. The Chinese article is committed to the PR branch.

**CI limitation:** GitHub Actions runners cannot reach YouTube or Twitter/X. Use Layer 1 or Layer 2 for those sources, then paste the extracted content into the workflow.

For GitHub Actions setup, add your API key to **Settings → Secrets and variables → Actions**:
- `ANTHROPIC_API_KEY` (or your chosen provider's key)
- `LLM_PROVIDER` as a variable (optional, defaults to `anthropic`)

---

## Article types

The system infers the article type automatically from your intent and URLs:

| Type | Template used | Output folder |
|------|--------------|---------------|
| Analytical / opinion | `web-remix-to-csdn.md` | `output/analysis/` |
| Tutorial (from docs) | `polkadot-docs-to-csdn.md` | `output/tutorials/` |
| Concept explainer (from wiki) | `wiki-to-csdn.md` | `output/explainers/` |
| Pop-science (from YouTube) | `youtube-remix-to-csdn.md` | `output/science-pop/` |
| Monthly recap | `monthly-recap.md` | `output/monthly-recap/` |

---

## Knowledge base (snippets)

Every time you run Phase 1 with `--generate-snippets`, the fetched sources are saved as structured snippet files in `references/snippets/`. Each snippet records the source URL, key claims, and a one-line Chinese summary.

Snippets accumulate over time and are deduplicated automatically — if you fetch the same URL twice, the existing snippet is updated rather than duplicated.

The monthly recap command reads all snippets from a given month and synthesises them into a single Chinese recap article. This is the primary way the knowledge base gets consumed.

---

## Repository layout

```
.
├── skills/                         ← Templates and routing (the core product)
│   ├── SKILL.MD                    ← Router: which template to use when; zero-config guide
│   └── assets/
│       ├── styles/                 ← Writing style guides
│       │   ├── _base.md            ← Base style (voice, tone, critical perspective)
│       │   └── monthly-recap.md    ← Monthly recap style (extends _base)
│       └── templates/              ← One file per article type
│           ├── snippet.md
│           ├── web-remix-to-csdn.md
│           ├── youtube-remix-to-csdn.md
│           ├── polkadot-docs-to-csdn.md
│           ├── wiki-to-csdn.md
│           ├── monthly-recap.md
│           ├── github-digest.md
│           ├── event-review.md
│           └── humanizer-zh.md
├── scripts/                        ← Optional automation layer
│   ├── run_skill.py                ← Main orchestrator (phase1 / phase2 / monthly-recap)
│   ├── fetcher.py                  ← URL fetching: web / YouTube / Twitter/X
│   ├── llm.py                      ← Provider-agnostic LLM client
│   └── snippets.py                 ← Snippet generation, dedup, update
├── .github/workflows/              ← GitHub Actions (Layer 3)
│   ├── generate.yml
│   ├── on-generate-comment.yml
│   └── generate-monthly-recap.yml
├── .claude/commands/               ← Claude Code slash commands (Layer 1)
│   ├── phase1.md
│   ├── generate.md
│   └── monthly-recap.md
├── references/
│   └── snippets/                   ← Accumulated source records (knowledge base)
├── output/
│   ├── analysis/
│   ├── tutorials/
│   ├── explainers/
│   ├── science-pop/
│   └── monthly-recap/
├── examples/                       ← Sample outputs
│   ├── example-snippet.md
│   ├── example-outline.md
│   └── example-article.md
├── CLAUDE.md                       ← AI assistant project guide (auto-read by Claude Code)
├── .env.example
└── requirements.txt
```
