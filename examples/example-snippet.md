## Polkadot JAM Upgrade — Roadmap and Developer Impact

**id:** S-20260115-0042
**created:** 2026-01-15
**updated:** 2026-03-08

---

**sources:**

| # | title | url | author | date | note |
|---|-------|-----|--------|------|------|
| 1 | Join-Accumulate Machine: A New Direction | https://graypaper.com | Gavin Wood | 2026-01-15 | original whitepaper |
| 2 | JAM Implementer's Prize Announced | https://polkadot.com/blog/jam-prize | Web3 Foundation | 2026-03-08 | prize structure update |

---

**topic:**
- Polkadot core protocol
- JAM upgrade
- developer tooling

**tags:**
- JAM
- graypaper
- relay chain replacement
- coretime

---

## 一句话总结

JAM 是 Polkadot 对 Relay Chain 的根本性重构：用「积累-汇聚」计算模型替代现有的平行链插槽机制，目标是让任意计算（不限于区块链）都能在共享安全下运行。

## 核心要点

- JAM 不是「新链」，是现有 Relay Chain 的替代执行层，兼容 XCMP 和现有平行链
- 核心原语：Service（服务单元）、Work Package（工作包）、Accumulate + Refine 双阶段执行
- 开发语言：Rust（首选）+ 任何能编译到 PolkaVM / RISC-V 的语言
- Web3 Foundation 设置 1000 万美元实现者奖金，奖励非 Parity 团队的独立 JAM 实现
- 主网部署时间未定；2026 Q3 前至少需要 3 个独立客户端通过兼容性测试

## 关键引用

> "JAM is not a blockchain. It is a computation model that happens to have blockchain-like properties where useful." — Gavin Wood, GrayPaper v0.4

## 更新日志

- **2026-03-08** — Web3 Foundation 公布 JAM 实现者奖金细节：分 5 个里程碑，满分 10M USD；首个里程碑（状态机兼容）截止 2026-09-01
- **2026-01-15** — 初始创建，基于 GrayPaper 首版发布

## 适用场景

- 写「JAM 对开发者意味着什么」分析文章
- 月报中归纳 Polkadot 核心协议演进
- 向非技术读者解释 Polkadot 2.0 路线图

## 段落总结

JAM（Join-Accumulate Machine）是 Gavin Wood 提出的下一代 Polkadot 执行层，计划取代现有 Relay Chain。它将计算抽象为「服务」而非区块链，允许任意状态转换在 Polkadot 的共享安全下运行。Web3 Foundation 以 1000 万美元奖金激励多团队独立实现，以避免客户端单一化风险。
