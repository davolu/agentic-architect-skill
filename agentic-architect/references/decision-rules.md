# Decision rules

Apply these in order. Each rule gives a default, the conditions that change it, and the chapter of the A-Z of Agentic AI course it comes from. Record every decision in the spec's `rationale` list as "Choice: reason (ChN)". When the user pushes back, explain the trade-off in the chapter's terms, then do what they decide and log the residual risk.

## D1. How much autonomy? (Ch1, Ch3, Ch24)

Autonomy is a dial. Choose the **least autonomy that reliably solves the problem**.

| Level | Who chooses the next step | Use when |
|---|---|---|
| 0. Single call | nobody, one prompt | classification, extraction, rewriting |
| 1. Workflow | code, fixed path | the steps are known in advance |
| 2. Hybrid | code routes; model fills slots, classifies, drafts | known process, messy language input (the most common right answer) |
| 3. Bounded agent | model picks tools in a loop, code enforces budgets and gates | the path depends on what it finds (research, debugging, triage) |
| 4. Autonomous with approvals | agent acts, humans approve exact consequential actions | real side effects with clear policy |

Rules:
- Decide autonomy **per decision**, not per system. Ask "who chooses this next step?" for each one (Ch24).
- Reversible decisions can be model-chosen; **irreversible commitments belong behind deterministic code** (Ch24).
- If the user cannot write down what "done" means, step back and write the task spec first (Ch7).

## D2. Workflow or agent? (Ch24, Ch21, Ch22)

- Default to a **workflow or hybrid** when steps are enumerable. Use an agent loop only where the path genuinely depends on observations.
- Router, orchestrator-workers and evaluator-optimizer are partial-autonomy patterns; prefer them to a free agent (Ch24).
- Every gate needs a named safe outcome: clarify, deny, escalate or stop (Ch24).
- Framework: plain Python for short, stateless flows. Use a graph framework (for example LangGraph) when you need durable state, interrupts or replayable paths. Keep business logic in plain functions that know nothing about the orchestrator, to avoid lock-in (Ch21, Ch22).

## D3. Which reasoning pattern? (Ch12, Ch13)

| Pattern | Pick when | Cost |
|---|---|---|
| Plain loop (decide, dispatch, observe, stop) | few tools, short tasks | lowest |
| ReAct | path depends on observations; you need an auditable action trace | medium |
| Plan-execute | many steps, coverage matters, plan should be checkable before spending | +1 model call; plan checked in code |
| Reflection or verifier gate | output quality or correctness is checkable | revise only when a check fails |

- Use the simplest pattern that handles the task's uncertainty and risk; measure the overhead (Ch13).
- Prefer **deterministic verifiers** (recomputed numbers, citation checks, schema checks) over model critics (Ch13).
- Common good combo: plan-execute at the top, ReAct inside bounded steps, a verifier before delivery.

## D4. One agent or many? (Ch31, Ch32, Ch33, Ch34)

