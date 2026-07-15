from __future__ import annotations

import os

# Keep Streamlit/Arrow serialization stable on macOS. This must be set early.
os.environ.setdefault("ARROW_DEFAULT_MEMORY_POOL", "system")

import base64
import hashlib
import inspect
import platform
from pathlib import Path
import sys
import traceback

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from gatesignal import __version__
from gatesignal.decision import build_decision_brief
from gatesignal.errors import DataProblem, friendly_message
from gatesignal.examples import blank_project, demo_project
from gatesignal.finance import analyze_cash_flows, analyze_volume_bridge
from gatesignal.interop import read_trial_intention
from gatesignal.io import (
    load_project,
    project_template,
    results_to_excel,
    results_to_json,
    tables_to_csv_zip,
)
from gatesignal.risk import analyze_risks, challenge_completion, prepare_challenge
from gatesignal.scoring import score_gate


PAGES = [
    "Welcome",
    "1 · Evidence & criteria",
    "2 · Economics & scenarios",
    "3 · Risks & contingencies",
    "4 · Decision & export",
    "Methods & limits",
]
COLORS = {
    "ink": "#17322E",
    "deep": "#102C2A",
    "teal": "#173C3A",
    "coral": "#D95B40",
    "mint": "#83D2B4",
    "gold": "#F2C66D",
    "paper": "#F8F5ED",
    "muted": "#59716C",
}
CAUTION = (
    "**GateSignal structures a decision; it does not approve a project.** Scores express declared preferences, "
    "cash flows are conditional scenarios, and risk ratings are ordinal triage. The accountable gatekeepers remain "
    "responsible for the decision, the evidence, and the consequences."
)
mark_path = ROOT / "assets" / "gatesignal-mark.svg"
MARK_URI = (
    "data:image/svg+xml;base64," + base64.b64encode(mark_path.read_bytes()).decode("ascii")
    if mark_path.exists()
    else ""
)


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


