<p align="center">
  <img src="assets/gatesignal-banner.png" alt="Gate Signal: Does a concept deserve the next investment?" width="100%">
</p>

<p align="center">
  <a href="https://github.com/UlrikErlingsen/launch-decision-gate/actions"><img alt="Tests" src="https://github.com/UlrikErlingsen/launch-decision-gate/actions/workflows/tests.yml/badge.svg"></a>
  <a href="https://github.com/UlrikErlingsen/signal-hub"><img alt="Signal · Decide" src="https://img.shields.io/badge/Signal-Decide-4f80a2?labelColor=2e2b25"></a>
  <img alt="Python 3.10+" src="https://img.shields.io/badge/Python-3.10%2B-2e2b25?logo=python&logoColor=f9f4ed">
  <img alt="Streamlit" src="https://img.shields.io/badge/Streamlit-app-4f80a2?logo=streamlit&logoColor=f9f4ed">
  <a href="LICENSE"><img alt="License: AGPL-3.0-or-later" src="https://img.shields.io/badge/License-AGPL--3.0--or--later-645c50"></a>
</p>

<p align="center"><strong>Open new-product gate support — keep evidence, economics, hard constraints, and accountable judgment visibly separate.</strong></p>

**Gate Signal** is a local-first decision-support app for one difficult new-product question. It combines declared decision criteria, evidence strength, hard gate checks, scenario cash flows, a transparent volume bridge, risk contingencies, a brand-extension/alliance evidence audit, and independent challenge prompts. It does **not** calculate a probability of product success or approve a project automatically.

> Should this concept receive the next bounded investment?

Everything runs locally with open-source Python packages. There is no account, telemetry, analytics SDK, external AI call, remote database, required network service, or built-in persistence.

## Read this first

> **Gate Signal structures a bounded investment decision; it does not manufacture evidence or delegate approval.** The scores express declared preferences, the cash flows remain scenarios, and the accountable gatekeepers retain the decision.

New-product reviews often mix different claims into one persuasive average. A strategically attractive concept can still fail a safety requirement. A positive base case can hide a negative downside. A high risk can be “mitigated” without an owner or observable trigger. Gate Signal keeps these questions visible and separate.

Gate Signal is decision structure, not a forecasting oracle:

- the weighted criterion score expresses declared preferences, not product-success probability;
- evidence coverage is a weighted documentation indicator, not a p-value or confidence level;
- brand evidence coverage is not a universal fit, equity, authenticity, or reputation score;
- a 1–5 risk matrix is ordinal triage, not expected monetary loss;
- the volume bridge is assumption arithmetic, not a calibrated adoption model;
- NPV is primary; IRR is suppressed when the cash-flow pattern does not support a unique interpretable result;
- the generated disposition is a conservative discussion prompt, never an authorization.

## Scope

**Version 1.2 supports six linked tasks:**

1. declare weighted criteria and non-compensatory must-pass requirements;
2. record evidence strength separately from preference scores;
3. compare downside, reference, and upside cash-flow scenarios using NPV;
4. assign owners, mitigations, triggers, and responses to material risks;
5. audit fit, transfer asymmetry, dilution, control, disclosure, activism, and reputation exposure when a brand extension or alliance is involved; and
6. export a traceable evidence pack for an accountable human decision.

