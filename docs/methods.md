# Methods and limitations

GateSignal separates six objects that are easy to blur in a gate meeting: preferences, evidence, hard constraints, conditional economics, risk preparedness, and accountable judgment.

## Preference score

For criterion score \(s_i\) and positive raw weight \(w_i\), GateSignal normalizes the weights and calculates:

\[
S = \sum_i \frac{w_i}{\sum_j w_j}s_i
\]

Scores range from 0 to 10. The result is an additive multi-attribute preference score. It is not a probability of success. Additive scoring assumes that the declared scale and trade-offs are meaningful enough for the decision; users should challenge that assumption instead of treating the decimal result as objective fact.

## Evidence coverage

Evidence strength is entered on an ordinal 0–3 scale and kept outside the criterion score:

\[
E = \sum_i \frac{w_i}{\sum_j w_j}\frac{e_i}{3}
\]

This is a documentation indicator: high-weight claims supported by stronger evidence increase coverage. It is not statistical confidence, reliability, or validity. GateSignal highlights low-evidence criteria and reports a simple score band if every criterion score were one point lower or higher. That band is a sensitivity prompt, not an uncertainty distribution.

## Must-pass gates

A must-pass criterion fails when its score is below its declared threshold. This is deliberately non-compensatory: high scores elsewhere cannot offset a failed safety, legal, feasibility, or other genuine constraint. Teams should use hard gates sparingly because an arbitrary threshold can create false certainty.

## Scenario economics

For cash flow \(CF_t\), period \(t\), and management-entered discount rate \(r\):

\[
NPV = \sum_{t=0}^{T}\frac{CF_t}{(1+r)^t}
\]

Expected NPV is the probability-weighted average of scenario NPVs:

\[
E[NPV] = \sum_k p_k NPV_k
\]

Scenario probabilities must sum to one. They are user judgments, not inferred frequencies. GateSignal does not estimate the cost of capital; the accountable decision owner must supply and justify the discount rate.

IRR is displayed only when non-zero cash flows have exactly one sign change and the polynomial has one valid real solution greater than -100%. This removes many—but not every—interpretation problem. Discounted payback is secondary because it ignores value after the payback point.

## Volume bridge

The app makes a common commercial chain explicit:

\[
Trials = Market \times Awareness \times Availability \times TrialRate
\]

\[
RepeatUnits = Trials \times RepeatRate \times AdditionalUnitsPerRepeater
\]

\[
Contribution = (Trials + RepeatUnits) \times UnitContribution
\]

This is transparent assumption arithmetic. It is not a diffusion curve, simulated test market, causal demand model, or validated sales forecast. The resulting contribution does not automatically flow into the cash-flow table; users must reconcile timing, cannibalization, fixed costs, working capital, taxes, and other relevant items themselves.

## Risk triage and contingency readiness

Probability and impact are ordinal 1–5 ratings. Their product creates four triage bands: Low (1–4), Medium (5–9), High (10–15), and Critical (16–25). Multiplication helps order attention but does not make the scale cardinal and must not be read as expected loss.

A high or critical risk is response-ready only when it has all four fields: owner, mitigation, observable trigger, and executable response. “Response-ready” does not mean controlled or acceptable; it means the contingency is documented for review.

## Brand-extension and alliance evidence

The brand evidence register keeps eight questions visible: category fit, image/value fit, transfer asymmetry, dilution/confusion, control and exit rights, disclosure, activism congruence, and reputation spillover. Each row records direction (`Supports`, `Neutral / mixed`, `Raises concern`, or `Not assessed`), evidence strength 0–3, materiality 1–5, whether it must be resolved, an owner, a source/limitation note, and a next test.

Materiality-weighted evidence coverage is `sum(materiality × evidence_strength / 3) / sum(materiality)`. It is a documentation indicator, not a brand-fit score or success probability. A must-resolve row blocks when evidence is weak/unassessed or raises concern. A material concern also blocks when no owner and next test are documented. These transparent rules keep a persuasive overall case from hiding dilution, partner-control, disclosure, activism, or reputation exposure.

Public brand-extension research motivates testing perceived fit and potential feedback to the parent brand; brand-alliance research motivates reciprocal spillover and asymmetry checks. Brand-activism research motivates checking alignment between claims, practice, stakeholders, and partner conduct. GateSignal turns these into original audit prompts and does not reproduce a proprietary brand model.

## Decision disposition

GateSignal applies conservative rules in this order:

1. failed must-pass gate → **Rework or stop**;
2. weighted score below 5 → **Stop or redesign**;
3. unresolved declared brand blocker → **Hold for brand evidence**;
4. negative reference and expected NPV → **Rework economics**;
5. untreated high or critical risk → **Hold for risk response**;
6. evidence coverage below 60% → **Hold for evidence**;
7. fewer than two-thirds of challenge checks complete → **Hold for challenge**;
8. otherwise → **Consider go**.

These are transparent defaults, not empirically calibrated decision thresholds. The user can record a different management decision, rationale, funding limit, learning milestone, and review date in the export. Accountability never transfers to the software.

## Practical limitations

- Weighted scores can conceal disagreement about scales, criteria, and trade-offs.
- Scenario probabilities can create an appearance of precision unsupported by evidence.
- Cash flows may omit option value, interactions with other projects, resource constraints, or portfolio balance.
- Risk matrices can compress important differences and are sensitive to category definitions.
- Evidence strength is self-reported unless the governance process verifies it.
- A project-level tool cannot optimize an entire product portfolio.
- No model result substitutes for legal, safety, financial, technical, customer, or ethical review.

The implementation intentionally exposes these limits rather than hiding them behind a single “go score.”