st.set_page_config(page_title="GateSignal | New-product gate decisions", page_icon="◆", layout="wide")
st.markdown(
    """
    <style>
    :root {
        --gs-ink:#17322e; --gs-deep:#102c2a; --gs-teal:#173c3a;
        --gs-coral:#d95b40; --gs-mint:#83d2b4; --gs-gold:#f2c66d;
        --gs-paper:#f8f5ed; --gs-line:rgba(23,50,46,.14);
    }
    [data-testid="stAppViewContainer"] {
        background:radial-gradient(circle at 94% 2%,rgba(217,91,64,.14),transparent 28rem),
                   radial-gradient(circle at 2% 92%,rgba(242,198,109,.13),transparent 25rem),
                   linear-gradient(180deg,#fbf9f3 0%,var(--gs-paper) 100%);
    }
    [data-testid="stHeader"] { background:rgba(248,245,237,.78); }
    [data-testid="stSidebar"] { background:linear-gradient(165deg,#173c3a 0%,#102c2a 65%,#0c2422 100%); }
    [data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p,[data-testid="stSidebar"] label,[data-testid="stSidebar"] span { color:#f8f5ed; }
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p { color:#b9cbc5; }
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
        background:rgba(255,255,255,.06); border-color:rgba(242,198,109,.32);
    }
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] small,
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] small span { color:#b9cbc5 !important; }
    [data-testid="stSidebar"] [data-testid="stButton"] button {
        background:rgba(255,255,255,.08); color:#f8f5ed !important; border-color:rgba(255,255,255,.23);
    }
    [data-testid="stSidebar"] [data-testid="stButton"] button:hover {
        background:rgba(242,198,109,.14); border-color:rgba(242,198,109,.48);
    }
    [data-testid="stSidebar"] [data-testid="stButton"] button * { color:#f8f5ed !important; }
    [data-testid="stSidebar"] [data-testid="stDownloadButton"] button {
        background:rgba(255,255,255,.08); color:#f8f5ed !important; border-color:rgba(255,255,255,.23);
    }
    [data-testid="stSidebar"] [data-testid="stDownloadButton"] button:hover {
        background:rgba(242,198,109,.14); border-color:rgba(242,198,109,.48);
    }
    [data-testid="stSidebar"] [data-testid="stDownloadButton"] button * { color:#f8f5ed !important; }
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button {
        background:#f8f5ed; color:#17322e !important;
    }
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button * { color:#17322e !important; }
    .block-container { max-width:1240px; padding-top:4.4rem; padding-bottom:4rem; }
    h1,h2,h3 { color:var(--gs-ink); letter-spacing:-.025em; }
    a { color:#9b3e2b; }
    [data-testid="stMetric"] {
        background:rgba(255,255,255,.75); border:1px solid var(--gs-line); border-radius:16px;
        padding:1rem 1.05rem; box-shadow:0 8px 28px rgba(23,50,46,.045);
    }
    [data-testid="stMetricValue"] { color:var(--gs-ink); font-size:clamp(1.35rem,2.3vw,1.9rem); }
    .stButton > button[kind="primary"] {
        background:linear-gradient(135deg,#e26748,#c94c34); color:white; border:0;
        box-shadow:0 8px 20px rgba(217,91,64,.22); font-weight:750;
    }
    .stButton > button[kind="primary"]:hover { background:linear-gradient(135deg,#c94c34,#b63f2b); color:white; }
    button:focus-visible,a:focus-visible,input:focus-visible { outline:3px solid #f2c66d !important; outline-offset:2px; }
    [data-testid="stExpander"],[data-testid="stAlert"],[data-testid="stVerticalBlockBorderWrapper"] { border-radius:14px; }
    .gs-brand { padding:.25rem 0 1.1rem; }
    .gs-lockup { display:flex; align-items:center; gap:.65rem; }
    .gs-mark { width:38px; height:38px; }
    .gs-name { color:white; font-size:1.28rem; line-height:1; font-weight:850; letter-spacing:-.04em; }
    .gs-name span { color:#f2c66d !important; }
    .gs-tag { margin:.55rem 0 0 !important; color:#b9cbc5 !important; font-size:.77rem; line-height:1.4; }
    .gs-masthead {
        display:flex; justify-content:space-between; align-items:center; gap:1rem; padding:.72rem 1rem .72rem .78rem;
        margin-bottom:1.35rem; background:rgba(255,255,255,.65); border:1px solid var(--gs-line);
        border-radius:18px; box-shadow:0 10px 36px rgba(23,50,46,.05);
    }
    .gs-masthead .gs-mark { width:48px; height:48px; }
    .gs-wordmark { color:var(--gs-ink); font-weight:850; letter-spacing:-.045em; font-size:1.55rem; line-height:1; }
    .gs-wordmark span { color:var(--gs-coral); }
    .gs-kicker { margin-top:.32rem; color:#59716c; font-size:.67rem; font-weight:800; letter-spacing:.13em; }
    .gs-promise { color:#47645e; font-size:.78rem; font-weight:700; white-space:nowrap; }
    .gs-promise span { color:var(--gs-coral); padding:0 .3rem; }
    .gs-hero {
        position:relative; overflow:hidden; padding:clamp(1.7rem,4vw,3.4rem); margin-bottom:1.3rem;
        background:linear-gradient(135deg,#173c3a 0%,#102c2a 75%); border-radius:26px;
        box-shadow:0 18px 50px rgba(23,50,46,.17);
    }
    .gs-hero:after {
        content:""; position:absolute; width:330px; height:330px; right:-105px; top:-148px;
        border-radius:50%; border:56px solid rgba(217,91,64,.13);
    }
    .gs-eyebrow { color:#83d2b4; font-size:.72rem; font-weight:850; letter-spacing:.16em; }
    .gs-hero h1 { color:white; font-size:clamp(2.25rem,5vw,4.7rem); line-height:.97; margin:.75rem 0 1rem; max-width:960px; }
    .gs-hero h1 em { color:#f2c66d; font-style:normal; }
    .gs-hero p { color:#d7e3df; font-size:1.06rem; line-height:1.6; max-width:820px; }
    .gs-pills { display:flex; flex-wrap:wrap; gap:.55rem; margin-top:1.15rem; }
    .gs-pill {
        padding:.4rem .72rem; border:1px solid rgba(255,255,255,.16); border-radius:999px;
        color:#f8f5ed; font-size:.78rem; font-weight:700; background:rgba(255,255,255,.055);
    }
    .gs-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:1rem; }
    .gs-step,.gs-insight {
        height:100%; padding:1.2rem 1.2rem 1rem; background:rgba(255,255,255,.66);
        border:1px solid var(--gs-line); border-radius:18px;
    }
    .gs-step b,.gs-insight b { color:var(--gs-coral); font-size:.72rem; letter-spacing:.12em; }
    .gs-step h3,.gs-insight h3 { margin:.4rem 0 .5rem; }
    .gs-step p,.gs-insight p { color:#59716c; font-size:.9rem; line-height:1.55; }
    .gs-note {
        padding:1rem 1.1rem; margin:.75rem 0 1rem; border-left:4px solid var(--gs-mint);
        background:rgba(255,255,255,.62); border-radius:0 14px 14px 0; color:#47645e;
    }
    .gs-decision {
        padding:1.3rem 1.4rem; margin:1rem 0; color:white; border-radius:18px;
        background:linear-gradient(135deg,#173c3a,#102c2a); box-shadow:0 12px 34px rgba(23,50,46,.14);
    }
    .gs-decision b { color:#f2c66d; font-size:.78rem; letter-spacing:.14em; }
    .gs-decision h2 { color:white; margin:.35rem 0 .4rem; }
    .gs-decision p { color:#d7e3df; margin:0; }
    .gs-footer { margin-top:3.2rem; padding-top:1rem; border-top:1px solid var(--gs-line); color:#617670; font-size:.76rem; text-align:center; }
    .gs-footer span { color:var(--gs-coral); padding:0 .38rem; }
    @media (max-width:1050px) { .gs-grid{grid-template-columns:1fr} }
    @media (max-width:760px) { .gs-promise{display:none}.gs-hero{border-radius:20px}.block-container{padding-top:3.5rem} }
    @media (prefers-reduced-motion:reduce) { * { scroll-behavior:auto !important; transition:none !important; } }
    </style>
    """,
    unsafe_allow_html=True,
)