**It does not:** estimate demand, causal effects, cost of capital, technical feasibility, or safety; produce a probability of success, a universal brand-fit score, or a calibrated adoption forecast; or authorize spending. Measured trial intent comes from **[Choice Signal](https://github.com/UlrikErlingsen/conjoint-analysis)**, tested price evidence from **[Tag Signal](https://github.com/UlrikErlingsen/pricing-analysis)**, and causal customer evidence from **[Experiment Signal](https://github.com/UlrikErlingsen/experiment-analysis)**.

## Try the demo in three minutes

1. Start the app and click **Demo · LoopDose concept**, or download the blank project template.
2. Adapt criteria before scoring. Hard gates should be few, explicit, and genuinely non-compensatory. Treat evidence strength as an audit prompt, not a statistical confidence interval.
3. Enter scenario probabilities that sum to `1.00`, forward cash flows by period, and the decision owner's declared discount rate.
4. Add the response plan for every high or critical risk before treating the case as decision-ready, review the brand-extension/alliance section, and mark genuinely non-compensatory exposures as must-resolve.
5. Complete the independent challenge checklist and export the evidence pack as XLSX, CSV-ZIP, or JSON.

The demo is fictional synthetic data. The LoopDose concept, its interviews, financials, risks, companies, and decisions represent no real organisation, course case, or empirical finding and must not be treated as market evidence.

## Data contract

A project is a portable, editable `.xlsx` workbook or `.json` bundle; download the template from the sidebar to keep the expected names. Workbook sheets are case-insensitive, and spaces become underscores.

| Sheet | One row per | Key columns |
|---|---|---|
| `Metadata` | field | `field`, `value` (`project_name`, `decision_question`, `decision_owner`, `review_stage`, `currency`, `discount_rate`) |
| `Criteria` | criterion | `category`, `criterion`, `weight`, `score` (0–10), `evidence_strength` (0–3), `must_pass`, `threshold`, `evidence_note` |
| `Cash flows` | scenario × period | `scenario`, `probability`, `period`, `cash_flow` |
| `Volume bridge` | scenario | `market_size`, `awareness_rate`, `availability_rate`, `trial_rate`, `repeat_rate`, `additional_units_per_repeater`, `unit_contribution` |
| `Risks` | risk | `risk`, `owner`, `probability` (1–5), `impact` (1–5), `evidence_strength`, `mitigation`, `trigger`, `response` |
| `Brand evidence` | claim or risk | `domain`, `claim_or_risk`, `evidence_direction`, `evidence_strength`, `materiality`, `must_resolve`, `owner`, `evidence_note`, `next_test` |
| `Challenge` | check | `check`, `completed`, `note` |

Gate Signal accepts only `.xlsx` and `.json`; it does not execute macros or embedded code. Uploads default to a 50 MB limit, workbooks may not expand beyond 100 MB, and each analytical table is limited to 20,000 rows.

Two sibling bridges can prefill assumptions without duplicating their engines: a Choice Signal trial-intention JSON (`signal.trial-intention.v1`) sets a scenario's trial rate, and a Tag Signal price-evidence JSON (`signal.price-evidence.v1`) sets a scenario's unit contribution. The imported value stays an assumption; its source, caveats, and applied value are recorded in the project metadata and exports.

See the [data guide](docs/data-guide.md).

## Methods

1. **Criteria.** A normalized additive multi-attribute score, `S = Σ wⱼ sⱼ`, reported next to weighted evidence coverage, `E = Σ wⱼ eⱼ / 3`. Must-pass rows are non-compensatory, and a ±1 sensitivity range shows how fragile the score is.
2. **Economics.** Scenario NPV with an explicit, management-supplied discount rate; probability-weighted expected NPV; IRR only for a conventional cash-flow pattern with one valid real root; discounted payback as a secondary view.
3. **Volume bridge.** Transparent arithmetic: trials = market × awareness × availability × trial rate, plus repeat units. Not a calibrated simulated-test-market model.
4. **Risk.** Ordinal 1–5 probability × impact triage with contingency readiness (owner, mitigation, observable trigger, executable response).
5. **Brand extension and alliance.** Materiality-weighted evidence coverage with must-resolve blockers for fit, transfer, dilution, control, disclosure, activism, and reputation exposure.
6. **Challenge and disposition.** An independent challenge checklist, then conservative, ordered disposition rules.

See [methods](docs/methods.md).

## Decision statuses

The model disposition applies these transparent defaults in order; they are not empirically calibrated thresholds.

- **REWORK OR STOP**: a must-pass criterion fails; the weighted average cannot override it.
- **STOP OR REDESIGN**: the weighted score is below 5.
- **HOLD FOR BRAND EVIDENCE**: a declared brand-extension or alliance blocker remains unresolved.
- **REWORK ECONOMICS**: both the reference case and probability-weighted NPV are negative.
- **HOLD FOR RISK RESPONSE**: a high or critical risk lacks a complete contingency response.
- **HOLD FOR EVIDENCE**: weighted evidence coverage is below 60%.
- **HOLD FOR CHALLENGE**: fewer than two-thirds of the challenge checks are complete.
- **CONSIDER GO**: no built-in stop or hold rule fires. This is not approval and does not authorize spending.

The brand audit reports its own status: **BRAND RISK UNRESOLVED**, **BRAND EVIDENCE INCOMPLETE**, **CONDITIONAL BRAND SUPPORT**, or **NO AUTOMATIC BRAND CLEARANCE**.

See the [decision guide](docs/decision-guide.md).

## Exports

Excel, CSV-ZIP and JSON decision packs include:

- the decision brief: model disposition, headline, decision trace, and required actions;
- the accountable management decision and its rationale;
- metadata: project fields, software version, Python version, and the SHA-256 fingerprint of the project bundle;
- criteria, evidence gaps, scenario economics, cash flows, and the volume bridge;
- the risk register, brand evidence and gaps, and the challenge record;
- status notes stating that the score is not a probability of success and the risk rating is ordinal triage.

Spreadsheet exports neutralize text beginning with `=`, `+`, `-`, or `@` to reduce formula-injection risk.

## Run locally

You need Python 3.10 or newer and a local copy of this folder.

**macOS:** double-click `run_app.command`. **Windows:** double-click `run_app.bat`.

The first launch creates a private `.venv` and downloads open-source dependencies. Later launches reuse it. Or use a terminal:

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Then open the local address shown in the terminal. Gate Signal prefers local port `8597` and selects a free port if it is occupied. The launchers accept `GATESIGNAL_PORT`; the macOS launcher also accepts `GATESIGNAL_MAX_UPLOAD_MB` and `GATESIGNAL_NO_BROWSER`, and `GATESIGNAL_DEBUG=1` shows technical error details.

### Docker

```bash
docker build -t gatesignal .
docker run --rm -p 8597:8597 gatesignal
```

Then open http://127.0.0.1:8597. The container runs as a non-root user.

## Privacy

Gate Signal is local-first: project data is processed by the local Python process and is not sent to an analytics SDK, database, account system, or required network service. If someone hosts Gate Signal, that operator becomes responsible for transport security, authentication, logs, retention, and applicable privacy obligations. Review [PRIVACY.md](PRIVACY.md) and [SECURITY.md](SECURITY.md) before using real company data.

## No install? Give this file to an AI

[AI_ANALYST.md](AI_ANALYST.md) is a single copy-paste file that turns a capable AI assistant (Claude, ChatGPT, Gemini, …) into this analysis. Copy the file into a chat, add your data, and the AI follows the same published methods and honesty rules as the app. The local app is the more private option: local mode keeps your data on your computer, while a cloud AI sees whatever you upload or paste.

## Development

```bash
python -m pip install -e ".[test]"
python -m pytest
python -m ruff check .
python -m build
```

The analysis core installs without Streamlit or Plotly; `pip install -e ".[ui]"` adds the app dependencies. Tests cover the analytical rules, safe project-file round trips, exports, every Streamlit page, and the Signal Hub entry point (`gatesignal.ui.render`).

## Where this fits in Signal

Gate Signal is the decision gate of the suite: it structures the go/hold/rework/stop conversation and **imports evidence from the other apps instead of duplicating their engines**.

- **[Choice Signal](https://github.com/UlrikErlingsen/conjoint-analysis)** — conjoint analysis and a single-concept purchase-intent test whose trial-intention JSON export (`signal.trial-intention.v1`) loads directly into Gate Signal's volume bridge as the trial-rate assumption.
- **[Tag Signal](https://github.com/UlrikErlingsen/pricing-analysis)** — its `signal.price-evidence.v1` bridge supplies a unit-margin assumption for a volume scenario.
- **[Adopt Signal](https://github.com/UlrikErlingsen/adoption-forecasting)** — Bass-diffusion adoption forecasting for the *when* behind the volume story.
- **[Worth Signal](https://github.com/UlrikErlingsen/customer-value-analytics)** — customer value, retention, and marketing ROI for the unit-economics assumptions.
- **[Segment Signal](https://github.com/UlrikErlingsen/customer-segmentation)** — customer segmentation for who the concept is actually for.
- **[Position Signal](https://github.com/UlrikErlingsen/brand-positioning)** — perceptual mapping for the competitive-position evidence.
- **[Driver Signal](https://github.com/UlrikErlingsen/survey-driver-analysis)** — survey driver analysis for what moves satisfaction.
- **[Alloc Signal](https://github.com/UlrikErlingsen/marketing-mix-allocation)** — response curves and budget allocation once a concept passes the gate.
- **[Experiment Signal](https://github.com/UlrikErlingsen/experiment-analysis)** — randomized experiment analysis whose decision status, effect estimate, and interval are exactly the customer-evidence input a gate review wants.
- **[Measure Signal](https://github.com/UlrikErlingsen/measurement-validation)** — measurement diagnostics for the multi-item scores behind the evidence register.
- **[Text Signal](https://github.com/UlrikErlingsen/open-text-analysis)** — open-text evidence: stable language patterns from customer responses, handed to human coding.
- **[Recommend Signal](https://github.com/UlrikErlingsen/recommender-evaluation)** — offline recommendation-policy evidence when the gated concept includes a recommender; commercial or causal lift still belongs in Experiment Signal.
- **[Trace Signal](https://github.com/UlrikErlingsen/journey-path-analysis)** — descriptive customer-journey evidence from event logs: transitions, path support, drop-off, and Markov removal sensitivity, with no causal channel credit.
- **[Track Signal](https://github.com/UlrikErlingsen/brand-tracking)** — brand-tracking wave comparison: separate measures with intervals, multiple-comparison control, and declared practical thresholds.

<!-- signal-suite:start (generated from signal-hub/apps.yaml by scripts/sync_readme_suite.py) -->
| Family | App | Asks |
|---|---|---|
| Brand | [Track Signal](https://github.com/UlrikErlingsen/brand-tracking) | Is the brand moving, or is the tracker just noisy? |
| Brand | [Position Signal](https://github.com/UlrikErlingsen/brand-positioning) | Where do brands sit relative to competitors? |
| Market | [Prospect Signal](https://github.com/UlrikErlingsen/b2b-prospecting) | Which Norwegian companies fit your ideal customer, and which first? |
| Market | [Listen Signal](https://github.com/UlrikErlingsen/media-listening) | Who is talking about the brand in Norwegian media, and in what tone? |
| Market | [Influence Signal](https://github.com/UlrikErlingsen/influencer-campaigns) | Which creators delivered, and was every post labelled properly? |
| Market | [Season Signal](https://github.com/UlrikErlingsen/marketing-calendar) | What does the Norwegian marketing year look like, worked backwards? |
| Market | [Adopt Signal](https://github.com/UlrikErlingsen/adoption-forecasting) | When will a new product be adopted? |
| Customer | [Worth Signal](https://github.com/UlrikErlingsen/customer-value-analytics) | What are customers and relationships worth? |
| Customer | [Segment Signal](https://github.com/UlrikErlingsen/customer-segmentation) | Do customers form stable, useful groups? |
| Customer | [Trace Signal](https://github.com/UlrikErlingsen/journey-path-analysis) | How do logged customer journeys actually unfold? |
| Customer | [Recommend Signal](https://github.com/UlrikErlingsen/recommender-evaluation) | Which recommendation policy should be tested live? |
| Research | [Choice Signal](https://github.com/UlrikErlingsen/conjoint-analysis) | How do product attributes drive choice? |
| Research | [Driver Signal](https://github.com/UlrikErlingsen/survey-driver-analysis) | Which measured experiences move with satisfaction? |
| Research | [Measure Signal](https://github.com/UlrikErlingsen/measurement-validation) | Does a multi-item score have a defensible structure? |
| Research | [Text Signal](https://github.com/UlrikErlingsen/open-text-analysis) | What recurring patterns appear in open-ended responses? |
| Research | [Tag Signal](https://github.com/UlrikErlingsen/pricing-analysis) | What price range is supported, and how does profit move? |
| Decide | [Experiment Signal](https://github.com/UlrikErlingsen/experiment-analysis) | Did the treatment cause a practically meaningful change? |
| Decide | **Gate Signal** (this app) | Does a concept deserve the next investment? |
| Decide | [Shift Signal](https://github.com/UlrikErlingsen/cannibalization-analysis) | Does a launch grow the portfolio, or move existing demand around? |
| Decide | [Alloc Signal](https://github.com/UlrikErlingsen/marketing-mix-allocation) | Where should the next marketing budget go? |

All 20 apps run side by side in [Signal Hub](https://github.com/UlrikErlingsen/signal-hub), each opening with fictional demo data. Every repo carries the [`signal-suite`](https://github.com/topics/signal-suite) topic, and the suite is listed at [ulrikerlingsen.com](https://ulrikerlingsen.com). Freddo CRM is a separate product.
<!-- signal-suite:end -->

## References

- Aaker, D. A., & Keller, K. L. (1990). Consumer evaluations of brand extensions. *Journal of Marketing, 54*(1), 27–41. https://doi.org/10.1177/002224299005400102
- Arkes, H. R., & Blumer, C. (1985). The psychology of sunk cost. *Organizational Behavior and Human Decision Processes, 35*(1), 124–140. https://doi.org/10.1016/0749-5978(85)90049-4
- Cooper, R. G. (1990). Stage-gate systems: A new tool for managing new products. *Business Horizons, 33*(3), 44–54. https://doi.org/10.1016/0007-6813(90)90040-I
- Cooper, R. G., Edgett, S. J., & Kleinschmidt, E. J. (1999). New product portfolio management: Practices and performance. *Journal of Product Innovation Management, 16*(4), 333–351. https://doi.org/10.1016/S0737-6782(99)00005-3
- Edwards, W. (1977). How to use multiattribute utility measurement for social decisionmaking. *IEEE Transactions on Systems, Man, and Cybernetics, 7*(5), 326–340. https://doi.org/10.1109/TSMC.1977.4309720
- Howard, R. A. (1966). Decision analysis: Applied decision theory. *Proceedings of the Fourth International Conference on Operational Research*.
- Loken, B., & Roedder John, D. (1993). Diluting brand beliefs: When do brand extensions have a negative impact? *Journal of Marketing, 57*(3), 71–84. https://doi.org/10.1177/002224299305700305
- Silk, A. J., & Urban, G. L. (1978). Pre-test-market evaluation of new packaged goods: A model and measurement methodology. *Journal of Marketing Research, 15*(2), 171–191. https://doi.org/10.1177/002224377801500201
- Simonin, B. L., & Ruth, J. A. (1998). Is a company known by the company it keeps? Assessing the spillover effects of brand alliances on consumer brand attitudes. *Journal of Marketing Research, 35*(1), 30–42. https://doi.org/10.1177/002224379803500105
- Tversky, A., & Kahneman, D. (1974). Judgment under uncertainty: Heuristics and biases. *Science, 185*(4157), 1124–1131. https://doi.org/10.1126/science.185.4157.1124
- Vredenburg, J., Kapitan, S., Spry, A., & Kemper, J. A. (2020). Brands taking a stand: Authentic brand activism or woke washing? *Journal of Public Policy & Marketing, 39*(4), 444–460. https://doi.org/10.1177/0743915620947359

The citations point to original publications and remain the property of their authors and publishers. No citation validates Gate Signal's default thresholds or generated disposition.

## Originality and license

Gate Signal is independently designed and written from general decision-analysis, capital-budgeting, forecasting, behavioral-decision, and new-product-management literature. No lecture slides, classroom cases, assessment material, proprietary gate template, or course-specific wording is reproduced. The bundled example, company, numbers, evidence notes, and interface are fictional and created for this project. `Stage-Gate` is a third-party term; Gate Signal is not affiliated with or a substitute for any proprietary Stage-Gate product. See [sources and originality](docs/sources-and-originality.md) for the complete boundary and bibliography.

The software and documentation are free under the [GNU Affero General Public License v3 or later](LICENSE). The license covers this project's expression, not ownership of published statistical or decision-analysis methods.

This application was developed with AI coding assistance and checked through source review, analytical fixtures, deterministic synthetic tests, automated app tests and visual inspection. Verify material decisions independently; no warranty is provided.

---

<p>
  <img src="assets/gatesignal-mark-64.png" width="20" height="20" alt="" align="absmiddle">
  <strong>Gate Signal</strong> is part of <a href="https://github.com/UlrikErlingsen/signal-hub"><strong>Signal</strong></a>, open marketing-evidence tools by <a href="https://ulrikerlingsen.com">Ulrik Erlingsen</a>.
</p>
