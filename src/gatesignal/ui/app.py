"""Gate Signal Streamlit UI.

Everything that draws the app runs inside ``render()`` (or the functions it calls), so it runs on every rerun,
both in the standalone ``app.py`` and inside Signal Hub. Module-level code here only defines constants and
functions. ``render()`` never calls ``st.set_page_config`` or ``st.navigation``.
"""

from __future__ import annotations

import hashlib
import inspect
import os
import platform
import traceback

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from gatesignal import __version__
from gatesignal.brand import BRAND_EVIDENCE_DIRECTIONS, analyze_brand_evidence
from gatesignal.decision import build_decision_brief
from gatesignal.errors import DataProblem, friendly_message
from gatesignal.examples import blank_project, demo_project
from gatesignal.finance import analyze_cash_flows, analyze_volume_bridge
from gatesignal.interop import read_price_evidence, read_trial_intention
from gatesignal.io import (
    load_project,
    project_template,
    results_to_excel,
    results_to_json,
    tables_to_csv_zip,
)
from gatesignal.risk import analyze_risks, challenge_completion, prepare_challenge
from gatesignal.scoring import score_gate
from gatesignal.ui import signal_theme as sig


NS = "gate"


def k(name: str) -> str:
    """Namespace a session-state or widget key with the app slug, so apps can share one Hub session."""
    return f"{NS}:{name}"


CAUTION = (
    "**Gate Signal structures a decision; it does not approve a project.** Scores express declared preferences, "
    "cash flows are conditional scenarios, and risk ratings are ordinal triage. The accountable gatekeepers remain "
    "responsible for the decision, the evidence, and the consequences."
)
SIDEBAR_TAGLINE = "Know when the evidence deserves the next investment."
MASTHEAD_KICKER = "OPEN PRODUCT DECISION SUPPORT"
MASTHEAD_PROMISES = ["Local-first", "Traceable", "Open source"]
FOOTER_LINE = "structured evidence, not automated approval"
DERIVED_STATE = (
    "gate_summary",
    "finance_summary",
    "volume_results",
    "risk_summary",
    "brand_summary",
    "challenge_score",
    "decision_brief",
)
RISK_BANDS = ("Low", "Medium", "High", "Critical")


def full_width(widget, *args, **kwargs):
    """Use Streamlit's current width API while retaining older compatibility."""
    try:
        parameters = inspect.signature(widget).parameters
    except (TypeError, ValueError):
        parameters = {}
    width_parameter = parameters.get("width")
    if width_parameter is not None and isinstance(width_parameter.default, str):
        kwargs["width"] = "stretch"
    elif "use_container_width" in parameters:
        kwargs["use_container_width"] = True
    return widget(*args, **kwargs)


def show_error(exc: Exception) -> None:
    """Render a useful error while keeping tracebacks opt-in."""
    st.error(friendly_message(exc))
    if not isinstance(exc, (DataProblem, ValueError)) and os.getenv("GATESIGNAL_DEBUG") == "1":
        with st.expander("Technical details"):
            st.code("".join(traceback.format_exception(exc)))


# ── State ────────────────────────────────────────────────────────────────────
def copy_project(project: dict[str, object]) -> dict[str, object]:
    copied: dict[str, object] = {}
    for key, value in project.items():
        copied[key] = value.copy(deep=True) if isinstance(value, pd.DataFrame) else dict(value) if isinstance(value, dict) else value
    return copied


def set_project(project: dict[str, object]) -> None:
    st.session_state[k("project")] = copy_project(project)
    for name in DERIVED_STATE:
        st.session_state.pop(k(name), None)
    st.session_state[k("project_epoch")] = int(st.session_state.get(k("project_epoch"), 0)) + 1


def invalidate_from(section: str) -> None:
    mapping = {
        "criteria": ["gate_summary", "decision_brief"],
        "economics": ["finance_summary", "volume_results", "decision_brief"],
        "risk": ["risk_summary", "challenge_score", "decision_brief"],
        "brand": ["brand_summary", "decision_brief"],
    }
    for name in mapping[section]:
        st.session_state.pop(k(name), None)


def go_to(page_name: str) -> None:
    """Ask for another page. The sidebar applies the request before the page radio is drawn, then reruns."""
    st.session_state[k("nav_request")] = page_name


def _ensure_state() -> None:
    for name, default in (
        ("project_epoch", 0),
        ("upload_epoch", 0),
        ("upload_identity", None),
        ("management_decision", "Not decided"),
        ("management_rationale", ""),
    ):
        st.session_state.setdefault(k(name), default)
    if st.session_state.get(k("project")) is None:
        set_project(blank_project())


def _project() -> dict[str, object]:
    return st.session_state[k("project")]


def _epoch() -> int:
    return int(st.session_state[k("project_epoch")])


# ── Charts ───────────────────────────────────────────────────────────────────
def criteria_figure(summary) -> go.Figure:
    ordered = summary.criteria.sort_values("weighted_contribution")
    roles = sig.roles(NS)
    colors = [roles["threshold"] if status == "Fail" else roles["highlight"] for status in ordered["must_pass_status"]]
    figure = go.Figure(
        go.Bar(
            x=ordered["weighted_contribution"],
            y=ordered["criterion"],
            orientation="h",
            marker_color=colors,
            customdata=ordered[["score", "normalized_weight", "evidence_strength"]],
            hovertemplate="%{y}<br>Contribution %{x:.2f}<br>Score %{customdata[0]:.1f}/10<br>Weight %{customdata[1]:.0%}<br>Evidence %{customdata[2]:.0f}/3<extra></extra>",
        )
    )
    figure.update_layout(
        template=sig.template(NS),
        title="Contribution to the weighted score",
        xaxis_title="Weighted points",
        yaxis_title=None,
        height=max(360, 46 * len(ordered)),
        margin=dict(l=20, r=20, t=60, b=40),
    )
    return figure


