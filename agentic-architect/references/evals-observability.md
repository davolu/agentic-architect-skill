# Evaluation and observability checklist

Fill the spec's `evals` section from this. Design evals with the architecture, not after it.

## What to measure (Ch41)

| Dimension | Example check | How |
|---|---|---|
| Task success | refund case resolved with the correct outcome | deterministic on final state |
| Groundedness | every claim cites a retrieved source ID that supports it | ID check plus claim check |
| Tool accuracy | right tool, valid arguments, no unnecessary calls | trace assertions |
| Trajectory efficiency | steps, tokens, latency per case | trace metrics |
| Safety | zero unapproved side effects, correct denials, injection resisted | effect ledger, red-team cases |
| Abstention | says "no supporting source" when it should | labelled unanswerable cases |
| User experience | clarity, tone, accessibility | human reviewers |

Write criteria **before** running; they must be observable and decidable.

## Datasets (Ch42)

- [ ] Golden set with stable unique case IDs: happy paths, failure paths, abstention, adversarial (injection), edge cases.
- [ ] Frozen environment (mocks, corpus snapshot); dataset and environment versioned separately and recorded with every result.
- [ ] Deterministic simulator checks first, model-backed trials second; repeat model trials and report the pass-rate range.
- [ ] Never silently rewrite a reviewed label to make a run pass.

## Tracing (Ch43)

- [ ] One trace per run: a tree of spans (model call, tool call, retrieval, approval, state transition) with one trace ID.
- [ ] Attributes: sanitized inputs and outputs, token counts, durations, approval outcomes, stop reason.
- [ ] Redact before values become attributes; export a fixed record shape; prefer allowlisted metadata.
- [ ] Telemetry records; it does not enforce. Enforcement stays in the code that acts.

## Judges (Ch44)

- [ ] Rules first. A model judge only for qualities rules cannot express (helpfulness, completeness of synthesis).
- [ ] Rubric with observable criteria and a typed verdict; blind, evidence-grounded grading.
- [ ] Calibrate against human labels (agreement, Cohen's kappa) and re-calibrate when the judge, rubric or traffic changes.

## Release gate (Ch45, Ch64, Ch65)

- [ ] Control and candidate on the same versioned benchmark.
- [ ] PROMOTE only if every dimension meets its floor; safety has a zero-tolerance floor; a sufficient-cases guard.
- [ ] Optimizations cross the same gates; never lower a threshold to pass.
- [ ] Save the report (JSON plus a readable summary) with the benchmark version.

## In production (Ch54, Ch55)

- [ ] SLIs and SLOs agreed in advance, alerts with owners; separate correct refusals from failures.
- [ ] Canary on labelled tasks before wide rollout; rollback to a known-good bundle; verify recovery by re-running evals.
- [ ] Sample real traffic for review; refresh the golden set with real failures (Ch3, Ch44).
