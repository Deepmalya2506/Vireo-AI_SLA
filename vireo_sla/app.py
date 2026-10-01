from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re
import streamlit as st

from main import ai_investigate
from ui_effects import apply_theme, render_topbar, render_pipeline


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"


st.set_page_config(
    page_title="Vireo | SLA Command Center",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_theme()          

# ============================================================
# DESIGN SYSTEM
# ============================================================
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');

:root {
    --navy: #071426;
    --navy-2: #0d2139;
    --royal: #162d52;
    --gold: #d8ad55;
    --gold-soft: #f0d79d;
    --ink: #172033;
    --muted: #667085;
    --paper: #f5f1e9;
    --card: #fffdf8;
    --line: #e8e0cf;
    --teal: #2e8b87;
    --red: #b95050;
    --green: #39765b;
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at 80% 0%, rgba(216,173,85,0.08), transparent 30%),
        linear-gradient(180deg, #071426 0%, #0b1d34 18%, #f5f1e9 18%, #f5f1e9 100%);
    color: var(--ink);
}

.block-container {
    padding: 1.4rem 3rem 3rem 3rem;
    max-width: 1500px;
}

[data-testid="stSidebar"] {
    background: #061121;
    border-right: 1px solid rgba(216,173,85,0.22);
}

[data-testid="stSidebar"] * {
    color: #edf1f7;
}

.hero {
    padding: 1.0rem 0 1.5rem 0;
    color: white;
}

.hero-kicker {
    color: var(--gold-soft);
    text-transform: uppercase;
    font-size: 0.76rem;
    letter-spacing: 0.16em;
    font-weight: 700;
}

.hero-title {
    font-family: 'Playfair Display', serif;
    font-size: 2.7rem;
    line-height: 1.05;
    margin: 0.25rem 0 0.35rem 0;
    color: white;
}

.hero-sub {
    color: #c8d2df;
    font-size: 1rem;
    max-width: 950px;
}

.question-bar {
    background: rgba(255,253,248,0.96);
    border: 1px solid rgba(216,173,85,0.45);
    border-left: 5px solid var(--gold);
    padding: 0.9rem 1rem;
    border-radius: 10px;
    margin: 0.2rem 0 1.2rem 0;
    color: var(--ink);
}

.card {
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: 1.1rem 1.15rem;
    box-shadow: 0 7px 25px rgba(7,20,38,0.07);
}

.card-dark {
    background: linear-gradient(145deg, #0a1b31, #102b4a);
    color: white;
    border: 1px solid rgba(216,173,85,0.24);
    border-radius: 14px;
    padding: 1.1rem 1.15rem;
    box-shadow: 0 10px 30px rgba(7,20,38,0.18);
}

.card-label {
    color: #7a8494;
    font-size: 0.74rem;
    text-transform: uppercase;
    letter-spacing: 0.10em;
    font-weight: 700;
}

.card-dark .card-label {
    color: #b7c4d3;
}

.card-number {
    color: var(--ink);
    font-size: 2rem;
    font-weight: 700;
    margin-top: 0.15rem;
}

.card-dark .card-number {
    color: white;
}

.card-detail {
    color: var(--muted);
    font-size: 0.83rem;
    line-height: 1.45;
    margin-top: 0.22rem;
}

.card-dark .card-detail {
    color: #cbd6e2;
}

.section-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.65rem;
    color: var(--navy);
    margin: 1.25rem 0 0.15rem 0;
}

.section-subtitle {
    color: var(--muted);
    font-size: 0.9rem;
    margin-bottom: 0.8rem;
}

.insight {
    background: #fffdf8;
    border: 1px solid var(--line);
    border-radius: 12px;
    padding: 0.95rem 1rem;
    height: 100%;
}

.insight strong {
    color: var(--navy);
}

.insight .number {
    color: var(--gold);
    font-size: 1.7rem;
    font-weight: 700;
}

.callout {
    background: #f8f3e8;
    border: 1px solid #e8d9b8;
    border-radius: 10px;
    padding: 0.9rem 1rem;
    color: #3d3527;
    line-height: 1.5;
}

.callout-red {
    background: #fbf1ef;
    border: 1px solid #e8c8c2;
}

.callout-blue {
    background: #edf4fb;
    border: 1px solid #cadbec;
}

.evidence-step {
    background: rgba(255,253,248,0.98);
    border: 1px solid var(--line);
    border-radius: 12px;
    padding: 0.85rem;
    min-height: 140px;
}

.step-no {
    color: var(--gold);
    font-weight: 700;
    letter-spacing: 0.08em;
    font-size: 0.75rem;
}

.step-title {
    color: var(--navy);
    font-weight: 700;
    font-size: 0.98rem;
    margin-top: 0.2rem;
}

.step-value {
    color: var(--navy);
    font-size: 1.45rem;
    font-weight: 700;
    margin: 0.25rem 0;
}

.step-text {
    color: var(--muted);
    font-size: 0.79rem;
    line-height: 1.45;
}

div[data-testid="stDataFrame"] {
    border-radius: 10px;
    overflow: hidden;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 0.15rem;
}

.stTabs [data-baseweb="tab"] {
    padding: 0.55rem 0.9rem;
}

.small-note {
    color: #7b8491;
    font-size: 0.77rem;
}

hr {
    border-color: var(--line);
}
</style>
""",
    unsafe_allow_html=True,
)

@st.cache_data
def load_outputs() -> dict[str, pd.DataFrame]:
    required_csvs = [
        "ticket_sla.csv",
        "channel_contribution.csv",
        "shift_summary.csv",
        "shift_contribution.csv",
        "shift_channel_summary.csv",
        "weekly_summary.csv",
        "agent_summary.csv",
        "team_shift_summary.csv",
        "hourly_risk.csv",
        "arrival_summary.csv",
        "arrival_contribution.csv",
        "arrival_to_response_shift.csv",
        "overall_kpis.csv",
        "business_case.csv",
        "morning_mix_detail.csv",
        "morning_diagnostic.csv",
        "validation_checks.csv",
        "validation_checks_independent.csv",
    ]
    required_files = [*required_csvs, "validation_report.txt"]

    missing = [
        name for name in required_files
        if not (OUTPUT_DIR / name).exists()
    ]

    if missing:
        raise FileNotFoundError(
            "Derived outputs are missing. Run `python main.py` first. "
            f"Missing: {', '.join(missing)}"
        )

    return {
        name[:-4]: pd.read_csv(OUTPUT_DIR / name)
        for name in required_csvs
    }


try:
    d = load_outputs()
except Exception as exc:
    st.error(str(exc))
    st.stop()


# ============================================================
# SIDEBAR — DECISION GUIDE
# ============================================================
with st.sidebar:
    st.markdown("### ◈ VIREO OPS")
    st.caption("First-response SLA command center")
    st.divider()

    st.markdown("**Decision question**")
    st.write(
        "Where is SLA leakage concentrated, and what evidence should "
        "Support Operations investigate first?"
    )

    st.markdown("**Evidence hierarchy**")
    st.caption("1. Deterministic SLA calculation")
    st.caption("2. Shift / timing comparison")
    st.caption("3. Channel-mix diagnostic")
    st.caption("4. Agent / team context")
    st.caption("5. AI ticket investigation")

    st.divider()
    st.markdown("**Data basis**")
    st.caption("11,200 canonical tickets")
    st.caption("Tier-1 used for resolver-shift analysis")
    st.caption("All timestamps converted from UTC to IST")
    st.caption("Final ISO week is partial")
    st.caption("Resolver attribution is policy-defined, not causal")

render_topbar()

# ============================================================
# HERO
# ============================================================
st.markdown(
    """
<div class="hero">
    <div class="hero-kicker">Support Operations Intelligence</div>
    <div class="hero-title">Where is the SLA leakage?</div>
    <div class="hero-sub">
        A decision-oriented view of Vireo Audio's first-response SLA problem:
        measure the exposure, locate the concentration, test competing explanations,
        then drill into agents and individual tickets.
    </div>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="question-bar">
    <strong>Client ask:</strong>
    Produce a weekly breach report by agent and shift so Support Operations knows
    where to investigate. This dashboard keeps that ask, but adds the evidence needed
    to interpret the agent/shift numbers without treating them as causal proof.
</div>
""",
    unsafe_allow_html=True,
)

# 3. Right after the "Client ask" question-bar block, before the KPI header
render_pipeline()

# ============================================================
# KPI HEADER
# ============================================================
overall = d["overall_kpis"].set_index("metric")["value"]

overall_breach_rate = float(overall["overall_breach_rate_pct"])
canonical_tickets = int(overall["unique_tickets"])
realized_credits = float(overall["realized_sla_credits_inr"])
quarterly_projection = float(
    overall["projected_quarterly_credits_inr_at_650_week"]
)

night_row = d["business_case"].set_index("metric")
night_rate = float(
    night_row.loc["night_created_tier1_breach_rate_pct", "value"]
)
non_night_rate = float(
    night_row.loc["non_night_created_tier1_breach_rate_pct", "value"]
)

k1, k2, k3, k4 = st.columns(4)

with k1:
    st.markdown(
        f"""
<div class="card-dark">
    <div class="card-label">Overall SLA breach</div>
    <div class="card-number">{overall_breach_rate:.2f}%</div>
    <div class="card-detail">2,440 breaches across {canonical_tickets:,} canonical tickets.</div>
</div>
""",
        unsafe_allow_html=True,
    )

with k2:
    st.markdown(
        f"""
<div class="card">
    <div class="card-label">Realized SLA credits</div>
    <div class="card-number">₹{realized_credits:,.0f}</div>
    <div class="card-detail">Observed on resolved/closed breached tickets in the supplied data.</div>
</div>
""",
        unsafe_allow_html=True,
    )

with k3:
    st.markdown(
        f"""
<div class="card">
    <div class="card-label">Planning exposure / quarter</div>
    <div class="card-number">₹{quarterly_projection:,.0f}</div>
    <div class="card-detail">650 tickets/week × 13 weeks × observed 21.79% breach × ₹350.</div>
</div>
""",
        unsafe_allow_html=True,
    )

with k4:
    st.markdown(
        f"""
<div class="card-dark">
    <div class="card-label">Night-created Tier-1</div>
    <div class="card-number">{night_rate:.2f}%</div>
    <div class="card-detail">vs {non_night_rate:.2f}% for non-night arrivals.</div>
</div>
""",
        unsafe_allow_html=True,
    )


# ============================================================
# EXECUTIVE READOUT
# ============================================================
st.markdown('<div class="section-title">Executive readout</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-subtitle">What the analysis says before you look at the charts.</div>',
    unsafe_allow_html=True,
)

r1, r2, r3 = st.columns(3)

with r1:
    st.markdown(
        """
<div class="insight">
    <div class="number">01</div>
    <strong>The problem is material.</strong><br><br>
    Vireo's sample contains 2,440 first-response breaches. At the stated operating
    volume, the observed rate maps to roughly ₹644k of quarterly SLA-credit exposure.
</div>
""",
        unsafe_allow_html=True,
    )

with r2:
    st.markdown(
        f"""
<div class="insight">
    <div class="number">02</div>
    <strong>Timing is the strongest concentration signal.</strong><br><br>
    Night-created Tier-1 tickets breach at <strong>{night_rate:.2f}%</strong> versus
    <strong>{non_night_rate:.2f}%</strong> for non-night arrivals.
</div>
""",
        unsafe_allow_html=True,
    )

with r3:
    st.markdown(
        """
<div class="insight">
    <div class="number">03</div>
    <strong>Agent numbers need context.</strong><br><br>
    The export attributes breaches to the resolver for reporting, but it does not
    contain complete queue/event history. Resolver rates are therefore accountability
    context, not proof of individual causation.
</div>
""",
        unsafe_allow_html=True,
    )


# ============================================================
# EVIDENCE CHAIN
# ============================================================
st.markdown('<div class="section-title">From symptom to operational signal</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-subtitle">Each step narrows the question instead of showing an isolated graph.</div>',
    unsafe_allow_html=True,
)

morning_diag = d["morning_diagnostic"].set_index("metric")["value"]
morning_actual = float(morning_diag["Actual Morning resolver breach rate"])
morning_expected = float(morning_diag["Expected Morning breach rate from channel mix"])
morning_gap = float(morning_diag["Actual minus expected gap (percentage points)"])
night_response_morning = float(morning_diag["Night-created first responses occurring in Morning"])
morning_from_night = float(morning_diag["Night-created share of Morning-attributed tickets"])

e1, e2, e3, e4 = st.columns(4)

evidence_cards = [
    (
        e1, "01", "Measure the symptom", f"{overall_breach_rate:.2f}%",
        "Overall first-response breach rate across canonical tickets."
    ),
    (
        e2, "02", "Locate the concentration", f"{night_rate:.2f}%",
        "Breach rate for Tier-1 tickets created during Night."
    ),
    (
        e3, "03", "Trace the timing", f"{night_response_morning:.2f}%",
        "Share of Night-created Tier-1 tickets first answered during Morning."
    ),
    (
        e4, "04", "Rule out one explanation", f"{morning_actual:.2f}% vs {morning_expected:.2f}%",
        f"Observed vs channel-mix-expected Morning rate; gap = {morning_gap:.2f} pp."
    ),
]

for col, no, title, value, text in evidence_cards:
    with col:
        st.markdown(
            f"""
<div class="evidence-step">
    <div class="step-no">{no}</div>
    <div class="step-title">{title}</div>
    <div class="step-value">{value}</div>
    <div class="step-text">{text}</div>
</div>
""",
            unsafe_allow_html=True,
        )


# ============================================================
# MAIN ANALYTICAL TABS
# ============================================================
tabs = st.tabs([
    "01 · Concentration",
    "02 · Timing & Handoffs",
    "03 · Agents & Teams",
    "04 · Trend",
    "05 · Ticket Investigator",
    "06 · Validation",
])


# ============================================================
# TAB 1 — CONCENTRATION
# ============================================================
with tabs[0]:
    st.markdown(
        '<div class="section-title">Where do the breaches come from?</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-subtitle">Start with contribution, then compare rates. A high rate alone does not tell you how much of the problem it represents.</div>',
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)

    with c1:
        ch = d["channel_contribution"].sort_values("breach_share_pct", ascending=True)
        fig = px.bar(
            ch,
            x="breach_share_pct",
            y="channel",
            orientation="h",
            text="breach_share_pct",
            hover_data=["tickets", "breaches", "breach_rate"],
            labels={
                "breach_share_pct": "Share of all breaches (%)",
                "channel": "Channel",
                "tickets": "Tickets",
                "breaches": "Breaches",
                "breach_rate": "Breach rate (%)",
            },
        )
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig.update_layout(
            title="Contribution by channel",
            xaxis_range=[0, max(35, float(ch["breach_share_pct"].max()) * 1.18)],
            height=390,
            margin=dict(l=10, r=30, t=60, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, width="stretch")

        st.markdown(
            """
<div class="callout">
<strong>What this tells us:</strong> channel is useful for locating volume and
breach rate, but it does not yet explain the shift pattern. Next we separate
arrival timing from resolver shift.
</div>
""",
            unsafe_allow_html=True,
        )

    with c2:
        ar = d["arrival_contribution"].sort_values("breach_share_pct", ascending=True)
        fig = px.bar(
            ar,
            x="breach_share_pct",
            y="arrival_shift",
            orientation="h",
            text="breach_share_pct",
            hover_data=["tickets", "breaches", "breach_rate"],
            labels={
                "breach_share_pct": "Share of Tier-1 breaches (%)",
                "arrival_shift": "Creation shift",
                "tickets": "Tier-1 tickets",
                "breaches": "Breaches",
                "breach_rate": "Breach rate (%)",
            },
        )
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig.update_layout(
            title="Contribution by ticket creation shift",
            xaxis_range=[0, 100],
            height=390,
            margin=dict(l=10, r=30, t=60, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, width="stretch")

        st.markdown(
            f"""
<div class="callout callout-red">
<strong>Key signal:</strong> Night-created tickets contribute
<strong>{float(ar.loc[ar['arrival_shift'].eq('Night'), 'breach_share_pct'].iloc[0]):.1f}%</strong>
of Tier-1 breaches in the supplied data, with a <strong>{night_rate:.2f}%</strong>
breach rate. This is a concentration signal, not a causal claim.
</div>
""",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    sc1, sc2 = st.columns([1.05, 0.95])

    with sc1:
        hm = d["shift_channel_summary"].pivot(
            index="shift",
            columns="channel",
            values="breach_rate",
        )
        fig_hm = px.imshow(
            hm,
            text_auto=".1f",
            aspect="auto",
            labels={
                "x": "Channel",
                "y": "Resolver shift",
                "color": "Breach rate (%)",
            },
            zmin=0,
            zmax=100,
        )
        fig_hm.update_layout(
            title="Resolver shift × channel breach rate",
            height=430,
            margin=dict(l=10, r=10, t=60, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_hm, width="stretch")

    with sc2:
        st.markdown(
            """
<div class="card">
<div class="card-label">How to read the heatmap</div>
<h4 style="margin:0.35rem 0 0.65rem 0;color:#071426;">Rate ≠ contribution</h4>
<p class="card-detail">
Each cell answers: "When this resolver shift handled this channel, what share
breached?" It does not answer how many total breaches came from that cell.
Use the contribution charts above alongside it.
</p>
<p class="card-detail">
The Morning pattern is visible across several channels, while voice has much
smaller volume. This is why channel-level rate and volume should be read together.
</p>
</div>
""",
            unsafe_allow_html=True,
        )

        st.dataframe(
            d["shift_summary"].round(2),
            width="stretch",
            hide_index=True,
        )


# ============================================================
# TAB 2 — TIMING
# ============================================================
with tabs[1]:
    st.markdown(
        '<div class="section-title">What happens around the shift boundary?</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-subtitle">This section tests whether the problem is aligned with when tickets arrive and when they first receive a response.</div>',
        unsafe_allow_html=True,
    )

    t1, t2 = st.columns(2)

    with t1:
        fig = px.line(
            d["hourly_risk"],
            x="arrival_hour",
            y="breach_rate",
            markers=True,
            labels={
                "arrival_hour": "Ticket creation hour (IST)",
                "breach_rate": "Breach rate (%)",
            },
            hover_data=[
                "tickets",
                "breaches",
                "median_response",
            ],
        )
        fig.add_vrect(
            x0=22,
            x1=23.99,
            fillcolor="rgba(216,173,85,0.16)",
            line_width=0,
        )
        fig.add_vrect(
            x0=0,
            x1=5.99,
            fillcolor="rgba(216,173,85,0.09)",
            line_width=0,
        )
        fig.update_layout(
            title="Breach risk by ticket arrival hour",
            height=420,
            margin=dict(l=10, r=10, t=60, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, width="stretch")

        st.markdown(
            """
<div class="callout">
<strong>What this tells us:</strong> the risk is concentrated in the overnight
arrival window, especially around 22:00–05:59 IST. This makes queue coverage,
handoff, and overnight backlog mechanics more relevant questions than simply
counting resolver-agent breaches.
</div>
""",
            unsafe_allow_html=True,
        )

    with t2:
        flow = d["arrival_to_response_shift"].set_index("arrival_shift")
        fig = px.imshow(
            flow,
            text_auto=".1f",
            aspect="auto",
            labels={
                "x": "First-response shift",
                "y": "Ticket creation shift",
                "color": "Share of tickets (%)",
            },
            zmin=0,
            zmax=100,
        )
        fig.update_layout(
            title="Where is the first response happening?",
            height=420,
            margin=dict(l=10, r=10, t=60, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, width="stretch")

        st.markdown(
            f"""
<div class="callout callout-blue">
<strong>What this tells us:</strong> <strong>{night_response_morning:.2f}%</strong>
of Night-created Tier-1 tickets receive their first response during Morning.
That does not prove the handoff caused the breach, but it gives operations a
specific queue/handoff mechanism to inspect.
</div>
""",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    m1, m2 = st.columns([1.15, 0.85])

    with m1:
        fig = px.bar(
            d["morning_mix_detail"],
            x="channel",
            y=[
                "morning_ticket_share_pct",
                "tier1_channel_breach_rate_pct",
            ],
            barmode="group",
            labels={
                "value": "Percent (%)",
                "channel": "Channel",
                "variable": "Measure",
            },
        )
        fig.update_layout(
            title="Morning composition vs channel-level baseline",
            height=390,
            margin=dict(l=10, r=10, t=60, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            legend_title_text="",
        )
        st.plotly_chart(fig, width="stretch")

    with m2:
        st.markdown(
            f"""
<div class="card-dark">
<div class="card-label">Channel-mix diagnostic</div>
<div class="card-number">{morning_actual:.2f}%</div>
<div class="card-detail">
Observed Morning resolver breach rate.
</div>
<br>
<div class="card-number" style="font-size:1.55rem;">{morning_expected:.2f}%</div>
<div class="card-detail">
Expected rate if Morning retained its actual channel mix but followed the
Tier-1 overall breach rate for each channel.
</div>
<br>
<div class="card-detail">
<strong>Gap: {morning_gap:.2f} percentage points.</strong>
Channel mix alone does not account for the full Morning rate in this
descriptive test.
</div>
</div>
""",
            unsafe_allow_html=True,
        )

    st.caption(
        "This standardization is a descriptive benchmark: it does not prove which "
        "operational mechanism creates the residual gap."
    )


# ============================================================
# TAB 3 — PEOPLE
# ============================================================
with tabs[2]:
    st.markdown(
        '<div class="section-title">What is happening at team and agent level?</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-subtitle">The client asked for agent/shift reporting. We retain it, but add volume and contribution context so a rate is not interpreted in isolation.</div>',
        unsafe_allow_html=True,
    )

    # Team heatmap
    team_hm = d["team_shift_summary"].pivot(
        index="team",
        columns="shift",
        values="breach_rate",
    )

    p1, p2 = st.columns([1.1, 0.9])

    with p1:
        fig = px.imshow(
            team_hm,
            text_auto=".1f",
            aspect="auto",
            labels={
                "x": "Resolver shift",
                "y": "Team",
                "color": "Breach rate (%)",
            },
            zmin=0,
            zmax=max(45, float(team_hm.max().max()) + 5),
        )
        fig.update_layout(
            title="Team × resolver shift breach rate",
            height=500,
            margin=dict(l=10, r=10, t=60, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, width="stretch")

    with p2:
        st.markdown(
            """
<div class="card">
<div class="card-label">Interpretation</div>
<h4 style="margin:0.35rem 0 0.65rem 0;color:#071426;">
Multiple Morning teams are elevated
</h4>
<p class="card-detail">
The pattern is not confined to one named team. That makes it more useful to
investigate the shared Morning operating context — arrival timing, queue coverage,
and handoff mechanics — before treating individual agents as the primary explanation.
</p>
<p class="card-detail">
Tier 2 is excluded from this agent/shift comparison because Vireo's policy says
Tier 2 is multi-touch and should not be compared with Tier 1 on volume metrics.
</p>
</div>
""",
            unsafe_allow_html=True,
        )

        st.markdown("### Agent context")

        agent_display = d["agent_summary"].copy()
        agent_display["rate_minus_shift_pct"] = (
            agent_display["breach_rate"]
            - agent_display.groupby("shift")["breach_rate"].transform("mean")
        )

        st.dataframe(
            agent_display.sort_values(
                ["shift", "breaches"],
                ascending=[True, False],
            )
            .round(2),
            width="stretch",
            hide_index=True,
        )

    st.markdown("---")

    # Agent scatter: factual positioning, no "worst" labels.
    scatter = d["agent_summary"].copy()
    scatter["label"] = scatter["agent_id"]

    fig = px.scatter(
        scatter,
        x="tickets",
        y="breach_rate",
        size="breaches",
        text="label",
        facet_col="shift",
        facet_col_wrap=3,
        hover_data=["agent_id", "breaches", "shift_breach_share_pct"],
        labels={
            "tickets": "Tier-1 tickets handled",
            "breach_rate": "Breach rate (%)",
            "breaches": "Breaches",
        },
    )
    fig.update_traces(textposition="top center")
    fig.update_layout(
        title="Agent volume × breach rate × breach count",
        height=600,
        margin=dict(l=10, r=10, t=65, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, width="stretch")

    st.markdown(
        """
<div class="callout">
<strong>How to use this view:</strong> high breach rate, high breach count, and
high share of shift breaches answer different questions. The dashboard does not
collapse them into a single score or label because the dataset does not contain
the full queue/event history needed for causal attribution.
</div>
""",
        unsafe_allow_html=True,
    )


# ============================================================
# TAB 4 — TREND
# ============================================================
with tabs[3]:
    st.markdown(
        '<div class="section-title">When did the problem move?</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-subtitle">Weekly view helps separate a persistent operating pattern from a one-off spike.</div>',
        unsafe_allow_html=True,
    )

    weekly = d["weekly_summary"].copy()

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=weekly["report_week"],
            y=weekly["breach_rate"],
            mode="lines+markers",
            name="Weekly breach rate",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=weekly["report_week"],
            y=weekly["rolling_4wk"],
            mode="lines",
            name="4-week rolling average",
        )
    )

    fig.update_layout(
        title="First-response SLA over time",
        yaxis_title="Breach rate (%)",
        xaxis_title="Report week",
        hovermode="x unified",
        height=500,
        margin=dict(l=10, r=10, t=60, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, width="stretch")

    st.markdown(
        """
<div class="callout">
<strong>What this tells us:</strong> the weekly chart is a monitoring view, not a
causal test. Use it to identify when the rate changed, then use the timing,
channel-mix, and shift analyses to investigate what changed operationally.
</div>
""",
        unsafe_allow_html=True,
    )

    st.dataframe(
        weekly.tail(12).round(2),
        width="stretch",
        hide_index=True,
    )

    st.caption(
        "The final ISO week is partial because the supplied source data ends on "
        "30 June 2026."
    )


# ============================================================
# TAB 5 — AI INVESTIGATOR
# ============================================================
with tabs[4]:
    st.markdown(
        '<div class="section-title">Investigate an individual ticket</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-subtitle">Use Groq to interpret ticket language and operational context after the deterministic SLA result is already known.</div>',
        unsafe_allow_html=True,
    )

    all_tickets = d["ticket_sla"]

    # Prefer a breached ticket in the default view so the demo immediately
    # shows why the investigator exists.
    breached_ids = all_tickets.loc[
        all_tickets["breach"] == True, "ticket_id"
    ].tolist()

    default_index = 0 if breached_ids else 0

    selected_ticket = st.selectbox(
        "Select a ticket",
        all_tickets["ticket_id"].tolist(),
        index=(
            all_tickets["ticket_id"].tolist().index(breached_ids[0])
            if breached_ids
            else default_index
        ),
    )

    row = all_tickets.loc[
        all_tickets["ticket_id"] == selected_ticket
    ].iloc[0]

    f1, f2 = st.columns([0.9, 1.1])

    with f1:
        facts = pd.DataFrame({
            "Field": [
                "SLA result",
                "Channel",
                "Priority",
                "Created (IST)",
                "First response (IST)",
                "Response time",
                "SLA target",
                "Arrival shift",
                "Response shift",
                "Transfers",
                "Resolver",
            ],
            "Value": [
                "BREACH" if bool(row["breach"]) else "ON TIME",
                row["channel"],
                row["priority"],
                str(row["created_at_ist"]),
                str(row["first_response_at_ist"]),
                f"{row['response_minutes']:.1f} min",
                f"{row['sla_target_minutes']:.0f} min",
                row["arrival_shift"],
                row["response_shift"],
                str(row["transfers"]),
                row["agent_id"],
            ],
        })

        st.dataframe(
            facts,
            width="stretch",
            hide_index=True,
        )

    with f2:
        st.markdown(
            f"""
<div class="card-dark">
<div class="card-label">Why the AI layer exists</div>
<div class="card-number" style="font-size:1.4rem;">
Deterministic KPI → qualitative investigation
</div>
<div class="card-detail">
The model receives the ticket text plus already-calculated SLA metadata.
It does not decide whether the ticket breached. Its job is to surface possible
issue types, textual evidence, plausible operational factors, and uncertainty.
</div>
</div>
""",
            unsafe_allow_html=True,
        )

    with st.expander("Show ticket text", expanded=False):
        st.markdown("**Customer message**")
        st.write(str(row["customer_message"]))
        st.markdown("**Agent notes**")
        st.write(str(row["agent_notes"]))

    if st.button(
        "Ask Groq to investigate this ticket",
        type="primary",
    ):
        try:
            with st.spinner("Calling Groq..."):
                answer, input_tokens, output_tokens = ai_investigate(row)

            st.markdown("### Investigation")
            st.markdown(answer)
            st.caption(
                f"API usage reported by provider: "
                f"input={input_tokens}, output={output_tokens} tokens."
            )
        except Exception as exc:
            st.error(f"AI investigator unavailable: {exc}")


# ============================================================
# TAB 6 — VALIDATION
# ============================================================
with tabs[5]:
    st.markdown(
        '<div class="section-title">Can we trust the deterministic result?</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-subtitle">Validation is part of the product, not an appendix.</div>',
        unsafe_allow_html=True,
    )

    # Read the independent validator's own machine-generated report so the UI
    # never hard-codes a validation result.
    validation_report = (OUTPUT_DIR / "validation_report.txt").read_text(
        encoding="utf-8"
    )

    breach_match = re.search(
        r"Full-population independent breach-flag mismatches:\s*(\d+)",
        validation_report,
    )
    audit_match = re.search(
        r"32-ticket stratified audit mismatches:\s*(\d+)/(\d+)",
        validation_report,
    )
    audit_rate_match = re.search(
        r"32-ticket audit error rate:\s*([0-9.]+)%",
        validation_report,
    )
    boundary_match = re.search(
        r"Boundary test passed:\s*(True|False)",
        validation_report,
    )

    breach_mismatches = int(breach_match.group(1)) if breach_match else None
    audit_mismatches = audit_match.group(1) if audit_match else None
    audit_denominator = audit_match.group(2) if audit_match else "32"
    audit_rate = audit_rate_match.group(1) if audit_rate_match else "N/A"
    boundary_pass = (
        boundary_match.group(1) == "True"
        if boundary_match
        else False
    )

    v1, v2, v3 = st.columns(3)

    with v1:
        st.markdown(
            f"""
<div class="card-dark">
<div class="card-label">Independent full-population check</div>
<div class="card-number">{breach_mismatches if breach_mismatches is not None else "N/A"}</div>
<div class="card-detail">
Breach-flag discrepancies across all {canonical_tickets:,} canonical tickets.
</div>
</div>
""",
            unsafe_allow_html=True,
        )

    with v2:
        st.markdown(
            f"""
<div class="card">
<div class="card-label">32-ticket independent audit</div>
<div class="card-number">{audit_rate}%</div>
<div class="card-detail">
{audit_mismatches if audit_mismatches is not None else "N/A"} mismatches across
{audit_denominator} fixed tickets (8 per channel).
</div>
</div>
""",
            unsafe_allow_html=True,
        )

    with v3:
        st.markdown(
            f"""
<div class="card">
<div class="card-label">Boundary rule</div>
<div class="card-number">{"PASS" if boundary_pass else "FAIL"}</div>
<div class="card-detail">
Exactly at SLA target = not a breach; one second beyond = breach.
</div>
</div>
""",
            unsafe_allow_html=True,
        )

    st.markdown("### Pipeline validation")
    st.dataframe(
        d["validation_checks"],
        width="stretch",
        hide_index=True,
    )

    st.markdown("### Independent validation audit")
    st.dataframe(
        d["validation_checks_independent"],
        width="stretch",
        hide_index=True,
    )

    with st.expander("Validation report"):
        st.code(validation_report, language="text")

    st.info(
        "For reproducibility, run `python tests/validation.py` after "
        "`python main.py`. The independent validator reconstructs the canonical "
        "ticket set and recomputes SLA, timing, and shift fields from the raw data."
    )


# ============================================================
# FOOTER
# ============================================================
st.markdown("---")
st.markdown(
    """
<div style="display:flex;justify-content:space-between;gap:1rem;align-items:center;">
    <div>
        <span style="font-weight:700;color:#071426;">Vireo Audio</span>
        <span style="color:#7b8491;"> · Support Operations Intelligence</span>
    </div>
    <div class="small-note">
        Deterministic SLA engine · reproducible outputs · optional Groq investigator
    </div>
</div>
""",
    unsafe_allow_html=True,
)