def finance_figure(summary) -> go.Figure:
    roles = sig.roles(NS)
    colors = [roles["threshold"] if value < 0 else roles["highlight"] for value in summary.scenarios["npv"]]
    figure = go.Figure(
        go.Bar(
            x=summary.scenarios["scenario"],
            y=summary.scenarios["npv"],
            marker_color=colors,
            customdata=summary.scenarios[["probability", "irr", "discounted_payback"]],
            hovertemplate="%{x}<br>NPV %{y:,.0f}<br>Probability %{customdata[0]:.0%}<extra></extra>",
        )
    )
    figure.add_hline(y=0, line_color=roles["zero"], line_width=1)
    figure.update_layout(
        template=sig.template(NS),
        title="Scenario net present value",
        xaxis_title=None,
        yaxis_title="NPV",
        height=410,
        margin=dict(l=20, r=20, t=60, b=40),
    )
    return figure


def volume_figure(frame: pd.DataFrame) -> go.Figure:
    figure = go.Figure()
    figure.add_bar(
        name="First-time trials",
        x=frame["scenario"],
        y=frame["first_time_trials"],
        marker_color=sig.FAMILIES["research"]["600"],
    )
    figure.add_bar(name="Repeat units", x=frame["scenario"], y=frame["repeat_units"], marker_color=sig.app(NS)["fam"]["600"])
    figure.update_layout(
        template=sig.template(NS),
        barmode="stack",
        title="Assumption bridge to modeled units",
        yaxis_title="Units",
        height=410,
        margin=dict(l=20, r=20, t=60, b=40),
        legend_orientation="h",
    )
    return figure


def risk_figure(summary) -> go.Figure:
    # Ordinal bands on the app's sequential ramp (200, 300, 600, 800): darker means a higher triage band.
    ramp = sig.sequential(NS)
    palette = dict(zip(RISK_BANDS, (ramp[0], ramp[1], ramp[2], ramp[4]), strict=True))
    label_colors = {"Low": sig.CORE["text"], "Medium": sig.CORE["text"], "High": sig.CORE["paper"], "Critical": sig.CORE["paper"]}
    figure = go.Figure()
    for band in RISK_BANDS:
        subset = summary.risks[summary.risks["risk_band"].eq(band)]
        if subset.empty:
            continue
        figure.add_trace(
            go.Scatter(
                x=subset["probability"],
                y=subset["impact"],
                mode="markers+text",
                name=band,
                text=[str(index + 1) for index in subset.index],
                textposition="middle center",
                textfont=dict(color=label_colors[band]),
                marker=dict(size=30, color=palette[band], line=dict(color=sig.CORE["text"], width=1)),
                customdata=subset[["risk", "owner", "response_ready"]],
                hovertemplate="%{customdata[0]}<br>Owner: %{customdata[1]}<br>Response ready: %{customdata[2]}<extra></extra>",
            )
        )
    figure.update_xaxes(range=[0.5, 5.5], dtick=1, title="Probability rating (ordinal)")
    figure.update_yaxes(range=[0.5, 5.5], dtick=1, title="Impact rating (ordinal)")
    figure.update_layout(
        template=sig.template(NS),
        title="Risk triage matrix",
        height=470,
        margin=dict(l=20, r=20, t=60, b=40),
        legend_orientation="h",
    )
    return figure


def build_all_summaries() -> tuple[object, object, pd.DataFrame, object, object, float, object]:
    project = _project()
    metadata = project["metadata"]
    gate = score_gate(project["criteria"])
    finance = analyze_cash_flows(project["cash_flows"], float(metadata.get("discount_rate", 0.12)))
    volume = analyze_volume_bridge(project["volume_bridge"])
    risks = analyze_risks(project["risks"])
    brand = analyze_brand_evidence(project["brand_evidence"])
    challenge = challenge_completion(project["challenge"])
    brief = build_decision_brief(gate, finance, risks, challenge, brand=brand)
    st.session_state[k("gate_summary")] = gate
    st.session_state[k("finance_summary")] = finance
    st.session_state[k("volume_results")] = volume
    st.session_state[k("risk_summary")] = risks
    st.session_state[k("brand_summary")] = brand
    st.session_state[k("challenge_score")] = challenge
    st.session_state[k("decision_brief")] = brief
    return gate, finance, volume, risks, brand, challenge, brief


# ── Pages ────────────────────────────────────────────────────────────────────
def page_welcome() -> None:
    sig.hero(
        NS,
        eyebrow="NEW-PRODUCT GATE DECISIONS",
        title="Make the next investment",
        em="earn its way through.",
        body=(
            "Gate Signal keeps customer evidence, strategic criteria, scenario economics, material risks, and "
            "independent challenge in one traceable decision pack. A polished average cannot hide a failed hard gate."
        ),
        pills=["Must-pass checks", "Evidence strength", "Scenario NPV", "Contingency triggers"],
    )
    st.warning(CAUTION)
    sig.cards(
        [
            (
                "STEP 01",
                "Declare the case",
                "Write the decision, score explicit criteria, identify hard gates, and record what evidence actually "
                "supports each claim.",
            ),
            (
                "STEP 02",
                "Challenge the economics",
                "Keep downside, reference, and upside cash flows separate; calculate NPV; and expose the reach, "
                "trial, and repeat assumptions.",
            ),
            (
                "STEP 03",
                "Prepare the response",
                "Name material risks, owners, observable triggers, and executable actions before asking for an "
                "irreversible commitment.",
            ),
        ]
    )
    st.markdown("### What Gate Signal refuses to do")
    refusal_cols = st.columns(3)
    refusal_cols[0].markdown("**No fake success probability**\n\nPreference scores and evidence strength stay separate.")
    refusal_cols[1].markdown("**No sunk-cost rescue**\n\nPast spending does not enter forward NPV.")
    refusal_cols[2].markdown("**No automatic approval**\n\nThe model recommendation is a prompt for accountable review.")
    if st.button("Open the gate review →", type="primary", key=k("open_review")):
        go_to("1 · Evidence & criteria")
        st.rerun()


