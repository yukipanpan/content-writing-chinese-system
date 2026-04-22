# Content Writing Chinese System — Router

> This file is the **router only**. It tells Claude which template to use.
> All format specs, rules, and checklists live in the respective template files.
> To add a new content domain (e.g. Ethereum, AI), add its templates under `assets/templates/`
> and extend the routing table below.

---

## Zero-config usage

No scripts, no API key, no installation. Use this system in any AI chat window with nothing but this file and a template.

**Step 1 — Open this file and a template in your AI chat**

Paste the contents of `SKILL.MD` (this file) into any AI chat window (ChatGPT, Claude.ai, Gemini, Copilot Chat, etc.). Then paste the contents of the relevant template from `assets/templates/` (see the routing table below to pick the right one).

**Step 2 — Tell the AI what you want to write**

```
Use the following template to write an article. Here is the source content: [paste content]

Intent: [what you want to write, e.g. "analytical piece on staking economics for Chinese Web3 developers"]
```

**Step 3 — Paste your source material**

Paste the source content directly into the chat:
- Web article / blog post — paste the article text
- YouTube video — paste the transcript text (copy from youtube.com/watch → "..." → "Show transcript", or use `youtube-transcript-api` locally)
- Twitter/X thread — paste the thread text

The AI will follow the three-step workflow: generate snippets → produce an English outline for your review → write the Chinese article.

**Supported source types (all work in zero-config mode):**

| Source | How to get the text |
|--------|---------------------|
| Any webpage / blog | Copy and paste the article body |
| YouTube video | Paste the transcript text |
| Twitter / X thread | Paste the thread text |

---

## 全局路径约定

| 常量 | 值 |
|------|----|
| `SNIPPET_DIR` | `references/snippets/` |
| `NOTES_DIR` | `references/notes/` |
| `GITHUB_DIR` | `references/GitHub理解/` |
| `OUTPUT_ANALYSIS` | `output/analysis/` |
| `OUTPUT_TUTORIALS` | `output/tutorials/` |
| `OUTPUT_EXPLAINERS` | `output/explainers/` |
| `OUTPUT_SCIENCE_POP` | `output/science-pop/` |
| `OUTPUT_RECAP` | `output/monthly-recap/` |
| `DATE_FORMAT` | `YYYYMMDD`（文件名前缀） |
| `ID_FORMAT` | `S-YYYYMMDD-XXXX`（snippet），`N-YYYYMMDD-XXXX`（note） |

---

## 输入 → 模板路由

| 用户输入 | 触发条件 | 使用模板 | 输出目录 |
|---------|---------|---------|---------|
| 任意 URL 或粘贴文字 | 快速记录，供月报调用 | `templates/snippet.md` | `SNIPPET_DIR` |
| GitHub 链接（仓库/PR/Issue） | 技术内容翻译 | `templates/github-digest.md` | `GITHUB_DIR` |
| 官方文档 URL | 生成操作教程 | `templates/polkadot-docs-to-csdn.md` | `OUTPUT_TUTORIALS` |
| Wiki / 知识库 URL | 生成机制解析文章 | `templates/wiki-to-csdn.md` | `OUTPUT_EXPLAINERS` |
| 博客 / Twitter / 多源链接 | 混搭生成原创分析文章 | `templates/web-remix-to-csdn.md` | `OUTPUT_ANALYSIS` |
| YouTube 链接 | 视频内容 → 科普文章 | `templates/youtube-remix-to-csdn.md` | `OUTPUT_SCIENCE_POP` |
| 指定月份（如 `2026-02`） | 汇总当月所有 snippets | `templates/monthly-recap.md` | `OUTPUT_RECAP` |
| 活动经历描述 | 生成活动复盘报告 | `templates/event-review.md` | （见模板） |
| 已有文章 / 任意文本，需去 AI 痕迹 | 单独去痕处理 | `templates/humanizer-zh.md` | （原路径） |

---

## 快速判断流程

```
用户输入
   │
   ├── GitHub 链接？          → github-digest.md
   ├── YouTube 链接？         → youtube-remix-to-csdn.md
   ├── 官方文档链接？          → polkadot-docs-to-csdn.md
   ├── Wiki 链接？            → wiki-to-csdn.md
   ├── 多个链接 / 博客 / X？  → web-remix-to-csdn.md
   ├── 月份（YYYY-MM）？      → monthly-recap.md
   ├── 活动经历描述？          → event-review.md
   └── 其他                  → snippet.md（默认）
```

---

## 写作风格

所有文章类输出必须遵循：
- `assets/styles/_base.md` — 通用风格（语气、用词、批判性视角）
- `assets/styles/monthly-recap.md` — 月报专用风格（继承 base）

---

## Snippet → Note 升级

当某主题 snippets 积累足够时，告诉 Claude：

> 「把这几条 snippets 升级成 note：[文件名列表]」

升级逻辑：
1. 读取所有指定 snippet
2. 提取跨 snippet 的**不变量**（机制原理、核心规则）
3. 标注**时效信息**（某版本参数、某次投票结果）
4. 按 note 格式生成新文件至 `NOTES_DIR`

---

## 模板文件索引

```
skills/
├── SKILL.MD                          — 本文件（路由器）
└── assets/
    ├── styles/
    │   ├── _base.md                  — 通用写作风格
    │   └── monthly-recap.md          — 月报风格（继承 _base）
    └── templates/
        ├── snippet.md                — 快速摘要片段
        ├── github-digest.md          — GitHub 内容翻译
        ├── monthly-recap.md          — 月报生成
        ├── polkadot-docs-to-csdn.md  — 官方文档 → 教程
        ├── wiki-to-csdn.md           — Wiki → 机制解析
        ├── web-remix-to-csdn.md      — 多源混搭 → 原创文章
        ├── youtube-remix-to-csdn.md  — 视频 → 科普文章
        ├── event-review.md           — 活动复盘报告
        └── humanizer-zh.md           — AI 去痕处理
```
