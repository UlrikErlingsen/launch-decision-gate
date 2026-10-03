# Changelog

All notable changes to Gate Signal are documented here.

## 1.3.0 — 2026-10-03

Larger datasets: no built-in data limits when run locally. The decision rules, calculations, project-file contract and exports are unchanged.

### Larger datasets

- Larger datasets: run locally, Gate Signal has no built-in limit on project-file size, table rows or evidence imports any more (it was 50 MB, 20,000 rows per table, workbooks unzipping to 100 MB and 5 MB evidence exports); memory is the limit, and running out of memory is reported as a plain message. `GATESIGNAL_MAX_UPLOAD_MB` is no longer read in code; it only sets the launchers' Streamlit upload cap.
- The public demo (`SIGNAL_PUBLIC=1`) keeps demo limits from the new `gatesignal/limits.py`: 50 MB per project file, 20,000 rows per table, workbooks that unzip to at most 500 MB, and 5 MB per evidence export; its messages say the downloaded app has none.
- Only the Gate sheets and the metadata sheet are parsed, so unrelated sheets in a project workbook cost no time or memory (a 34 MB workbook with a 250,000-row extra sheet and six 20,000-row tables loads in about 9 s at about 160 MB peak memory; it was refused before). Reading a project shows a spinner.
- Streamlit's upload cap is 10,000 MB: `.streamlit/config.toml` (synced from Signal Hub), both launchers (`run_app.bat` now honors `GATESIGNAL_MAX_UPLOAD_MB` like `run_app.command`, default 10000) and the Dockerfile (`STREAMLIT_SERVER_MAX_UPLOAD_SIZE=10000`).

### Suite

- Suite: Rival, Reach, Learn and Blueprint Signal added to the suite table.

## 1.2.0 — 2026-10-02

Signal brand refresh and Signal Hub entry point. The decision rules, calculations, project-file contract, sibling-app bridges and exports are unchanged.

### Brand

- Display name written **Gate Signal** (with a space) in the app, README, docs, launchers, export metadata and CITATION. Package, file and environment-variable names stay `gatesignal` / `GATESIGNAL_*`; the `signal.trial-intention.v1` and `signal.price-evidence.v1` schema keys are unchanged. Sibling apps are written with spaced names too (Choice Signal, Tag Signal, …).
- The app uses the shared `signal_theme` module (Organic Signal design, Decide family colour `#4f80a2`, Figtree): sidebar lockup, masthead, hero, step cards, notes, decision card, footer, Plotly template and the mark as favicon replace the pasted styles. Charts keep their meaning with theme colours.
- New banner, social preview and marks in `assets/`; the old banner SVG is removed. `.streamlit/config.toml` uses the family colours; the 50 MB upload limit is unchanged.
- README follows the Signal template; bug-report and feature-request issue templates added.

### Signal Hub contract

- `gatesignal.ui` exposes `APP_INFO` and `render()`, so Signal Hub can embed the app; `app.py` is now a thin standalone entry point.
- All session-state and widget keys are namespaced `gate:` (including the page selector).
- `streamlit` and `plotly` moved to a `ui` extra (also in `test`); the decision core installs without them. `requirements.txt` still lists everything.
- New tests: no Streamlit/Plotly import outside `gatesignal.ui`, `render()` runs from a script without a page config, every widget key is namespaced, and `render()` works from a packaged install without repository files.

## 1.1.2 — 2026-07-17

- Sibling app PriceSignal is now TagSignal; labels and docs updated. The `signal.price-evidence.v1` schema key is unchanged.

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
