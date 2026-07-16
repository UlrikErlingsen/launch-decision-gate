# Changelog

All notable changes to GateSignal are documented here.

## 1.1.1 — 2026-07-16

### Security

- Export sanitizer now also neutralizes formula-like column headers and strips control characters; Docker images keep application code root-owned; defusedxml hardens workbook XML parsing.

## 1.1.0 — 2026-07-16

- Added a brand-extension and alliance evidence section covering category/image fit, transfer asymmetry, dilution, control and exit rights, disclosure, activism congruence, and reputation spillover.
- Added materiality, evidence-direction/strength, ownership, next-test, and must-resolve checks without producing a universal brand-fit score.
- Added brand evidence to project templates, portable exports, and conservative decision holds when a declared blocker remains unresolved.
- Import price evidence from PriceSignal: the price-evidence JSON export (schema `signal.price-evidence.v1`) can now prefill a volume scenario's unit contribution with the tested unit margin — candidate price minus declared unit cost — with the source, evidence tier, decision status, and applied value recorded in the project metadata, and an explicit extrapolation warning when the candidate price sits outside observed support.

## 1.0.0 — 2026-07-16

First public release.

- Import trial intention from ChoiceSignal: the concept-test JSON export (schema `signal.trial-intention.v1`) can now prefill a volume scenario's trial rate — weighted estimate or top-two-box ceiling — with the source, sample size, and applied value recorded in the project metadata and exports.
- The preferred local port moved from 8595 to 8597 so GateSignal and PositionSignal can run side by side.
- Added `AI_ANALYST.md`, the no-install copy-paste file that lets any AI assistant run the same decision-structuring workflow.
- Documentation: related Signal tools section in the README.

## 0.1.0 — 2026-07-15

- Added transparent multi-criteria scoring and non-compensatory must-pass checks.
- Added separate weighted evidence coverage and evidence-gap review.
- Added scenario NPV, constrained IRR, discounted payback, and an assumption-level volume bridge.
- Added ordinal risk triage, contingency readiness, and independent challenge prompts.
- Added conservative decision dispositions and portable evidence-pack exports.
- Added a fictional demonstration, blank template, methodological limits, tests, and local launchers.
