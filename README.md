<p align="center">
  <img src="assets/gatesignal-banner.svg" alt="GateSignal — know when the evidence deserves the next investment" width="100%">
</p>

<p align="center">
  <a href="https://github.com/UlrikErlingsen/launch-decision-gate/actions/workflows/tests.yml"><img alt="Tests" src="https://github.com/UlrikErlingsen/launch-decision-gate/actions/workflows/tests.yml/badge.svg"></a>
  <img alt="Python 3.10+" src="https://img.shields.io/badge/Python-3.10%2B-173C3A?logo=python&logoColor=white">
  <img alt="Streamlit" src="https://img.shields.io/badge/Streamlit-app-D95B40?logo=streamlit&logoColor=white">
  <a href="LICENSE"><img alt="License: AGPL-3.0-or-later" src="https://img.shields.io/badge/License-AGPL--3.0--or--later-36534E"></a>
</p>

<p align="center"><strong>Open new-product gate support — keep evidence, economics, hard constraints, and accountable judgment visibly separate.</strong></p>

GateSignal is a local-first decision-support app for one difficult new-product question:

> Should this concept receive the next bounded investment?

It combines declared decision criteria, evidence strength, hard gate checks, scenario cash flows, a transparent volume bridge, risk contingencies, a brand-extension/alliance evidence audit, and independent challenge prompts. It does **not** calculate a probability of product success or approve a project automatically.

## Read this first

> **GateSignal structures a bounded investment decision; it does not manufacture evidence or delegate approval.** The scores express declared preferences, the cash flows remain scenarios, and the accountable gatekeepers retain the decision.

## Why GateSignal

New-product reviews often mix different claims into one persuasive average. A strategically attractive concept can still fail a safety requirement. A positive base case can hide a negative downside. A high risk can be “mitigated” without an owner or observable trigger. GateSignal keeps these questions visible and separate.

The app supports six linked tasks:

1. declare weighted criteria and non-compensatory must-pass requirements;
2. record evidence strength separately from preference scores;
3. compare downside, reference, and upside cash-flow scenarios using NPV;
4. assign owners, mitigations, triggers, and responses to material risks;
5. audit fit, transfer asymmetry, dilution, control, disclosure, activism, and reputation exposure when a brand extension or alliance is involved; and
6. export a traceable evidence pack for an accountable human decision.

## Try it in three minutes

- Begin with the fictional **LoopDose** demonstration or download the blank project template.
- Adapt criteria before scoring. Hard gates should be few, explicit, and genuinely non-compensatory.
- Treat evidence strength as an audit prompt, not a statistical confidence interval.
- Enter scenario probabilities that sum to `1.00`, forward cash flows by period, and the decision owner's declared discount rate.
- Add the response plan for every high or critical risk before treating the case as decision-ready.
- Review the brand-extension/alliance section and mark genuinely non-compensatory exposures as must-resolve.
- Complete the independent challenge checklist and export the evidence pack.

The downloadable `.xlsx` and `.json` project files are portable and editable. All analysis runs in the local Python process; GateSignal has no analytics SDK, database, account system, or required network service.

## Method boundary

GateSignal is decision structure, not a forecasting oracle:

- the weighted criterion score expresses declared preferences, not product-success probability;
- evidence coverage is a weighted documentation indicator, not a p-value or confidence level;
- brand evidence coverage is not a universal fit, equity, authenticity, or reputation score;
- a 1–5 risk matrix is ordinal triage, not expected monetary loss;
- the volume bridge is assumption arithmetic, not a calibrated adoption model;
- NPV is primary; IRR is suppressed when the cash-flow pattern does not support a unique interpretable result;
- the generated disposition is a conservative discussion prompt, never an authorization.

See [Methods](docs/methods.md), [Data guide](docs/data-guide.md), and [Decision guide](docs/decision-guide.md).

## Run locally

On macOS, double-click `run_app.command`, or run:

```bash
./run_app.command
```

On Windows, double-click `run_app.bat`.

For a manual setup:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Then open the local address shown in the terminal. GateSignal prefers port `8597` and selects a free port if it is occupied.

