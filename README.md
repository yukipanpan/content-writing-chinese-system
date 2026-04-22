# Content Writing Chinese System

A two-phase content pipeline for writing high-quality Chinese articles from English sources.

Capture sources → review an English outline → generate a Chinese article for CSDN, WeChat, and monthly recaps.

Works with **Anthropic**, **OpenAI**, or **Ollama** (local). Runs via GitHub Actions, CLI, or as a Python library.

---

## How it works

```
Phase 1                          Review              Phase 2
──────────────────────────────   ──────────────────  ─────────────────────
URLs + intent                    PR opens with       Comment /generate
  → fetch web/YouTube/Twitter    English outline       → Chinese article
  → generate snippets (KB)       ← edit if needed      → committed to PR
  → infer article type
  → English outline
```

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

### Outline — what the PR shows for review (Phase 1 output)

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

### Article — the Chinese output (Phase 2)

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

## Usage

### Option A — GitHub Actions (recommended for teams)

**Step 1 — Submit sources**

> **Actions → Generate Content (Phase 1 — Outline) → Run workflow**

| Field | What to enter |
|-------|--------------|
| `source_urls` | One or more URLs. One per line or comma-separated. |
| `intent` | What you want to write — free text (see examples below). |
| `generate_snippets` | `yes` to save sources into the knowledge base. |

**Intent examples:**
```
"analytical piece on JAM's timeline and what it means for Ethereum developers"
"tutorial on how to set up an RPC node from the official docs"
"summarise this YouTube talk for a Chinese Web3 audience"
"explain the new staking changes to a non-technical reader"
```

A pull request opens with the English outline in the description.

**Step 2 — Review the outline**

Read the PR description. Edit it directly if you want to change the angle or sections. When satisfied, comment `/generate` on the PR.

The Chinese article is committed to the PR branch. Merge when ready.

---

### Option B — CLI

```bash
# Phase 1: fetch sources, generate outline
python3 scripts/run_skill.py phase1 \
  --urls "https://example.com/post, https://youtu.be/xyz" \
  --intent "analytical piece on staking economics" \
  --generate-snippets \
  --pr-body-file pr_body.md

# Review pr_body.md, edit the outline section, then:

# Phase 2: generate Chinese article from approved outline
python3 scripts/run_skill.py phase2 \
  --pr-body-file pr_body.md

# Monthly recap
python3 scripts/run_skill.py monthly-recap --month 2026-04
```

---

### Option C — Monthly recap (automated)

> **Actions → Generate Monthly Recap → Run workflow**

| Field | What to enter |
|-------|--------------|
| `month` | Format: `YYYY-MM` (e.g. `2026-04`) |

Also runs automatically on the 1st of every month.

---

## Article types

The system infers the type automatically from your intent and URLs:

| Type | Template used | Output folder |
|------|--------------|---------------|
| Analytical / opinion | `web-remix-to-csdn.md` | `output/analysis/` |
| Tutorial (from docs) | `polkadot-docs-to-csdn.md` | `output/tutorials/` |
| Concept explainer (from wiki) | `wiki-to-csdn.md` | `output/explainers/` |
| Pop-science (from YouTube) | `youtube-remix-to-csdn.md` | `output/science-pop/` |
| Monthly recap | `monthly-recap.md` | `output/monthly-recap/` |

---

## Setup

### 1. Fork or clone

```bash
git clone https://github.com/yourorg/content-writing-chinese-system.git
cd content-writing-chinese-system
pip install -r requirements.txt
```

### 2. Configure your LLM provider

Copy `.env.example` to `.env` and fill in your key:

```bash
cp .env.example .env
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

### 3. For GitHub Actions

Go to **Settings → Secrets and variables → Actions** and add:

- `ANTHROPIC_API_KEY` (or your chosen provider's key)
- `LLM_PROVIDER` (as a variable, not secret) — optional, defaults to `anthropic`

---

## Repository structure

```
.
├── skills/                         ← Prompt templates (the core logic)
│   ├── SKILL.MD                    ← Router: which template to use when
│   └── assets/
│       ├── styles/                 ← Writing style guides
│       └── templates/              ← One file per article type
├── scripts/
│   ├── llm.py                      ← Provider-agnostic LLM client
│   ├── fetcher.py                  ← URL content extraction (web/YouTube/Twitter)
│   ├── snippets.py                 ← Snippet generation, deduplication, update
│   └── run_skill.py                ← Main orchestrator (phase1 / phase2 / monthly-recap)
├── .github/workflows/
│   ├── generate.yml                ← Phase 1: fetch + snippets + outline → PR
│   ├── on-generate-comment.yml     ← Phase 2: /generate comment → Chinese article
│   └── generate-monthly-recap.yml  ← Manual + scheduled monthly recap
├── references/
│   └── snippets/                   ← Accumulated source records (knowledge base)
├── output/
│   ├── analysis/
│   ├── tutorials/
│   ├── explainers/
│   ├── science-pop/
│   └── monthly-recap/
├── .env.example
└── requirements.txt
```

---

## Supported URL types

| Source | How content is extracted |
|--------|--------------------------|
| Any webpage / blog | `requests` + `BeautifulSoup` |
| YouTube | `youtube-transcript-api` (transcript text) |
| Twitter / X | ADHX API (full thread content) |

---

## Output language

Articles are always written in **Chinese (中文)**.
PR descriptions, outlines, and status messages are always in **English**.
