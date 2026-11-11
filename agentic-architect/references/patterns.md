# Patterns catalog

The building blocks of an agentic system, with the `kind` to use in `architecture.json` and the chapter that teaches each. Pick only what the decision rules justify.

## Core anatomy (Ch4)

Goal, policy, model, orchestrator, tools, state, memory, planner, evaluator, people and environment. The **orchestrator** (code) owns the loop; the **model** proposes; **tools** act; **policy** decides what is allowed; **people** set goals, approve and give feedback; the **environment** returns untrusted observations.

## Control patterns

| Pattern | kind | What it is | Chapter |
|---|---|---|---|
| Single LLM call with structured output | agent | one call, typed schema, validated | Ch8 |
| Deterministic workflow | orchestrator | fixed steps in code | Ch24 |
| Router | agent + orchestrator | model returns a typed route (enum); code dispatches | Ch24, Ch31 |
| Hybrid workflow | orchestrator + agent | code routes, authorizes and executes; model classifies and drafts | Ch24, Ch25 |
| Agent loop | orchestrator + agent | decide, dispatch, observe, update, stop; allowlisted dispatch | Ch12 |
| ReAct | agent | interleaved action and observation with a trace | Ch13 |
| Plan-execute | agent + guardrail | plan first, check it in code, then execute | Ch13, Ch7 |
| Reflection / verifier gate | guardrail | check the draft; revise only on failure | Ch13, Ch15 |
| Evaluator-optimizer | agent + guardrail | generate, score, improve within a budget | Ch24 |
| Orchestrator-workers / supervisor | orchestrator + agent | coordinator delegates bounded sub-tasks and validates results | Ch32, Ch35 |
| Peer handoff | agent | agents pass control; no central result | Ch32 |
| Sequential crew | agent | ordered specialist stages | Ch32 |
| Graph with durable state | orchestrator + data | typed state, reducers, conditional edges, checkpointer | Ch22, Ch23 |
| Durable human interrupt | human + data | pause in persisted state, resume with a decision | Ch23, Ch49 |

## Knowledge and state

| Component | kind | Notes | Chapter |
|---|---|---|---|
| Ingestion pipeline | orchestrator | chunk, embed, metadata (source ID, version, offsets) | Ch16 |
| Vector / hybrid index | data | semantic plus keyword with rank fusion, metadata filters | Ch16, Ch17 |
| Retriever | orchestrator | query rewrite (does not answer), filters, similarity floor | Ch17 |
| Grounded generator | agent | cites source IDs or abstains | Ch17, Ch20 |
| Working memory | data | current task only | Ch18 |
| Episodic memory | data | dated, bounded summaries of past episodes | Ch18 |
| Semantic memory | data | approved durable facts with source and date | Ch18 |
| Procedural memory | data | know-how, survives personal-data deletion | Ch18 |
| Checkpoint store | data | thread ID, sequence, next step, memory refs, no credentials | Ch19, Ch23 |
| Evidence store | data | each source stored once by ID; citations point only here | Ch15, Ch35 |

## Integration

| Component | kind | Notes | Chapter |
|---|---|---|---|
| Function tool | tool | narrow, typed, one envelope, stable error codes | Ch11 |
| MCP server | tool | tools, resources, prompts; stdio or Streamable HTTP | Ch26, Ch27 |
| MCP client / host policy | guardrail | allowlist fails closed, prefix namespacing, result limits | Ch29, Ch30 |
| A2A remote agent | external | Agent Card, tasks with lifecycle states, artifacts | Ch34 |
| Browser / computer-use executor | tool | DOM and accessibility tree, semantic locators, verify state | Ch36, Ch37 |
| Coding agent loop | orchestrator | reproduce, map, search, plan, patch, test, review | Ch38 |
| Sandbox | guardrail | allowlisted commands, empty env, scoped dir, time limits | Ch39, Ch40 |

## Safety and oversight

| Component | kind | Notes | Chapter |
|---|---|---|---|
| Input guard | guardrail | schema, size, PII redaction, injection screening | Ch47, Ch48 |
| Policy / effect gate | guardrail | typed proposal checked by deny-by-default code | Ch48, Ch65 |
| Output guard | guardrail | citations, PII, format, tone, size | Ch48 |
| Approval service | human | exact-action receipts, single-use, expiring | Ch49 |
| Escalation queue | human | named owner, safe outcome for every gate | Ch24, Ch56 |
| Budget guard | guardrail | step, token, cost and time budgets | Ch14, Ch52 |

## Operations

| Component | kind | Notes | Chapter |
|---|---|---|---|
| API edge | interface | typed request, auth, request ID | Ch51 |
| Queue + worker | orchestrator | async jobs, transactional outbox, idempotent workers | Ch51 |
| Cache | data | exact-key, scoped, versioned, expiring | Ch52 |
| Tracing | observability | OpenTelemetry span tree, redaction | Ch43 |
| Audit log | observability | approvals, denials, expiries; tamper-evident | Ch49 |
| Eval harness + release gate | observability | golden set, judges, PROMOTE/HOLD | Ch42, Ch45 |
| Release bundle registry | observability | prompt + model + tools + data + policy versions, rollback | Ch54 |
