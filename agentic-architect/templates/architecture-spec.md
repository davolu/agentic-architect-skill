# <System name> architecture

> Designed with Agentic Architect. Diagram: <Miro board link or "see architecture.mmd">. Machine-readable twin: `architecture.json`.

## 1. Goal and scope
- **User and journey:**
- **Done means:** (observable acceptance criteria, Ch7)
- **Supported requests:**
- **Non-goals:**

## 2. Autonomy (Ch1, Ch24)
Level: <single call | workflow | hybrid | bounded agent | autonomous with approvals>. Per decision: who chooses the next step?

| Decision | Chosen by | Why |
|---|---|---|

## 3. Pattern decisions
| # | Decision | Choice | Reason | Chapter | Rejected alternative |
|---|---|---|---|---|---|
| D1 | Autonomy | | | Ch1, Ch24 | |
| D2 | Workflow vs agent | | | Ch24 | |
| D3 | Reasoning pattern | | | Ch13 | |
| D4 | Single vs multi-agent | | | Ch31 | |
| D5 | Tools / MCP | | | Ch11, Ch29 | |
| D6 | Knowledge / RAG | | | Ch17 | |
| D7 | Memory and state | | | Ch18, Ch19 | |
| D8 | Guardrails | | | Ch48 | |
| D9 | Human in the loop | | | Ch49 | |
| D10 | Reliability | | | Ch14, Ch53 | |
| D11 | Evals and tracing | | | Ch41-45 | |
| D12 | Deployment and cost | | | Ch51-52 | |

## 4. Components
| Layer | Component | Kind | Responsibility | Owner |
|---|---|---|---|---|

## 5. Data flows
| From | To | What flows | Trusted? |
|---|---|---|---|

## 6. Trust boundaries and checkers (Ch46, Ch62)
| Boundary | What crosses | Checker (code) | On failure |
|---|---|---|---|

## 7. Tool contracts (Ch11, Ch48)
| Tool | Read/write | Scope | Inputs (typed) | Errors | Timeout | Idempotency |
|---|---|---|---|---|---|---|

## 8. State, memory and checkpoints (Ch18, Ch19)
| Store | Holds | Owner scope | Retention | Deletion |
|---|---|---|---|---|

## 9. Human approval points (Ch49)
| Action | Approver | Evidence shown | Expiry | On timeout |
|---|---|---|---|---|

## 10. Failure handling (Ch14, Ch53)
- Budgets: steps, tokens, cost, time
- Stop reasons:
- Retries and circuit breakers:
- Escalation path:

## 11. Evaluation and observability (Ch41-Ch45)
- Dimensions and floors:
- Golden set (size, categories):
- Tracing and audit:
- Release gate:

## 12. Cost and latency (Ch52)
- Estimate per task and levers:

## 13. Risks and owners (Ch46, Ch59)
| Risk | Impact x likelihood | Prevent / detect / correct | Owner |
|---|---|---|---|

## 14. Open questions