def page_criteria() -> None:
    project = _project()
    metadata = project["metadata"]
    epoch = _epoch()
    sig.header(
        "Step 1",
        "Declare the decision and score the evidence",
        "Scores express preferences. Evidence strength expresses support. Hard gates remain non-compensatory.",
    )
    basics = st.columns([1.2, 1.4, 1.0])
    project_name = basics[0].text_input(
        "Project name", value=str(metadata.get("project_name", "")), key=k(f"project_name_{epoch}")
    )
    decision_owner = basics[1].text_input(
        "Accountable decision owner", value=str(metadata.get("decision_owner", "")), key=k(f"decision_owner_{epoch}")
    )
    review_stage = basics[2].text_input(
        "Review stage", value=str(metadata.get("review_stage", "")), key=k(f"review_stage_{epoch}")
    )
    decision_question = st.text_area(
        "Decision question",
        value=str(metadata.get("decision_question", "")),
        help="Write a bounded funding or commitment decision, not a general aspiration.",
        key=k(f"decision_question_{epoch}"),
    )
    metadata.update(
        {
            "project_name": project_name.strip(),
            "decision_owner": decision_owner.strip(),
            "review_stage": review_stage.strip(),
            "decision_question": decision_question.strip(),
        }
    )
    st.markdown("### Criteria table")
    st.caption("Weights may use any positive scale; Gate Signal normalizes them. Evidence: 0 none, 1 weak, 2 moderate, 3 strong.")
    edited = full_width(
        st.data_editor,
        project["criteria"],
        key=k(f"criteria_editor_{epoch}"),
        num_rows="dynamic",
        hide_index=True,
        column_config={
            "weight": st.column_config.NumberColumn(min_value=0.01, format="%.2f"),
            "score": st.column_config.NumberColumn(min_value=0.0, max_value=10.0, format="%.1f"),
            "evidence_strength": st.column_config.NumberColumn(min_value=0.0, max_value=3.0, step=1.0, format="%.0f"),
            "must_pass": st.column_config.CheckboxColumn(),
            "threshold": st.column_config.NumberColumn(min_value=0.0, max_value=10.0, format="%.1f"),
        },
    )
    if not edited.equals(project["criteria"]):
        project["criteria"] = edited
        invalidate_from("criteria")
    if st.button("Save criteria & score gate", type="primary", key=k("score_gate")):
        try:
            summary = score_gate(project["criteria"])
            st.session_state[k("gate_summary")] = summary
            st.session_state.pop(k("decision_brief"), None)
        except Exception as exc:
            show_error(exc)
    summary = st.session_state.get(k("gate_summary"))
    if summary is not None:
        metrics = st.columns(4)
        metrics[0].metric("Weighted score", f"{summary.weighted_score:.2f} / 10")
        metrics[1].metric("Evidence coverage", f"{summary.evidence_coverage:.0%}")
        metrics[2].metric("Must-pass failures", len(summary.must_pass_failures))
        low, high = summary.score_range_if_one_point_wrong
        metrics[3].metric("If every score is ±1", f"{low:.2f}–{high:.2f}")
        if summary.must_pass_failures:
            st.error("Failed must-pass criteria: " + "; ".join(summary.must_pass_failures) + ".")
        elif not summary.evidence_gaps.empty:
            st.warning(f"{len(summary.evidence_gaps)} criteria have weak or no evidence. Read these before the average score.")
        sig.chart(NS, criteria_figure(summary), key=k("criteria_chart"))
        with st.expander("Evidence gaps and normalized calculations", expanded=not summary.evidence_gaps.empty):
            if summary.evidence_gaps.empty:
                st.success("No criterion is currently marked with weak or absent evidence.")
            else:
                full_width(st.dataframe, summary.evidence_gaps, hide_index=True)
            full_width(st.dataframe, summary.criteria, hide_index=True)


def _scenario_names(project: dict[str, object]) -> list[str]:
    return [str(name).strip() for name in project["volume_bridge"]["scenario"].tolist() if str(name).strip()]


