# Example: Phase 1 Outline

> This is what appears in the PR description after Phase 1 runs.
> The editor reviews this, edits if needed, then comments `/generate`.

---

**Intent submitted:** `"analytical piece on JAM's timeline and what it means for Ethereum developers considering Polkadot"`

**Sources submitted:**
- `https://graypaper.com`
- `https://polkadot.com/blog/jam-prize`
- `https://x.com/gavofyork/status/1234567890`

---

**Working title:** JAM Is Not a Blockchain — And That's the Point

**Type:** analytical

**Thesis / angle:** Ethereum developers evaluating Polkadot are still thinking in terms of "chains" and "slots." JAM erases that mental model entirely: it's a shared computation substrate where the concept of a parachain becomes one possible service among many. This piece argues the migration path for EVM developers is more disruptive — and more interesting — than the marketing suggests.

**Sections:**
1. The problem JAM is solving — Why the relay chain / parachain slot model created artificial constraints, and what Gavin Wood identified as the fundamental bottleneck
2. What JAM actually is (not what the press release says) — The Refine / Accumulate execution model explained without jargon; how a "Service" differs from a smart contract or a parachain
3. The timeline that matters — Breaking down the implementer's prize milestones; why "3 independent clients by Q3 2026" is the real signal to watch, not any mainnet date
4. What this means if you're an Ethereum developer — Concrete changes: no more Solidity-first assumptions, RISC-V target, PolkaVM; the honest tradeoff vs. staying on L2s
5. The open question — Whether JAM's abstraction is a superpower or a coordination trap; historical analogies from WebAssembly adoption

**Key claims to make:**
- JAM's 10M implementer prize is a hedge against client monoculture, not a development bounty — the distinction matters for assessing Polkadot's decentralization trajectory
- EVM compatibility on JAM will exist but as a "service," not a native assumption — this is a bigger philosophical shift than the technical docs suggest
- The Q3 2026 milestone deadline is the earliest meaningful signal of JAM's viability; anything before that is vaporware risk

**Sources used:** graypaper.com, polkadot.com/blog/jam-prize, @gavofyork thread
**KB references:** `references/snippets/20260115-polkadot-jam-upgrade.md` (existing snippet on JAM basics)
