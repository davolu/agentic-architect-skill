# Design checklist

## The eight core questions (Step 1)

Ask only the ones not yet answered. Offer a default in brackets so the user can accept quickly.

1. **Goal and done.** What outcome means the task is complete? Who is the user? [default: one named user, one journey]
2. **Autonomy.** Should it suggest, draft, act with approval, or act alone? [default: draft or act-with-approval]
3. **Tools and systems.** What does it read? What does it change? Any existing MCP servers or APIs?
4. **Data and memory.** Which documents or databases? Does it need to remember anything across sessions? [default: no long-term memory in v1]
5. **Risks and side effects.** Can it move money, delete, send messages, change permissions, run code, touch personal data?
6. **Human approval.** Which actions need a person to approve, and who? [default: every irreversible action]
7. **Latency and cost.** Interactive (seconds) or background (minutes)? Budget per task?
8. **Evaluation.** How will you know it works? Any examples of good and bad outcomes? [default: 20-case golden set incl. failure cases]

Follow-ups only if relevant: multi-tenant or single-user? regulated data or region? existing framework or language? deployment target? who owns operations?

## The spec must answer (Step 3)

- [ ] Goal, user, supported requests and explicit **non-goals** (Ch61)
- [ ] Autonomy level per decision (Ch1, Ch24)
- [ ] Components by layer, each with a single owner and a `kind`
- [ ] Data flows, labelled; which flows carry untrusted content
- [ ] **Trust boundaries** and the concrete checker at each (Ch62)
- [ ] Tool contracts: name, read or write, scope, schema, error codes, timeout (Ch11, Ch48)
- [ ] State, memory and checkpoints: what, where, owner, retention, deletion (Ch19)
- [ ] HITL points: what exactly is approved, by whom, expiry, what happens on timeout (Ch49)
- [ ] Failure handling: retries, idempotency, budgets, stop reasons, escalation (Ch14, Ch53)
- [ ] Evals: dimensions, golden set, release gate (Ch41-Ch45)
- [ ] Observability: trace, audit, redaction (Ch43)
- [ ] Cost and latency estimate and levers (Ch52)
- [ ] Risks with owners, ranked by impact x likelihood (Ch46)
- [ ] Rejected alternatives and why

## Layer order for the diagram (top = outside, bottom = inside)

Use the layers that apply, in this order, and name them plainly:

1. Users and channels
2. Edge and input guard
3. Planning (if plan-execute)
4. Orchestration / coordination
5. Agents or workers (if several)
6. Policy and human approval
7. Tools via MCP
8. Data, state and knowledge
9. Observability and evals

Put a trust boundary (`boundary_below`) under users and channels, and wherever untrusted content or a consequential action crosses.

## Red flags to call out

- A prompt is the only thing preventing a harmful action.
- A generic "execute" or "run SQL" tool with write access.
- Multi-agent with no named reason.
- Memory that can change what the agent is allowed to do.
- No step or cost budget; no stop reasons.
- "The LLM will check that": verification by the same model with no evidence.
- Tool output or retrieved text concatenated into the system prompt.
- No golden set or tracing before launch.
