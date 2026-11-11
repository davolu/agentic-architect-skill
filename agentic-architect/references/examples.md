# Example architectures

Worked examples produced by running this skill's own process. Full specs are in `examples/` (`*.json` for the generator, `*.mmd` Mermaid fallback). Use them as a quality bar, not as templates to copy blindly.

## 1. Customer support agent with human-approved refunds

**Prompt:** "Build a support agent that answers order questions from our policy docs and can issue refunds, but a person must approve every refund."

**Key decisions**
- Hybrid workflow, not a free agent: money moves only through code (D1, D2; Ch24).
- One agent; no multi-agent split (D4; Ch31).
- Intent classifier returns a typed route; reply drafter cites policy IDs or abstains (Ch8, Ch17).
- Refund path: triage, refund policy gate (deny by default), checkpoint and durable interrupt, human approves the exact refund (single-use, expiring), Refund MCP with idempotency key, ledger (Ch23, Ch48, Ch49, Ch53).
- Orders MCP is read-only; the refund tool is a separate write scope (Ch11).
- No long-term memory in v1 (Ch18).
- Evals: golden set incl. ineligible, over-limit and injected-email cases; zero-tolerance safety gate (Ch42, Ch45).

**Layers:** Users and channels / Edge and input guard / Orchestration / Policy and human approval / Tools via MCP / Data, state and knowledge / Observability and evals. Trust boundaries below the channel lane and below the approval lane.

## 2. Multi-source research agent

**Prompt:** "A research agent that answers a question using the web, our internal docs, academic papers and our analytics database, with citations."

**Key decisions**
- Orchestrator-workers justified by parallelism and context isolation over four independent sources (D4; Ch31, Ch32).
- Plan-execute with a code plan checker at the top; ReAct inside each worker with a step cap (D3; Ch13).
- All tools read-only; web and paper content labelled untrusted (Ch47).
- Coordinator merges artifacts by stable source ID into an evidence store; every source stored once (Ch15, Ch33).
- Synthesizer cites source IDs; claim verifier is the only path to "verified"; unsupported claims go to human review (Ch15, Ch44).
- No A2A: workers are in-process (Ch34, Ch62).
- Evals: golden questions with expected source IDs, unanswerable cases, replay without model calls (Ch15, Ch42).

**Layers:** User / Edge and brief / Planning / Coordination / Source workers / Sources via MCP / Synthesis and verification / Review and delivery / Observability and evals.

## 3. Sketch: coding agent from issue to PR (no full spec)

- Bounded agent in a sandbox: reproduce, map, search, plan, patch, test, review (Ch38).
- Model writes only the patch for named files; it cannot edit tests or run arbitrary commands (Ch38, Ch39).
- Allowlisted commands as argument lists, empty environment, scoped temp dir, time limits, egress rules (Ch39).
- Verification by an independent test run plus diff review; merge requires human approval (Ch38, Ch49).
- Trace and replay every run; golden set of past issues (Ch40, Ch42).