### Docker

```bash
docker build -t gatesignal .
docker run --rm -p 8597:8597 gatesignal
```

Then open `http://127.0.0.1:8597`. The container runs as a non-root user.

## No install? Give this file to an AI

Don't want to install anything? [AI_ANALYST.md](AI_ANALYST.md) is a single copy-paste file that turns a capable AI assistant (Claude, ChatGPT, Gemini, …) into this analysis. Copy the file into a chat, add your data, and the AI follows the same published methods and honesty rules as the app. The app is still the more private option: local mode keeps your data on your computer, while a cloud AI sees whatever you paste.

## Academic basis and originality

The app is independently designed and written from general decision-analysis, capital-budgeting, forecasting, behavioral-decision, and new-product-management literature. The citations point to original publications. No lecture slides, classroom cases, assessment material, proprietary gate template, or course-specific wording is reproduced. The bundled example, company, numbers, evidence notes, and interface are fictional and created for this project.

See [Sources and originality](docs/sources-and-originality.md) for the complete boundary and bibliography.

## Development

```bash
python -m pip install -e '.[test]'
pytest
ruff check .
python -m build
```

The package requires Python 3.10 or newer. Tests cover the analytical rules, safe project-file round trips, exports, and every Streamlit page.

## Relationship to the Signal suite

GateSignal is the decision gate of a family of open, local-first marketing-analytics apps that share one design language but do different statistical jobs — it structures the go/hold/rework/kill conversation and **imports their evidence instead of duplicating their engines**:

- **[ChoiceSignal](https://github.com/UlrikErlingsen/conjoint-analysis)** — conjoint analysis and a single-concept purchase-intent test whose trial-intention JSON export (`signal.trial-intention.v1`) loads directly into GateSignal's volume bridge as the trial-rate assumption.
- **[AdoptSignal](https://github.com/UlrikErlingsen/adoption-forecasting)** — Bass-diffusion adoption forecasting for the *when* behind the volume story.
- **[WorthSignal](https://github.com/UlrikErlingsen/customer-value-analytics)** — customer value, retention, and marketing ROI for the unit-economics assumptions.
- **[SegmentSignal](https://github.com/UlrikErlingsen/customer-segmentation)** — customer segmentation for who the concept is actually for.
- **[PositionSignal](https://github.com/UlrikErlingsen/brand-positioning)** — perceptual mapping for the competitive-position evidence.
- **[DriverSignal](https://github.com/UlrikErlingsen/survey-driver-analysis)** — survey driver analysis for what moves satisfaction.
- **[AllocSignal](https://github.com/UlrikErlingsen/marketing-mix-allocation)** — response curves and budget allocation once a concept passes the gate.
- **[ExperimentSignal](https://github.com/UlrikErlingsen/experiment-analysis)** — randomized experiment analysis whose decision status, effect estimate, and interval are exactly the customer-evidence input a gate review wants.
- **[MeasureSignal](https://github.com/UlrikErlingsen/measurement-validation)** — measurement diagnostics for the multi-item scores behind the evidence register.
- **[TextSignal](https://github.com/UlrikErlingsen/open-text-analysis)** — open-text evidence: stable language patterns from customer responses, handed to human coding.
- **[RecommendSignal](https://github.com/UlrikErlingsen/recommender-evaluation)** — offline recommendation-policy evidence when the gated concept includes a recommender; commercial or causal lift still belongs in ExperimentSignal.

GateSignal also reads the `signal.price-evidence.v1` bridge from the local **PriceSignal** working build as a unit-margin assumption. That label has a material active-market conflict and is not cleared for public release, so it is intentionally not linked or presented as a public suite handoff.

The maintained public suite is listed at [ulrikerlingsen.com](https://ulrikerlingsen.com).

## Privacy, security, and license

GateSignal is local-first. Review [PRIVACY.md](PRIVACY.md) and [SECURITY.md](SECURITY.md) before using real company data. The software is licensed under the [GNU Affero General Public License v3 or later](LICENSE). Academic references remain the property of their authors and publishers.
