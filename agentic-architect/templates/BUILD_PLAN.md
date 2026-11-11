# Build plan: <System name>

> Generated from `ARCHITECTURE.md` / `architecture.json`. Rule: code must match the architecture. If implementation needs to differ, update the spec and the diagram first, then this plan.

## 0. Ground rules
- The model proposes, the system disposes: all authorization, budgets and side effects live in plain, tested code (Ch4, Ch48).
- No secrets in code, prompts, logs or state; `.env.example` documents them (Ch5).
- Business logic in framework-agnostic functions (Ch21).
- Every task below has a test that proves it, written first or alongside.

## 1. Baseline (Ch5)
- [ ] Repo skeleton, pinned dependencies, README, `.env.example`
- [ ] Provider seam (one function for model calls) with timeout, bounded retries, structured logs (run ID, version, tokens, latency, status)
- [ ] Smoke tests: missing config error, mock response, secret-free log

## 2. Contracts (Ch8, Ch11)
- [ ] Typed request/response schemas for the edge
- [ ] Tool contracts from spec section 7: schema, read/write effect, stable error codes, one result envelope
- [ ] Action proposal schema for every side effect

## 3. Vertical slice: one journey end to end (Ch63)
Pick the single most important journey from the spec and build every layer thinly:
- [ ] Edge: auth, validation, request ID
- [ ] Orchestrator: the loop or graph with step/token budgets and named stop reasons
- [ ] Model steps: <list from spec>, structured outputs
- [ ] Tools/MCP: read tools first; client allowlist fails closed
- [ ] Policy gate: deny-by-default effect function
- [ ] HITL: durable interrupt with exact-action, single-use, expiring approval (if in spec)
- [ ] Write tool with idempotency key and ledger check
- [ ] Trace spans for every step

## 4. Remaining components (one task per spec component)
| Component (spec) | Task | Test that proves it | Done |
|---|---|---|---|

## 5. Safety tests (Ch47, Ch50)
- [ ] Prompt-injection fixtures (direct and indirect) with expected denials
- [ ] Unapproved action attempt: no side effect
- [ ] Expired / replayed approval: rejected
- [ ] Owner-confusion test on memory and data access
- [ ] Forced tool failures and budget exhaustion paths produce the right stop reason

## 6. Evaluation harness (Ch41-Ch45)
- [ ] Golden set with stable case IDs (happy, failure, abstention, adversarial)
- [ ] Deterministic checks, then model trials repeated N times
- [ ] Release gate script: PROMOTE / HOLD with per-dimension floors and zero-tolerance safety

## 7. Operations (Ch51-Ch55)
- [ ] Packaging (Dockerfile, secrets at runtime)
- [ ] SLOs, alerts with owners, runbook, rollback of the whole bundle
- [ ] Cost and latency report alongside quality

## 8. Traceability check (before calling it done)
- [ ] Every component in `architecture.json` maps to code and a test
- [ ] Every trust boundary has a checker in code and a test
- [ ] Every HITL point is enforced in code, not just in a prompt
- [ ] Diagram updated if anything changed