def _trial_intention_import(project: dict[str, object], metadata: dict[str, object], epoch: int) -> None:
    with st.expander("Import trial intention from Choice Signal"):
        st.caption(
            "Choice Signal's concept test exports a trial-intention JSON "
            "(schema `signal.trial-intention.v1`). Import it here to ground the trial rate in "
            "measured intent instead of a bare guess — the number stays an assumption, and its "
            "survey caveats travel with it."
        )
        intention_file = st.file_uploader(
            "Choice Signal trial-intention JSON",
            type=["json"],
            key=k(f"trial_intention_{epoch}"),
        )
        if intention_file is not None:
            try:
                intention = read_trial_intention(intention_file.getvalue())
            except Exception as exc:
                show_error(exc)
            else:
                st.info(
                    f"**{intention['concept']}** — {intention['respondents']:,} respondents "
                    f"({intention['source_product']} {intention['source_version']}). "
                    f"Weighted stated-trial estimate **{intention['weighted_trial_rate']:.1%}**; "
                    f"unadjusted top-two-box ceiling **{intention['ceiling_trial_rate']:.1%}**."
                )
                scenario_names = _scenario_names(project)
                if not scenario_names:
                    st.warning("Add at least one named volume scenario above before applying the import.")
                else:
                    apply_columns = st.columns([2, 2, 1])
                    chosen_value = apply_columns[0].radio(
                        "Value to apply",
                        ["Weighted estimate (recommended)", "Top-two-box ceiling"],
                        key=k("trial_intention_value"),
                    )
                    chosen_scenario = apply_columns[1].selectbox(
                        "Apply to scenario", scenario_names, key=k("trial_intention_scenario")
                    )
                    if apply_columns[2].button("Apply", key=k("apply_trial_intention")):
                        rate = (
                            intention["weighted_trial_rate"]
                            if chosen_value.startswith("Weighted")
                            else intention["ceiling_trial_rate"]
                        )
                        bridge = project["volume_bridge"].copy(deep=True)
                        mask = bridge["scenario"].astype(str).str.strip() == chosen_scenario
                        bridge.loc[mask, "trial_rate"] = rate
                        project["volume_bridge"] = bridge
                        metadata["trial_intention_import"] = (
                            f"{intention['concept']} · {intention['respondents']} respondents · "
                            f"{intention['source_product']} {intention['source_version']} · "
                            f"applied {rate:.4f} to ‘{chosen_scenario}’"
                        )
                        invalidate_from("economics")
                        st.session_state[k("project_epoch")] = epoch + 1
                        st.rerun()
        if metadata.get("trial_intention_import"):
            st.caption(f"Imported: {metadata['trial_intention_import']}. Recorded in the project metadata and exports.")


def _price_evidence_import(project: dict[str, object], metadata: dict[str, object], epoch: int) -> None:
    with st.expander("Import price evidence from Tag Signal"):
        st.caption(
            "Tag Signal exports a price-evidence JSON (schema `signal.price-evidence.v1`). "
            "Import it here to ground a scenario's unit contribution in the tested candidate price "
            "minus its declared unit cost — the number stays an assumption, and the pricing "
            "caveats travel with it. The market size is your population and is left untouched."
        )
        price_file = st.file_uploader(
            "Tag Signal price-evidence JSON",
            type=["json"],
            key=k(f"price_evidence_{epoch}"),
        )
        if price_file is not None:
            try:
                evidence = read_price_evidence(price_file.getvalue())
            except Exception as exc:
                show_error(exc)
            else:
                interval_low, interval_high = evidence["incremental_contribution_interval"]
                st.info(
                    f"Candidate price **{evidence['candidate_price']:,.2f}** vs reference "
                    f"**{evidence['reference_price']:,.2f}** "
                    f"({evidence['source_product']} {evidence['source_version']}). "
                    f"Unit margin **{evidence['unit_margin']:,.2f}** "
                    f"(candidate price − declared unit cost {evidence['declared_unit_cost']:,.2f}); "
                    f"projected volume **{evidence['candidate_projected_volume']:,.0f}**; "
                    f"incremental contribution **{evidence['incremental_contribution']:,.0f}** "
                    f"(interval {interval_low:,.0f} to {interval_high:,.0f}). "
                    f"Evidence tier: {evidence['evidence_tier']}."
                )
                st.caption(f"Tag Signal status: **{evidence['decision_status']}** — {evidence['interpretation']}")
                if not evidence["within_observed_support"]:
                    st.warning(
                        "The candidate price sits outside observed evidence support; "
                        "treat the projection as extrapolation."
                    )
                scenario_names = _scenario_names(project)
                if not scenario_names:
                    st.warning("Add at least one named volume scenario above before applying the import.")
                else:
                    apply_columns = st.columns([3, 1])
                    chosen_scenario = apply_columns[0].selectbox(
                        "Apply unit margin to scenario", scenario_names, key=k("price_evidence_scenario")
                    )
                    if apply_columns[1].button("Apply", key=k("apply_price_evidence")):
                        bridge = project["volume_bridge"].copy(deep=True)
                        mask = bridge["scenario"].astype(str).str.strip() == chosen_scenario
                        bridge.loc[mask, "unit_contribution"] = evidence["unit_margin"]
                        project["volume_bridge"] = bridge
                        metadata["price_evidence_import"] = (
                            f"candidate price {evidence['candidate_price']:.2f} − unit cost "
                            f"{evidence['declared_unit_cost']:.2f} · "
                            f"{evidence['source_product']} {evidence['source_version']} · "
                            f"tier {evidence['evidence_tier']} · status {evidence['decision_status']} · "
                            f"applied unit margin {evidence['unit_margin']:.2f} to ‘{chosen_scenario}’"
                        )
                        invalidate_from("economics")
                        st.session_state[k("project_epoch")] = epoch + 1
                        st.rerun()
        if metadata.get("price_evidence_import"):
            st.caption(f"Imported: {metadata['price_evidence_import']}. Recorded in the project metadata and exports.")