Default: **one agent**. Split only for a named, measured reason:
- context isolation (sub-tasks would pollute each other's context),
- genuine specialization (different tools, prompts or permissions),
- parallelism over independent work,
- real ownership boundaries between teams.

Every boundary adds model calls, latency, state and observability work; reliability multiplies down across links (Ch31). If you split:
- **Supervisor or coordinator** centralizes validation and accountability; prefer it to peer handoffs or swarms (Ch32).
- Every handoff has an owner, a trace and a hop budget enforced in code (Ch32).
- Typed message contracts; reject malformed messages; one writer per piece of data; merge by a stable key, never by completion order (Ch33).
- **A2A** only when agents are separately owned, remote and opaque. In-process workers do not need a protocol (Ch34, Ch62).

## D5. Tools and integrations (Ch11, Ch26-Ch30)

- Tools are **narrow, typed, well-erroring and permission-limited**; read and write are separate tools (Ch4, Ch11).
- One result envelope: `ok` with `data`, or `ok: false` with a stable error code. Unknown tool names and bad arguments come back as observations, not crashes (Ch11).
- Make unsafe behaviour unrepresentable (no `eval`, no generic "run command" tool) (Ch11, Ch12).
- **MCP** when a capability should be reusable across hosts or teams, or you are consuming existing servers. stdio for one local tool, Streamable HTTP with OAuth for remote ones (Ch26, Ch28).
- MCP standardizes the conversation, not authority: a caller-side allowlist that fails closed, checked right before dispatch, plus server-side value validation (Ch29, Ch30, Ch66).
- Never pass a received token through to a downstream service; audience-bound, scoped, short-lived tokens (Ch28).
- Bound and truncate tool results; label remote content untrusted (Ch29).

## D6. Knowledge: RAG, and how (Ch16, Ch17, Ch20)

Use RAG when answers must come from documents that change or are private. Then:
- Chunks carry source ID, version and offsets; updates replace a source's chunks (Ch16).
- **Hybrid retrieval** (semantic plus keyword, fused by rank) with **metadata filters** for permission and currency (Ch17).
- Grounded generation cites source IDs and has a detectable **abstention**; a similarity floor decides abstain (Ch17, Ch20).
- Measure retrieval separately from generation (Ch17).
Do not use RAG for facts that belong in a database query or a tool call.

## D7. Memory and state (Ch18, Ch19, Ch23)

Keep three things separate: **conversation state**, **durable workflow state (checkpoints)** and **long-term memory** (Ch19).
- Memory types: working (this task), episodic (dated summaries), semantic (approved durable facts), procedural (know-how) (Ch18).
- Default for v1: **no long-term memory** unless a requirement needs it. If needed: owner-scoped, provenance and date on every fact, promotion only through validation, designed forgetting and deletion (Ch18, Ch19).
- Memory may change presentation, never permissions (Ch61, Ch63).
- Long-running or approval-gated work needs **checkpoints** keyed by thread ID, saved after each completed transition, resumable without repeating finished steps (Ch19, Ch23).

## D8. Guardrails (Ch46-Ch48)

- Threat-model first: assets, actors, trust boundaries, abuse cases (Ch46).
- Layer controls at the **model, tool and environment** boundaries so each decides independently (Ch48).
- Typed action proposals checked by deterministic policy that **denies by default**; errors and timeouts never count as success (Ch48).
- Untrusted content (user text, retrieved docs, web pages, emails, tool output) is data, never instructions; the agent must not have both a sensitive data source and an exfiltration route without a gate in between (Ch47).
See security-guardrails.md for the full checklist.

## D9. Human in the loop (Ch49, Ch23, Ch56)

- Put the human decision **at the boundary where state changes**; keep preparation read-only and automatic (Ch49).
- Approve **exact actions**, not the agent: one tool, one target, one parameter set; perishable and single-use (Ch49).
- Timeouts, absent reviewers and failed step-up checks fail toward read-only or escalation (Ch49).
- Implement as a durable interrupt: checkpoint before the pause, re-check authorization at execution (Ch23, Ch62).
- Rollout order for consequential domains: read-only, then drafts, then bounded writes with approval (Ch56).
Always require approval for: moving money, deleting data, sending external messages, changing permissions, merging or deploying code, unless the user explicitly accepts the risk in writing.

## D10. Reliability and side effects (Ch14, Ch53)

- Timeout on every tool call; classify errors transient or permanent; retry only transient, bounded, with backoff; circuit breaker for a down dependency (Ch14, Ch53).
- **Idempotency keys** from business facts on every side-effecting write; after a lost response, check durable state before retrying (Ch14, Ch53).
- Step and token budgets with named stop reasons (`MODEL_ANSWER`, `STEP_BUDGET`, `TOKEN_BUDGET`, plus domain ones like `ESCALATED`) (Ch14).
- Compensation is a new, separately authorized action, never an automatic retry side effect (Ch53).

## D11. Evaluation and observability (Ch41-Ch45)

- Evaluate the trajectory, not just the final answer: task success, groundedness, tool accuracy, efficiency and safety as separate dimensions (Ch41).
- Golden set with stable case IDs, happy and failure paths, abstention cases; versioned dataset and environment (Ch42).
- Tracing: one span tree per run (OpenTelemetry), redacted before export (Ch43).
- Deterministic checks first; model judges only for qualities rules cannot express, calibrated against humans (Ch44).
- Release gate: PROMOTE or HOLD, with a zero-tolerance safety floor; a good average never hides an unsafe case (Ch45, Ch64).

## D12. Deployment, cost and operations (Ch51-Ch55)

- Long work: fast submit plus async worker with a durable queue and job store (transactional outbox); idempotent request IDs (Ch51).
- Cost = tokens x rate over the trajectory; levers are volume (compaction, caching, budgets) and rate (routing, smaller models); check quality before cost (Ch52).
- Version and roll back the whole **bundle** (prompt, model, tools, retrieval data, policy); canary on labelled tasks; SLOs with owners; runbooks (Ch54).
- A pilot needs identity, scoped effects, a spending limit, a tested restore and a named owner (Ch55).
- Computer-use or coding agents run in a sandbox: allowlisted commands, no shell, empty environment, scoped working dir, egress rules, and verified state changes rather than model claims (Ch36-Ch40).