def show_error(exc: Exception) -> None:
    st.error(friendly_message(exc))
    if not isinstance(exc, (DataProblem, ValueError)) and os.getenv("GATESIGNAL_DEBUG") == "1":
        with st.expander("Technical details"):
            st.code("".join(traceback.format_exception(exc)))


def copy_project(project: dict[str, object]) -> dict[str, object]:
    copied: dict[str, object] = {}
    for key, value in project.items():
        copied[key] = value.copy(deep=True) if isinstance(value, pd.DataFrame) else dict(value) if isinstance(value, dict) else value
    return copied


def set_project(project: dict[str, object]) -> None:
    st.session_state["project"] = copy_project(project)
    for key in ["gate_summary", "finance_summary", "volume_results", "risk_summary", "challenge_score", "decision_brief"]:
        st.session_state.pop(key, None)
    st.session_state["project_epoch"] = int(st.session_state.get("project_epoch", 0)) + 1


def invalidate_from(section: str) -> None:
    mapping = {
        "criteria": ["gate_summary", "decision_brief"],
        "economics": ["finance_summary", "volume_results", "decision_brief"],
        "risk": ["risk_summary", "challenge_score", "decision_brief"],
    }
    for key in mapping[section]:
        st.session_state.pop(key, None)


def go_to(page_name: str) -> None:
    st.session_state["nav_target"] = page_name
    st.session_state["nav_epoch"] = int(st.session_state["nav_epoch"]) + 1


def masthead() -> None:
    image = f'<img class="gs-mark" src="{MARK_URI}" alt="GateSignal gate mark"/>' if MARK_URI else "◆"
    st.markdown(
        f"""
        <div class="gs-masthead"><div class="gs-lockup">{image}
        <div><div class="gs-wordmark">Gate<span>Signal</span></div><div class="gs-kicker">OPEN PRODUCT DECISION SUPPORT</div></div></div>
        <div class="gs-promise">Local-first <span>•</span> Traceable <span>•</span> Open source</div></div>
        """,
        unsafe_allow_html=True,
    )