def page_economics() -> None:
    project = _project()
    metadata = project["metadata"]
    epoch = _epoch()
    sig.header("Step 2", "Challenge the volume and cash-flow story")
    st.warning(
        "These are conditional planning scenarios, not confidence intervals or forecasts. Scenario probabilities are judgments and must sum to 1."
    )
    controls = st.columns([1, 1, 2])
    currency = controls[0].text_input(
        "Currency label", value=str(metadata.get("currency", "NOK")), key=k(f"currency_{epoch}")
    )
    rate_percent = controls[1].number_input(
        "Discount rate %",
        min_value=0.0,
        max_value=100.0,
        value=float(metadata.get("discount_rate", 0.12)) * 100,
        step=0.5,
        key=k(f"discount_rate_{epoch}"),
    )
    with controls[2]:
        sig.note(
            "info",
            "**Hurdle-rate discipline.** Enter the organization-approved project rate. Gate Signal does not estimate "
            "a cost of capital from invented market inputs.",
        )
    metadata["currency"] = currency.strip() or "Currency"
    metadata["discount_rate"] = rate_percent / 100.0

    volume_tab, cash_tab = st.tabs(["Volume assumption bridge", "Scenario cash flows"])
    with volume_tab:
        st.caption(
            "Rates are decimals. Trial is conditional on the reachable population represented by market × awareness × availability. "
            "Additional units are purchases after first trial among repeaters."
        )
        edited_volume = full_width(
            st.data_editor,
            project["volume_bridge"],
            key=k(f"volume_editor_{epoch}"),
            num_rows="dynamic",
            hide_index=True,
        )
        if not edited_volume.equals(project["volume_bridge"]):
            project["volume_bridge"] = edited_volume
            invalidate_from("economics")
        _trial_intention_import(project, metadata, epoch)
        _price_evidence_import(project, metadata, epoch)
    with cash_tab:
        st.caption("Enter incremental future project cash flows only. Period 0 normally contains the next investment as a negative number.")
        edited_cash = full_width(
            st.data_editor,
            project["cash_flows"],
            key=k(f"cash_editor_{epoch}"),
            num_rows="dynamic",
            hide_index=True,
        )
        if not edited_cash.equals(project["cash_flows"]):
            project["cash_flows"] = edited_cash
            invalidate_from("economics")
    if st.button("Analyze economics", type="primary", key=k("analyze_finance")):
        try:
            st.session_state[k("volume_results")] = analyze_volume_bridge(project["volume_bridge"])
            st.session_state[k("finance_summary")] = analyze_cash_flows(project["cash_flows"], metadata["discount_rate"])
            st.session_state.pop(k("decision_brief"), None)
        except Exception as exc:
            show_error(exc)
    finance = st.session_state.get(k("finance_summary"))
    volume = st.session_state.get(k("volume_results"))
    if finance is not None and volume is not None:
        metrics = st.columns(4)
        label = str(metadata["currency"])
        metrics[0].metric("Probability-weighted NPV", f"{finance.expected_npv:,.0f} {label}")
        metrics[1].metric(f"{finance.reference_scenario} NPV", f"{finance.reference_npv:,.0f} {label}")
        metrics[2].metric("Probability of negative NPV", f"{finance.probability_negative_npv:.0%}")
        base_volume = volume.loc[volume["scenario"].str.casefold().eq("base")]
        selected_volume = base_volume.iloc[0] if not base_volume.empty else volume.iloc[0]
        metrics[3].metric(f"{selected_volume['scenario']} modeled units", f"{selected_volume['total_units']:,.0f}")
        chart_cols = st.columns(2)
        with chart_cols[0]:
            sig.chart(NS, finance_figure(finance), key=k("finance_chart"))
        with chart_cols[1]:
            sig.chart(NS, volume_figure(volume), key=k("volume_chart"))
        display = finance.scenarios.copy()
        display["irr"] = display["irr"].map(lambda value: "Suppressed" if pd.isna(value) else f"{value:.1%}")
        display["discounted_payback"] = display["discounted_payback"].map(
            lambda value: "Not reached" if pd.isna(value) else f"{value:.2f} periods"
        )
        st.markdown("### Scenario diagnostics")
        full_width(st.dataframe, display, hide_index=True)
        st.caption(
            "IRR is shown only for a conventional cash-flow pattern with one sign change and one valid real root. "
            "Discounted payback is secondary: unlike NPV, it ignores value created after payback."
        )


