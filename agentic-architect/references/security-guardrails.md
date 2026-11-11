# Security, guardrails and human oversight checklist

Run this pass on every design. Each item names the chapter it comes from. Put the results in the spec's `trust_boundaries`, `hitl` and `risks` sections.

## 1. Threat model first (Ch46)

- [ ] **Assets**: data (PII, secrets, business records) and authority (refunds, sends, deploys, deletes).
- [ ] **Actors**: users, operators, third-party content authors, attackers, other agents.
- [ ] **Trust boundaries**: every place data or control crosses between trust levels.
- [ ] **Abuse cases** written as reachable paths: "untrusted input X can reach asset Y via Z".
- [ ] Rank by impact x likelihood; pair each with prevent, detect and correct.
- [ ] A human owner accepts residual risks before release.

## 2. Untrusted content (Ch9, Ch47)

- [ ] User text, retrieved passages, web pages, emails, files and tool outputs are **data**, labelled with source and trust level, never placed in the system instruction.
- [ ] Indirect injection considered: content the agent reads while doing legitimate work.
- [ ] Confused deputy check: can a steered agent borrow its own privileges? Scope tools to the requesting user.
- [ ] Exfiltration: if the agent can read sensitive data **and** reach an exit (email, web request, public post, URL rendering), put a gate on the exit.
- [ ] Memory poisoning: memory writes are validated and owner-scoped; memory never relaxes permissions.

## 3. Layered guardrails (Ch48, Ch30)

| Layer | Control |
|---|---|
| Edge | authentication, typed request schema, size limits, rate limits (Ch51) |
| Model | behavioural contract, structured output, schema validation (Ch6, Ch8) |
| Tool | allowlist that fails closed, typed envelopes (schema, read/write effect, domain, rate budget, timeout), value validation (Ch11, Ch29, Ch48) |
| Effect | one small deny-by-default function decides every side effect, called by every transport (Ch65) |
| Environment | sandbox, egress rules, scoped credentials, empty child environment (Ch39) |
| Output | citations, PII, size and format checks (Ch48) |

- [ ] Every outcome starts as a denial; success is the only path that must be earned. Errors and timeouts are never reported as success.
- [ ] Denials are surfaced to the user and logged.
- [ ] No control depends on which model is used (Ch62).

## 4. Human-in-the-loop approvals (Ch49, Ch23)

- [ ] Approval is for an **exact action**: tool, target and parameters, bound with a keyed digest.
- [ ] Single-use and expiring; replay is rejected.
- [ ] Reviewer sees the evidence (source, amount, diff, draft), not the model's tone.
- [ ] Step-up authentication for high-impact writes.
- [ ] Timeout or missing reviewer leads to no effect plus escalation.
- [ ] Durable interrupt: checkpoint before the pause; the resumed node is small and side-effect free until approval is re-checked.
- [ ] Overrides are visible, attributed and re-approved.
- [ ] Audit records include denials and expiries, tamper-evident in production.

## 5. Identity, secrets and data (Ch5, Ch19, Ch28, Ch58)

- [ ] Secrets come from environment or a secret manager, never prompts, logs, state or images.
- [ ] Remote MCP over HTTP uses OAuth with audience-bound, scoped, short-lived tokens; 401 for identity, 403 for permission; no token passthrough.
- [ ] An ID is not permission: authorize every read and write by owner.
- [ ] Deletion removes the record and every reference, verified by reading back.
- [ ] Data region, retention and tenant isolation recorded (unknowns stay "unknown").

## 6. Agents that act on computers or code (Ch36-Ch40)

- [ ] Typed, narrow action space; semantic locators over coordinates.
- [ ] Observe before acting, verify after; success is a verified state change.
- [ ] Commands as argument lists without a shell, allowlisted, time-limited, in a scoped temp dir with an empty environment.
- [ ] Coding agents never edit tests to pass; verification by an independent test run and reviewed diff.
- [ ] Containers and network egress rules for anything hostile.

## 7. Prove it (Ch50)

- [ ] Red-team ledger: inputs with expected outcomes, including a benign control, re-run after every change.
- [ ] Expected denials are positive tests; observed effects (empty execution set) beat fluent refusals.
- [ ] Incident drill with owner, trigger, containment order and recovery criteria.
- [ ] Safety case: narrow claim, controls, evidence, residual risks, sign-off scope.