def footer() -> None:
    st.markdown(
        f'<div class="gs-footer">GateSignal {__version__}<span>•</span>Decision support, not delegated judgment<span>•</span>AGPL-3.0-or-later</div>',
        unsafe_allow_html=True,
    )


def criteria_figure(summary) -> go.Figure:
    ordered = summary.criteria.sort_values("weighted_contribution")
    colors = [COLORS["coral"] if status == "Fail" else COLORS["mint"] for status in ordered["must_pass_status"]]
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
        title="Contribution to the weighted score",
        xaxis_title="Weighted points",
        yaxis_title=None,
        height=max(360, 46 * len(ordered)),
        margin=dict(l=20, r=20, t=60, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,.55)",
        font_color=COLORS["ink"],
    )
    return figure


def finance_figure(summary) -> go.Figure:
    colors = [COLORS["coral"] if value < 0 else COLORS["mint"] for value in summary.scenarios["npv"]]
    figure = go.Figure(
        go.Bar(
            x=summary.scenarios["scenario"],
            y=summary.scenarios["npv"],
            marker_color=colors,
            customdata=summary.scenarios[["probability", "irr", "discounted_payback"]],
            hovertemplate="%{x}<br>NPV %{y:,.0f}<br>Probability %{customdata[0]:.0%}<extra></extra>",
        )
    )
    figure.add_hline(y=0, line_color=COLORS["ink"], line_width=1)
    figure.update_layout(
        title="Scenario net present value",
        xaxis_title=None,
        yaxis_title="NPV",
        height=410,
        margin=dict(l=20, r=20, t=60, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,.55)",
        font_color=COLORS["ink"],
    )
    return figure


def volume_figure(frame: pd.DataFrame) -> go.Figure:
    figure = go.Figure()
    figure.add_bar(name="First-time trials", x=frame["scenario"], y=frame["first_time_trials"], marker_color=COLORS["gold"])
    figure.add_bar(name="Repeat units", x=frame["scenario"], y=frame["repeat_units"], marker_color=COLORS["mint"])
    figure.update_layout(
        barmode="stack",
        title="Assumption bridge to modeled units",
        yaxis_title="Units",
        height=410,
        margin=dict(l=20, r=20, t=60, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,.55)",
        font_color=COLORS["ink"],
        legend_orientation="h",
    )
    return figure


def risk_figure(summary) -> go.Figure:
    palette = {"Low": "#83D2B4", "Medium": "#F2C66D", "High": "#E88954", "Critical": "#D95B40"}
    figure = go.Figure()
    for band in ["Low", "Medium", "High", "Critical"]:
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
                marker=dict(size=30, color=palette[band], line=dict(color=COLORS["ink"], width=1)),
                customdata=subset[["risk", "owner", "response_ready"]],
                hovertemplate="%{customdata[0]}<br>Owner: %{customdata[1]}<br>Response ready: %{customdata[2]}<extra></extra>",
            )
        )
    figure.update_xaxes(range=[0.5, 5.5], dtick=1, title="Probability rating (ordinal)")
    figure.update_yaxes(range=[0.5, 5.5], dtick=1, title="Impact rating (ordinal)")
    figure.update_layout(
        title="Risk triage matrix",
        height=470,
        margin=dict(l=20, r=20, t=60, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,.55)",
        font_color=COLORS["ink"],
        legend_orientation="h",
    )
    return figure


def build_all_summaries() -> tuple[object, object, pd.DataFrame, object, float, object]:
    project = st.session_state["project"]
    metadata = project["metadata"]
    gate = score_gate(project["criteria"])
    finance = analyze_cash_flows(project["cash_flows"], float(metadata.get("discount_rate", 0.12)))
    volume = analyze_volume_bridge(project["volume_bridge"])
    risks = analyze_risks(project["risks"])
    challenge = challenge_completion(project["challenge"])
    brief = build_decision_brief(gate, finance, risks, challenge)
    st.session_state["gate_summary"] = gate
    st.session_state["finance_summary"] = finance
    st.session_state["volume_results"] = volume
    st.session_state["risk_summary"] = risks
    st.session_state["challenge_score"] = challenge
    st.session_state["decision_brief"] = brief
    return gate, finance, volume, risks, challenge, brief