def page_risks() -> None:
    project = _project()
    epoch = _epoch()
    sig.header(
        "Step 3",
        "Turn uncertainty into owned responses",
        "The 1–5 ratings are ordinal triage. They prioritize discussion; they are not calibrated event probabilities or expected losses.",
    )
    risk_tab, brand_tab, challenge_tab = st.tabs(["Risk register", "Brand extension & alliance", "Independent challenge"])
    with risk_tab:
        edited_risks = full_width(
            st.data_editor,
            project["risks"],
            key=k(f"risk_editor_{epoch}"),
            num_rows="dynamic",
            hide_index=True,
            column_config={
                "probability": st.column_config.NumberColumn(min_value=1, max_value=5, step=1, format="%d"),
                "impact": st.column_config.NumberColumn(min_value=1, max_value=5, step=1, format="%d"),
                "evidence_strength": st.column_config.NumberColumn(min_value=0, max_value=3, step=1, format="%d"),
            },
        )
        if not edited_risks.equals(project["risks"]):
            project["risks"] = edited_risks
            invalidate_from("risk")
    with brand_tab:
        st.caption(
            "Use this section when a concept extends a brand, borrows another party's associations, uses a commercial "
            "alliance, or could create reputation spillovers. Evidence strength is 0–3; materiality is ordinal 1–5."
        )
        edited_brand = full_width(
            st.data_editor,
            project["brand_evidence"],
            key=k(f"brand_editor_{epoch}"),
            num_rows="dynamic",
            hide_index=True,
            column_config={
                "evidence_direction": st.column_config.SelectboxColumn(options=BRAND_EVIDENCE_DIRECTIONS),
                "evidence_strength": st.column_config.NumberColumn(min_value=0, max_value=3, step=1, format="%d"),
                "materiality": st.column_config.NumberColumn(min_value=1, max_value=5, step=1, format="%d"),
                "must_resolve": st.column_config.CheckboxColumn(),
            },
        )
        if not edited_brand.equals(project["brand_evidence"]):
            project["brand_evidence"] = edited_brand
            invalidate_from("brand")
        st.info(
            "The audit covers category/image fit, transfer asymmetry, dilution, control and exit rights, disclosure, "
            "activism congruence, and reputation spillover. It does not produce a universal brand-fit score."
        )
    with challenge_tab:
        st.caption("A checked box needs a note that lets another reviewer understand what was actually done.")
        edited_challenge = full_width(
            st.data_editor,
            project["challenge"],
            key=k(f"challenge_editor_{epoch}"),
            num_rows="dynamic",
            hide_index=True,
            column_config={"completed": st.column_config.CheckboxColumn()},
        )
        if not edited_challenge.equals(project["challenge"]):
            project["challenge"] = edited_challenge
            invalidate_from("risk")
    if st.button("Review risks, brand evidence & contingencies", type="primary", key=k("analyze_risk")):
        try:
            st.session_state[k("risk_summary")] = analyze_risks(project["risks"])
            st.session_state[k("brand_summary")] = analyze_brand_evidence(project["brand_evidence"])
            st.session_state[k("challenge_score")] = challenge_completion(project["challenge"])
            st.session_state.pop(k("decision_brief"), None)
        except Exception as exc:
            show_error(exc)
    risks = st.session_state.get(k("risk_summary"))
    brand = st.session_state.get(k("brand_summary"))
    challenge = st.session_state.get(k("challenge_score"))
    if risks is not None and brand is not None and challenge is not None:
        metrics = st.columns(4)
        metrics[0].metric("High / critical risks", risks.high_or_critical)
        metrics[1].metric("Without complete response", risks.untreated_high_or_critical)
        metrics[2].metric("Contingency coverage", f"{risks.contingency_coverage:.0%}")
        metrics[3].metric("Challenge completed", f"{challenge:.0%}")
        if risks.untreated_high_or_critical:
            st.error("At least one high or critical risk lacks an owner, mitigation, observable trigger, or executable response.")
        sig.chart(NS, risk_figure(risks), key=k("risk_chart"))
        with st.expander("Preparedness table", expanded=True):
            full_width(st.dataframe, risks.risks, hide_index=True)
        st.markdown("### Brand extension & alliance evidence")
        brand_metrics = st.columns(4)
        brand_metrics[0].metric("Evidence status", brand.status)
        brand_metrics[1].metric("Evidence coverage", f"{brand.evidence_coverage:.0%}")
        brand_metrics[2].metric("Material concerns", brand.material_concerns)
        brand_metrics[3].metric("Blocking items", len(brand.blocking_items))
        if brand.blocking_items:
            st.error("Unresolved brand evidence blockers: " + "; ".join(brand.blocking_items) + ".")
        elif brand.status == "BRAND EVIDENCE INCOMPLETE":
            st.warning("Brand evidence is incomplete. Preserve the gaps rather than inferring fit from absence of concern.")
        else:
            st.info("Brand evidence remains conditional on the declared scope, sources, partners, claims, and response plans.")
        with st.expander("Brand evidence audit and gaps", expanded=bool(brand.blocking_items)):
            full_width(st.dataframe, brand.evidence, hide_index=True)
            if not brand.evidence_gaps.empty:
                st.markdown("**Weak, unassessed, or blocking evidence**")
                full_width(st.dataframe, brand.evidence_gaps, hide_index=True)


