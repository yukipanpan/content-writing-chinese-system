# Example: Generated Chinese Article

> Output of Phase 2 — saved to `output/analysis/20260322-graypaper.md`
> Article type: **analytical** | Source: graypaper.com + jam-prize announcement

---

# JAM 不是区块链——这才是重点

如果你是一个 Ethereum 开发者，正在重新评估 Polkadot 的价值，你大概率还在用「链」「插槽」「平行链」这套词汇思考问题。这很正常，因为 Polkadot 过去五年的营销材料就是这么写的。

但 JAM 发布之后，这套词汇就过时了。

Gavin Wood 在 GrayPaper 里说得很直接：「JAM 不是区块链，它是一个碰巧具有类区块链属性的计算模型。」这句话不是在玩文字游戏。它意味着，Polkadot 下一代执行层的设计前提，是把「区块链」这个概念当作一种特殊情况来处理——而不是作为基础假设。

对于从 Ethereum 生态迁移过来的开发者，这个转变比技术文档暗示的要大得多。

---

## Relay Chain 的真正瓶颈

Polkadot 当前架构的问题，不是性能，不是费用，而是**抽象层的粒度太粗**。

平行链插槽模型把「一条完整的链」作为最小可租用的安全单元。这意味着，如果你只想运行一个状态机、一个 rollup 的结算层、或者一个定制的 ZK 验证电路，你仍然需要打包成一条完整的平行链——带着它的出块逻辑、collator 网络和所有开销。

JAM 的 Refine / Accumulate 执行模型切掉了这一层。它把计算单元定义为「服务」（Service）和「工作包」（Work Package）。服务是一段无状态的 RISC-V 代码；工作包是输入数据。Refine 阶段在去中心化的工作节点上并行执行，Accumulate 阶段在链上聚合结果。

你不再需要「一条链」。你需要的是一段代码和一批输入。

---

## 实现者奖金的真实含义

Web3 Foundation 宣布的 1000 万美元 JAM 实现者奖金，媒体普遍把它报道成「开发激励」。这个理解有偏差。

奖金的结构分 5 个里程碑，要求参赛团队独立实现完整的 JAM 状态机，并通过与 Parity 参考实现的兼容性测试。关键条件是：**奖金只颁给非 Parity 团队**。

这是一个对冲客户端单一化风险的机制，不是在给 JAM 开发提速。Polkadot 目前 85% 以上的验证节点跑的是 Parity 的 Substrate 客户端。如果 JAM 主网上线时仍然只有一个客户端，Polkadot 宣称的去中心化就是个叙事问题。

所以，Q3 2026 的里程碑截止日期是真正值得追踪的信号——不是「JAM 什么时候上线」，而是「届时有几个独立客户端通过了兼容性测试」。

---

## 对 Ethereum 开发者的诚实评估

JAM 会支持 EVM。但它会以「服务」的形式支持——EVM 执行环境是 JAM 上可以部署的一个服务，而不是内置假设。

这意味着什么？你的 Solidity 合约不会消失，但它们运行的执行层不再是一等公民。PolkaVM（基于 RISC-V）才是 JAM 的原生目标。用 Rust 写的服务在性能和安全模型上都有结构性优势。

长期来看，如果 JAM 按预期演化，以太坊生态的「EVM 优先」假设在 Polkadot 上会逐渐成为一种历史包袱，而不是竞争优势。

这个判断不是在唱衰 EVM 开发者。而是在说：**迁移成本比营销材料里写的要高，也比它值得的要值得**。

---

## 开放性问题

JAM 把计算抽象得足够底层，以至于几乎任何东西都可以在上面运行。这在理论上是一种超能力。

但 WebAssembly 的历史告诉我们，「任何东西都能跑」的抽象层往往面临一个协调陷阱：工具链、开发者习惯和生态工具需要很长时间才能追上底层能力。WASM 在 2019 年就达到了技术成熟度，但到 2024 年它在 web 开发者中的实际渗透率仍然有限。

JAM 的 Q3 2026 里程碑将回答第一个问题：协议能否实现。但第二个问题——**开发者生态愿不愿意迁移**——可能需要更长时间来验证。

---

**参考资料**
- GrayPaper v0.4 — https://graypaper.com
- JAM Implementer's Prize — https://polkadot.com/blog/jam-prize
- @gavofyork 原文线程 — https://x.com/gavofyork/status/1234567890