for key, default in (
    ("project", None),
    ("project_epoch", 0),
    ("upload_epoch", 0),
    ("upload_identity", None),
    ("nav_target", PAGES[0]),
    ("nav_epoch", 0),
    ("management_decision", "Not decided"),
    ("management_rationale", ""),
):
    st.session_state.setdefault(key, default)
if st.session_state["project"] is None:
    set_project(blank_project())


with st.sidebar:
    mark = f"<img class='gs-mark' src='{MARK_URI}' alt='GateSignal mark'/>" if MARK_URI else "◆"
    st.markdown(
        f"<div class='gs-brand'><div class='gs-lockup'>{mark}<div class='gs-name'>Gate<span>Signal</span></div></div><p class='gs-tag'>Know when the evidence deserves the next investment.</p></div>",
        unsafe_allow_html=True,
    )
    st.markdown("### Start with a project")
    if full_width(st.button, "Demo · LoopDose concept", key="load_demo"):
        set_project(demo_project())
        go_to("1 · Evidence & criteria")
        st.rerun()
    if full_width(st.button, "Start a blank project", key="load_blank"):
        set_project(blank_project())
        go_to("1 · Evidence & criteria")
        st.rerun()
    blank_template = project_template(blank_project())
    full_width(
        st.download_button,
        "Download project template",
        data=blank_template,
        file_name="gatesignal-project-template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    uploaded = st.file_uploader(
        "Open a GateSignal project",
        type=["xlsx", "json"],
        key=f"project_upload_{st.session_state['upload_epoch']}",
    )
    if uploaded is not None:
        identity = (uploaded.name, int(getattr(uploaded, "size", 0)), str(getattr(uploaded, "file_id", "")))
        if st.session_state.get("upload_identity") != identity:
            try:
                loaded = load_project(uploaded)
                baseline = blank_project()
                merged = {**baseline, **{key: value for key, value in loaded.items() if key != "source_name"}}
                merged["metadata"] = {**baseline["metadata"], **dict(loaded.get("metadata", {}))}
                set_project(merged)
                st.session_state["upload_identity"] = identity
                st.session_state["upload_epoch"] += 1
                go_to("1 · Evidence & criteria")
                st.rerun()
            except Exception as exc:
                show_error(exc)
    with st.expander("About the demo"):
        st.caption(
            "LoopDose is a fully fictional household-cleaning concept created for this repository. Its interviews, "
            "financials, risks, companies, and decisions are synthetic and must not be treated as market evidence."
        )
    project_name = str(st.session_state["project"]["metadata"].get("project_name", "Untitled concept"))
    st.caption(f"Current project: **{project_name}**")
    st.markdown("### Follow the review")
    page = st.radio(
        "Page",
        PAGES,
        index=PAGES.index(st.session_state["nav_target"]),
        key=f"nav_radio_{st.session_state['nav_epoch']}",
        label_visibility="collapsed",
    )
    st.session_state["nav_target"] = page


masthead()
project = st.session_state["project"]
metadata = project["metadata"]