def page_decision() -> None:
    project = _project()
    metadata = project["metadata"]
    sig.header("Step 4", "Build the accountable decision brief")
    st.warning(CAUTION)
    if st.button("Build decision brief", type="primary", key=k("build_decision")):
        try:
            build_all_summaries()
        except Exception as exc:
            show_error(exc)
    brief = st.session_state.get(k("decision_brief"))
    if brief is None:
        st.info("Build the brief when the criteria, economics, risks, brand evidence, and challenge record are ready.")
        return
    sig.cards([("MODEL DISPOSITION", str(brief.disposition), str(brief.headline))])
    reason_col, action_col = st.columns(2)
    with reason_col:
        st.markdown("### Decision trace")
        for reason in brief.reasons:
            st.markdown(f"- {reason}")
    with action_col:
        st.markdown("### Required before commitment")
        for action in brief.required_actions:
            st.markdown(f"- {action}")
    st.markdown("### Management record")
    record_cols = st.columns([1, 2])
    decision_options = ["Not decided", "Go", "Hold", "Rework", "Stop"]
    current = st.session_state.get(k("management_decision"), "Not decided")
    management_decision = record_cols[0].selectbox(
        "Accountable management decision",
        decision_options,
        index=decision_options.index(current) if current in decision_options else 0,
        key=k("management_decision_input"),
    )
    management_rationale = record_cols[1].text_area(
        "Decision rationale and conditions",
        value=st.session_state.get(k("management_rationale"), ""),
        height=120,
        key=k("management_rationale_input"),
    )
    st.session_state[k("management_decision")] = management_decision
    st.session_state[k("management_rationale")] = management_rationale
    if management_decision != "Not decided" and not management_rationale.strip():
        st.warning("Record why management accepted, changed, or rejected the model disposition before exporting.")

    gate = st.session_state[k("gate_summary")]
    finance = st.session_state[k("finance_summary")]
    volume = st.session_state[k("volume_results")]
    risks = st.session_state[k("risk_summary")]
    brand = st.session_state[k("brand_summary")]
    challenge_frame = prepare_challenge(project["challenge"])
    source_fingerprint = hashlib.sha256(project_template(project)).hexdigest()
    export_metadata = {
        **metadata,
        "software": "Gate Signal",
        "version": __version__,
        "python": platform.python_version(),
        "source_fingerprint_sha256": source_fingerprint,
        "model_disposition": brief.disposition,
        "management_decision": management_decision,
        "management_rationale": management_rationale.strip(),
        "decision_status": "Decision support; accountable management judgment required.",
        "score_status": "Weighted preference score; not a probability of success.",
        "risk_status": "Ordinal triage; not calibrated probability or expected loss.",
        "brand_evidence_status": brand.status,
        "brand_evidence_note": "Conditional evidence audit; not a universal brand-fit or reputation score.",
    }
    brief_table = pd.DataFrame(
        [
            {"section": "Model disposition", "item": brief.disposition},
            {"section": "Headline", "item": brief.headline},
            *[{"section": "Decision trace", "item": item} for item in brief.reasons],
            *[{"section": "Required action", "item": item} for item in brief.required_actions],
            {"section": "Management decision", "item": management_decision},
            {"section": "Management rationale", "item": management_rationale.strip()},
        ]
    )
    metadata_table = pd.DataFrame([{"field": key, "value": value} for key, value in export_metadata.items()])
    export_tables = {
        "Decision brief": brief_table,
        "Metadata": metadata_table,
        "Criteria": gate.criteria,
        "Evidence gaps": gate.evidence_gaps,
        "Scenario economics": finance.scenarios,
        "Cash flows": finance.cash_flows,
        "Volume bridge": volume,
        "Risk register": risks.risks,
        "Brand evidence": brand.evidence,
        "Brand evidence gaps": brand.evidence_gaps,
        "Challenge": challenge_frame,
    }
    project_name = str(metadata.get("project_name", ""))
    safe_name = "".join(character if character.isalnum() else "-" for character in project_name.lower()).strip("-") or "project"
    download_cols = st.columns(3)
    full_width(
        download_cols[0].download_button,
        "Download Excel decision pack",
        data=results_to_excel(export_tables),
        file_name=f"gatesignal-{safe_name}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key=k("download_excel"),
    )
    full_width(
        download_cols[1].download_button,
        "Download CSV evidence pack",
        data=tables_to_csv_zip(export_tables),
        file_name=f"gatesignal-{safe_name}-csv.zip",
        mime="application/zip",
        key=k("download_csv"),
    )
    full_width(
        download_cols[2].download_button,
        "Download JSON decision pack",
        data=results_to_json(export_tables, export_metadata),
        file_name=f"gatesignal-{safe_name}.json",
        mime="application/json",
        key=k("download_json"),
    )


def page_methods() -> None:
    sig.header("Methods and limits", "Methods, limits, and primary references")
    tabs = st.tabs(["Decision architecture", "Criteria scoring", "Financial models", "Risk & challenge", "Limits & sources"])
    with tabs[0]:
        st.markdown(
            """
            Gate Signal uses a **decision-gate architecture**, not a proprietary workflow template. Work creates evidence;
            a review point decides whether to commit the next bounded resources. The app keeps six objects separate:

            1. declared preferences and hard constraints;
            2. evidence strength;
            3. conditional scenario economics;
            4. ordinal risk preparedness;
            5. brand-extension/alliance evidence and blockers; and
            6. the accountable management decision.

            This separation prevents a high average from concealing a failed safety or feasibility constraint and prevents
            weak evidence from being converted into a fake probability of success.
            """
        )
    with tabs[1]:
        st.markdown(
            """
            The preference score is a normalized additive multi-attribute score. It is useful when decision makers can
            defend the criteria, scales, and tradeoffs. Gate Signal does not claim that one point on every criterion has an
            objectively equal value.
            """
        )
        st.latex(r"S = \sum_{j=1}^{J} w_j s_j, \qquad \sum_j w_j = 1")
        st.latex(r"E = \sum_{j=1}^{J} w_j \frac{e_j}{3}")
        st.caption("S is the declared preference score. E is weighted evidence coverage. They are reported separately.")
    with tabs[2]:
        st.markdown(
            """
            Net present value is primary because it retains the size and timing of incremental cash flows. Expected NPV is
            a probability-weighted scenario summary; it is only as defensible as the scenarios and assigned probabilities.
            The discount rate is an explicit management input, not an estimate generated from hidden market data.
            """
        )
        st.latex(r"NPV_s = \sum_{t=0}^{T} \frac{CF_{s,t}}{(1+r)^t}")
        st.latex(r"E[NPV] = \sum_{s=1}^{S} p_s NPV_s, \qquad \sum_s p_s = 1")
        st.latex(r"Trials = M \times Awareness \times Availability \times TrialRate")
        st.caption("The volume bridge is transparent scenario arithmetic, not a calibrated simulated-test-market model.")
    with tabs[3]:
        st.markdown(
            """
            Probability and impact use 1–5 ordinal ratings. Their product is a triage convention, not expected loss: the
            distance between ratings is not known to be equal. High ratings therefore trigger response preparation rather
            than a claim of mathematical risk precision.

            The independent challenge checklist operationalizes outside-view evidence, disconfirming evidence, sunk-cost
            separation, reviewer independence, assumption ownership, and bounded learning. A checked box is not proof;
            the note makes the review inspectable.
            """
        )
    with tabs[4]:
        st.markdown(
            """
            ### Important limits

            - Gate Signal does not estimate demand, causal effects, cost of capital, technical feasibility, or safety.
            - Weighted scores can hide scale and preference errors; hard gates reduce but do not eliminate that risk.
            - Scenario probabilities are subjective unless supported by calibrated evidence.
            - NPV does not capture every strategic option, distributional effect, or non-financial obligation.
            - Risk matrices can mis-rank risks and should not replace quantitative risk analysis where data support it.
            - A `CONSIDER GO` result is not approval and does not authorize spending.

            ### Primary references

            - Cooper, R. G. (1990). Stage-gate systems: A new tool for managing new products. *Business Horizons, 33*(3), 44–54. [DOI](https://doi.org/10.1016/0007-6813(90)90040-I)
            - Cooper, R. G., Edgett, S. J., & Kleinschmidt, E. J. (1999). New product portfolio management: Practices and performance. *Journal of Product Innovation Management, 16*(4), 333–351. [DOI](https://doi.org/10.1016/S0737-6782(99)00005-3)
            - Edwards, W. (1977). How to use multiattribute utility measurement for social decisionmaking. *IEEE Transactions on Systems, Man, and Cybernetics, 7*(5), 326–340. [DOI](https://doi.org/10.1109/TSMC.1977.4309720)
            - Howard, R. A. (1966). Decision analysis: Applied decision theory. *Proceedings of the Fourth International Conference on Operational Research*.
            - Silk, A. J., & Urban, G. L. (1978). Pre-test-market evaluation of new packaged goods: A model and measurement methodology. *Journal of Marketing Research, 15*(2), 171–191. [DOI](https://doi.org/10.1177/002224377801500201)
            - Tversky, A., & Kahneman, D. (1974). Judgment under uncertainty: Heuristics and biases. *Science, 185*(4157), 1124–1131. [DOI](https://doi.org/10.1126/science.185.4157.1124)
            - Arkes, H. R., & Blumer, C. (1985). The psychology of sunk cost. *Organizational Behavior and Human Decision Processes, 35*(1), 124–140. [DOI](https://doi.org/10.1016/0749-5978(85)90049-4)

            Gate Signal's text, examples, interface, formulas, and implementation are independently written. No lecture
            slides, cases, classroom examples, assessment prompts, or proprietary gate templates are included.
            """
        )


PAGES = {
    "Welcome": page_welcome,
    "1 · Evidence & criteria": page_criteria,
    "2 · Economics & scenarios": page_economics,
    "3 · Risks & contingencies": page_risks,
    "4 · Decision & export": page_decision,
    "Methods & limits": page_methods,
}


# ── Sidebar and entry point ──────────────────────────────────────────────────
def _open_uploaded_project(uploaded) -> None:
    identity = (uploaded.name, int(getattr(uploaded, "size", 0)), str(getattr(uploaded, "file_id", "")))
    if st.session_state.get(k("upload_identity")) == identity:
        return
    try:
        loaded = load_project(uploaded)
        baseline = blank_project()
        merged = {**baseline, **{key: value for key, value in loaded.items() if key != "source_name"}}
        merged["metadata"] = {**baseline["metadata"], **dict(loaded.get("metadata", {}))}
        set_project(merged)
        st.session_state[k("upload_identity")] = identity
        st.session_state[k("upload_epoch")] = int(st.session_state[k("upload_epoch")]) + 1
        go_to("1 · Evidence & criteria")
        st.rerun()
    except Exception as exc:
        show_error(exc)


def _sidebar() -> str:
    """Draw the sidebar lockup, project controls and page selector; return the selected page."""
    sig.sidebar_brand(NS, SIDEBAR_TAGLINE)
    with st.sidebar:
        st.markdown("### Start with a project")
        if full_width(st.button, "Demo · LoopDose concept", key=k("load_demo")):
            set_project(demo_project())
            go_to("1 · Evidence & criteria")
            st.rerun()
        if full_width(st.button, "Start a blank project", key=k("load_blank")):
            set_project(blank_project())
            go_to("1 · Evidence & criteria")
            st.rerun()
        full_width(
            st.download_button,
            "Download project template",
            data=project_template(blank_project()),
            file_name="gatesignal-project-template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=k("download_template"),
        )
        uploaded = st.file_uploader(
            "Open a Gate Signal project",
            type=["xlsx", "json"],
            key=k(f"project_upload_{st.session_state[k('upload_epoch')]}"),
        )
        if uploaded is not None:
            _open_uploaded_project(uploaded)
        with st.expander("About the demo"):
            st.caption(
                "LoopDose is a fully fictional household-cleaning concept created for this repository. Its interviews, "
                "financials, risks, companies, and decisions are synthetic and must not be treated as market evidence."
            )
        project_name = str(_project()["metadata"].get("project_name", "Untitled concept"))
        st.caption(f"Current project: **{project_name}**")
        st.markdown("### Follow the review")
        # A navigation request (from a button) is applied before the radio exists, so its state may change.
        requested = st.session_state.pop(k("nav_request"), None)
        if requested in PAGES:
            st.session_state[k("page")] = requested
        if st.session_state.get(k("page")) not in PAGES:
            st.session_state[k("page")] = next(iter(PAGES))
        page = st.radio("Navigate", list(PAGES), key=k("page"), label_visibility="collapsed")
    return page


def render() -> None:
    """Draw the whole Gate Signal app on the current page. Never calls st.set_page_config or st.navigation."""
    sig.apply(NS)
    _ensure_state()
    page = _sidebar()
    sig.masthead(NS, MASTHEAD_PROMISES, MASTHEAD_KICKER)
    try:
        PAGES[page]()
    except Exception as exc:
        show_error(exc)
    sig.footer(NS, __version__, FOOTER_LINE)