if page == "Welcome":
    st.markdown(
        """
        <section class="gs-hero">
          <div class="gs-eyebrow">NEW-PRODUCT GATE DECISIONS</div>
          <h1>Make the next investment <em>earn its way through.</em></h1>
          <p>GateSignal keeps customer evidence, strategic criteria, scenario economics, material risks, and independent
          challenge in one traceable decision pack. A polished average cannot hide a failed hard gate.</p>
          <div class="gs-pills"><span class="gs-pill">Must-pass checks</span><span class="gs-pill">Evidence strength</span>
          <span class="gs-pill">Scenario NPV</span><span class="gs-pill">Contingency triggers</span></div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    st.warning(CAUTION)
    st.markdown(
        """
        <div class="gs-grid">
          <div class="gs-step"><b>STEP 01</b><h3>Declare the case</h3><p>Write the decision, score explicit criteria, identify hard gates, and record what evidence actually supports each claim.</p></div>
          <div class="gs-step"><b>STEP 02</b><h3>Challenge the economics</h3><p>Keep downside, reference, and upside cash flows separate; calculate NPV; and expose the reach, trial, and repeat assumptions.</p></div>
          <div class="gs-step"><b>STEP 03</b><h3>Prepare the response</h3><p>Name material risks, owners, observable triggers, and executable actions before asking for an irreversible commitment.</p></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("### What GateSignal refuses to do")
    refusal_cols = st.columns(3)
    refusal_cols[0].markdown("**No fake success probability**\n\nPreference scores and evidence strength stay separate.")
    refusal_cols[1].markdown("**No sunk-cost rescue**\n\nPast spending does not enter forward NPV.")
    refusal_cols[2].markdown("**No automatic approval**\n\nThe model recommendation is a prompt for accountable review.")
    if st.button("Open the gate review →", type="primary"):
        go_to("1 · Evidence & criteria")
        st.rerun()


elif page == "1 · Evidence & criteria":
    st.title("Declare the decision and score the evidence")
    st.caption("Scores express preferences. Evidence strength expresses support. Hard gates remain non-compensatory.")
    basics = st.columns([1.2, 1.4, 1.0])
    project_name = basics[0].text_input("Project name", value=str(metadata.get("project_name", "")))
    decision_owner = basics[1].text_input("Accountable decision owner", value=str(metadata.get("decision_owner", "")))
    review_stage = basics[2].text_input("Review stage", value=str(metadata.get("review_stage", "")))
    decision_question = st.text_area(
        "Decision question",
        value=str(metadata.get("decision_question", "")),
        help="Write a bounded funding or commitment decision, not a general aspiration.",
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
    st.caption("Weights may use any positive scale; GateSignal normalizes them. Evidence: 0 none, 1 weak, 2 moderate, 3 strong.")
    edited = full_width(
        st.data_editor,
        project["criteria"],
        key=f"criteria_editor_{st.session_state['project_epoch']}",
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
    if st.button("Save criteria & score gate", type="primary", key="score_gate"):
        try:
            summary = score_gate(project["criteria"])
            st.session_state["gate_summary"] = summary
            st.session_state.pop("decision_brief", None)
        except Exception as exc:
            show_error(exc)
    summary = st.session_state.get("gate_summary")
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
        full_width(st.plotly_chart, criteria_figure(summary))
        with st.expander("Evidence gaps and normalized calculations", expanded=not summary.evidence_gaps.empty):
            if summary.evidence_gaps.empty:
                st.success("No criterion is currently marked with weak or absent evidence.")
            else:
                full_width(st.dataframe, summary.evidence_gaps, hide_index=True)
            full_width(st.dataframe, summary.criteria, hide_index=True)


elif page == "2 · Economics & scenarios":
    st.title("Challenge the volume and cash-flow story")
    st.warning(
        "These are conditional planning scenarios, not confidence intervals or forecasts. Scenario probabilities are judgments and must sum to 1."
    )
    controls = st.columns([1, 1, 2])
    currency = controls[0].text_input("Currency label", value=str(metadata.get("currency", "NOK")))
    rate_percent = controls[1].number_input(
        "Discount rate %",
        min_value=0.0,
        max_value=100.0,
        value=float(metadata.get("discount_rate", 0.12)) * 100,
        step=0.5,
    )
    controls[2].markdown(
        "<div class='gs-note'><b>Hurdle-rate discipline.</b> Enter the organization-approved project rate. GateSignal does not estimate a cost of capital from invented market inputs.</div>",
        unsafe_allow_html=True,
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
            key=f"volume_editor_{st.session_state['project_epoch']}",
            num_rows="dynamic",
            hide_index=True,
        )
        if not edited_volume.equals(project["volume_bridge"]):
            project["volume_bridge"] = edited_volume
            invalidate_from("economics")
        with st.expander("Import trial intention from ChoiceSignal"):
            st.caption(
                "ChoiceSignal's concept test exports a trial-intention JSON "
                "(schema `signal.trial-intention.v1`). Import it here to ground the trial rate in "
                "measured intent instead of a bare guess — the number stays an assumption, and its "
                "survey caveats travel with it."
            )
            intention_file = st.file_uploader(
                "ChoiceSignal trial-intention JSON",
                type=["json"],
                key=f"trial_intention_{st.session_state['project_epoch']}",
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
                    scenario_names = [
                        str(name).strip()
                        for name in project["volume_bridge"]["scenario"].tolist()
                        if str(name).strip()
                    ]
                    if not scenario_names:
                        st.warning("Add at least one named volume scenario above before applying the import.")
                    else:
                        apply_columns = st.columns([2, 2, 1])
                        chosen_value = apply_columns[0].radio(
                            "Value to apply",
                            ["Weighted estimate (recommended)", "Top-two-box ceiling"],
                            key="trial_intention_value",
                        )
                        chosen_scenario = apply_columns[1].selectbox(
                            "Apply to scenario", scenario_names, key="trial_intention_scenario"
                        )
                        if apply_columns[2].button("Apply", key="apply_trial_intention"):
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
                            st.session_state["project_epoch"] = int(st.session_state["project_epoch"]) + 1
                            st.rerun()
            if metadata.get("trial_intention_import"):
                st.caption(f"Imported: {metadata['trial_intention_import']}. Recorded in the project metadata and exports.")
    with cash_tab:
        st.caption("Enter incremental future project cash flows only. Period 0 normally contains the next investment as a negative number.")
        edited_cash = full_width(
            st.data_editor,
            project["cash_flows"],
            key=f"cash_editor_{st.session_state['project_epoch']}",
            num_rows="dynamic",
            hide_index=True,
        )
        if not edited_cash.equals(project["cash_flows"]):
            project["cash_flows"] = edited_cash
            invalidate_from("economics")
    if st.button("Analyze economics", type="primary", key="analyze_finance"):
        try:
            st.session_state["volume_results"] = analyze_volume_bridge(project["volume_bridge"])
            st.session_state["finance_summary"] = analyze_cash_flows(project["cash_flows"], metadata["discount_rate"])
            st.session_state.pop("decision_brief", None)
        except Exception as exc:
            show_error(exc)
    finance = st.session_state.get("finance_summary")
    volume = st.session_state.get("volume_results")
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
            full_width(st.plotly_chart, finance_figure(finance))
        with chart_cols[1]:
            full_width(st.plotly_chart, volume_figure(volume))
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


elif page == "3 · Risks & contingencies":
    st.title("Turn uncertainty into owned responses")
    st.caption("The 1–5 ratings are ordinal triage. They prioritize discussion; they are not calibrated event probabilities or expected losses.")
    risk_tab, challenge_tab = st.tabs(["Risk register", "Independent challenge"])
    with risk_tab:
        edited_risks = full_width(
            st.data_editor,
            project["risks"],
            key=f"risk_editor_{st.session_state['project_epoch']}",
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
    with challenge_tab:
        st.caption("A checked box needs a note that lets another reviewer understand what was actually done.")
        edited_challenge = full_width(
            st.data_editor,
            project["challenge"],
            key=f"challenge_editor_{st.session_state['project_epoch']}",
            num_rows="dynamic",
            hide_index=True,
            column_config={"completed": st.column_config.CheckboxColumn()},
        )
        if not edited_challenge.equals(project["challenge"]):
            project["challenge"] = edited_challenge
            invalidate_from("risk")
    if st.button("Review risks & contingencies", type="primary", key="analyze_risk"):
        try:
            st.session_state["risk_summary"] = analyze_risks(project["risks"])
            st.session_state["challenge_score"] = challenge_completion(project["challenge"])
            st.session_state.pop("decision_brief", None)
        except Exception as exc:
            show_error(exc)
    risks = st.session_state.get("risk_summary")
    challenge = st.session_state.get("challenge_score")
    if risks is not None and challenge is not None:
        metrics = st.columns(4)
        metrics[0].metric("High / critical risks", risks.high_or_critical)
        metrics[1].metric("Without complete response", risks.untreated_high_or_critical)
        metrics[2].metric("Contingency coverage", f"{risks.contingency_coverage:.0%}")
        metrics[3].metric("Challenge completed", f"{challenge:.0%}")
        if risks.untreated_high_or_critical:
            st.error("At least one high or critical risk lacks an owner, mitigation, observable trigger, or executable response.")
        full_width(st.plotly_chart, risk_figure(risks))
        with st.expander("Preparedness table", expanded=True):
            full_width(st.dataframe, risks.risks, hide_index=True)


elif page == "4 · Decision & export":
    st.title("Build the accountable decision brief")
    st.warning(CAUTION)
    if st.button("Build decision brief", type="primary", key="build_decision"):
        try:
            build_all_summaries()
        except Exception as exc:
            show_error(exc)
    brief = st.session_state.get("decision_brief")
    if brief is None:
        st.info("Build the brief when the criteria, economics, risks, and challenge record are ready.")
    else:
        st.markdown(
            f"<div class='gs-decision'><b>MODEL DISPOSITION</b><h2>{brief.disposition}</h2><p>{brief.headline}</p></div>",
            unsafe_allow_html=True,
        )
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
        current = st.session_state.get("management_decision", "Not decided")
        management_decision = record_cols[0].selectbox(
            "Accountable management decision",
            decision_options,
            index=decision_options.index(current) if current in decision_options else 0,
        )
        management_rationale = record_cols[1].text_area(
            "Decision rationale and conditions",
            value=st.session_state.get("management_rationale", ""),
            height=120,
        )
        st.session_state["management_decision"] = management_decision
        st.session_state["management_rationale"] = management_rationale
        if management_decision != "Not decided" and not management_rationale.strip():
            st.warning("Record why management accepted, changed, or rejected the model disposition before exporting.")

        gate = st.session_state["gate_summary"]
        finance = st.session_state["finance_summary"]
        volume = st.session_state["volume_results"]
        risks = st.session_state["risk_summary"]
        challenge_frame = prepare_challenge(project["challenge"])
        source_fingerprint = hashlib.sha256(
            project_template(project)
        ).hexdigest()
        export_metadata = {
            **metadata,
            "software": "GateSignal",
            "version": __version__,
            "python": platform.python_version(),
            "source_fingerprint_sha256": source_fingerprint,
            "model_disposition": brief.disposition,
            "management_decision": management_decision,
            "management_rationale": management_rationale.strip(),
            "decision_status": "Decision support; accountable management judgment required.",
            "score_status": "Weighted preference score; not a probability of success.",
            "risk_status": "Ordinal triage; not calibrated probability or expected loss.",
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
            "Challenge": challenge_frame,
        }
        safe_name = "".join(character if character.isalnum() else "-" for character in project_name.lower()).strip("-") or "project"
        download_cols = st.columns(3)
        full_width(
            download_cols[0].download_button,
            "Download Excel decision pack",
            data=results_to_excel(export_tables),
            file_name=f"gatesignal-{safe_name}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        full_width(
            download_cols[1].download_button,
            "Download CSV evidence pack",
            data=tables_to_csv_zip(export_tables),
            file_name=f"gatesignal-{safe_name}-csv.zip",
            mime="application/zip",
        )
        full_width(
            download_cols[2].download_button,
            "Download JSON decision pack",
            data=results_to_json(export_tables, export_metadata),
            file_name=f"gatesignal-{safe_name}.json",
            mime="application/json",
        )


else:
    st.title("Methods, limits, and primary references")
    tabs = st.tabs(["Decision architecture", "Criteria scoring", "Financial models", "Risk & challenge", "Limits & sources"])
    with tabs[0]:
        st.markdown(
            """
            GateSignal uses a **decision-gate architecture**, not a proprietary workflow template. Work creates evidence;
            a review point decides whether to commit the next bounded resources. The app keeps five objects separate:

            1. declared preferences and hard constraints;
            2. evidence strength;
            3. conditional scenario economics;
            4. ordinal risk preparedness; and
            5. the accountable management decision.

            This separation prevents a high average from concealing a failed safety or feasibility constraint and prevents
            weak evidence from being converted into a fake probability of success.
            """
        )
    with tabs[1]:
        st.markdown(
            """
            The preference score is a normalized additive multi-attribute score. It is useful when decision makers can
            defend the criteria, scales, and tradeoffs. GateSignal does not claim that one point on every criterion has an
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

            - GateSignal does not estimate demand, causal effects, cost of capital, technical feasibility, or safety.
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

            GateSignal's text, examples, interface, formulas, and implementation are independently written. No lecture
            slides, cases, classroom examples, assessment prompts, or proprietary gate templates are included.
            """
        )


footer()
