from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from main import ai_investigate


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"

st.set_page_config(page_title="Vireo SLA Analyser", layout="wide")
st.title("Vireo Audio — First-Response SLA Analyser")
st.caption("Precomputed deterministic SLA analysis with an optional Groq-powered ticket investigator.")


@st.cache_data
def load_outputs() -> dict[str, pd.DataFrame]:
    required = [
        "ticket_sla.csv",
        "channel_summary.csv",
        "shift_summary.csv",
        "shift_channel_summary.csv",
        "weekly_summary.csv",
        "agent_summary.csv",
        "team_shift_summary.csv",
        "hourly_risk.csv",
        "arrival_summary.csv",
        "arrival_to_response_shift.csv",
        "overall_kpis.csv",
        "business_case.csv",
        "validation_checks.csv",
        "manual_validation_sample.csv",
    ]
    missing = [name for name in required if not (OUTPUT_DIR / name).exists()]
    if missing:
        raise FileNotFoundError(
            "Derived outputs are missing. Run `python main.py` first. "
            f"Missing: {', '.join(missing)}"
        )

    return {name[:-4]: pd.read_csv(OUTPUT_DIR / name) for name in required}


try:
    d = load_outputs()
except Exception as exc:
    st.error(str(exc))
    st.stop()


# ---------- KPI cards ----------
overall = d["overall_kpis"]
metric_map = dict(zip(overall["metric"], overall["value"]))

c1, c2, c3, c4 = st.columns(4)
c1.metric("Overall breach rate", f"{metric_map['overall_breach_rate_pct']:.2f}%")
c2.metric("Canonical tickets", f"{int(metric_map['unique_tickets']):,}")
c3.metric("Realized SLA credits", f"₹{metric_map['realized_sla_credits_inr']:,.0f}")
c4.metric("Projected / quarter", f"₹{metric_map['projected_quarterly_credits_inr_at_650_week']:,.0f}")

st.divider()

# ---------- Weekly trend ----------
st.subheader("Weekly first-response SLA")
weekly = d["weekly_summary"]
fig = px.line(
    weekly,
    x="report_week",
    y=["breach_rate", "rolling_4wk"],
    markers=True,
    labels={"value": "Breach rate (%)", "report_week": "Week", "variable": "Series"},
)
fig.update_layout(legend_title_text="")
st.plotly_chart(fig, use_container_width=True)

# ---------- Shift / channel ----------
col1, col2 = st.columns(2)
with col1:
    st.subheader("Tier-1 shift performance")
    st.dataframe(d["shift_summary"].round(2), use_container_width=True, hide_index=True)

with col2:
    st.subheader("Tier-1 shift × channel")
    hm = d["shift_channel_summary"].pivot(
        index="shift", columns="channel", values="breach_rate"
    )
    fig_hm = px.imshow(
        hm,
        text_auto=".1f",
        aspect="auto",
        labels={"x": "Channel", "y": "Resolver shift", "color": "Breach rate (%)"},
        zmin=0,
        zmax=100,
    )
    st.plotly_chart(fig_hm, use_container_width=True)

# ---------- Timing ----------
st.subheader("Arrival timing")
col3, col4 = st.columns(2)
with col3:
    fig_arrival = px.line(
        d["hourly_risk"],
        x="arrival_hour",
        y="tickets",
        markers=True,
        labels={"arrival_hour": "Creation hour (IST)", "tickets": "Tickets created"},
    )
    st.plotly_chart(fig_arrival, use_container_width=True)

with col4:
    fig_risk = px.line(
        d["hourly_risk"],
        x="arrival_hour",
        y="breach_rate",
        markers=True,
        labels={"arrival_hour": "Creation hour (IST)", "breach_rate": "Breach rate (%)"},
    )
    st.plotly_chart(fig_risk, use_container_width=True)

# ---------- Handoff ----------
st.subheader("Arrival shift → first-response shift")
flow_pct = d["arrival_to_response_shift"].set_index("arrival_shift")
st.dataframe(flow_pct.round(2), use_container_width=True)

night_rate = float(metric_map.get("unused", 0))
night_row = d["business_case"].set_index("metric")
st.info(
    f"Night-created Tier-1 tickets breach at "
    f"{night_row.loc['night_created_tier1_breach_rate_pct', 'value']:.2f}% versus "
    f"{night_row.loc['non_night_created_tier1_breach_rate_pct', 'value']:.2f}% for non-night arrivals. "
    "This is an observed association, not proof that handoff caused each breach."
)

# ---------- Agent / team ----------
st.subheader("Tier-1 agent accountability context")
st.dataframe(
    d["agent_summary"].sort_values(["shift", "breaches"], ascending=[True, False]).round(2),
    use_container_width=True,
    hide_index=True,
)

st.subheader("Team context")
st.dataframe(
    d["team_shift_summary"].sort_values(["shift", "breaches"], ascending=[True, False]).round(2),
    use_container_width=True,
    hide_index=True,
)

# ---------- Validation ----------
st.subheader("Deterministic validation")
st.dataframe(d["validation_checks"], use_container_width=True, hide_index=True)
st.caption("The final ISO week is partial because the source data ends on 30 Jun 2026.")

st.subheader("Manual validation sample — 8 tickets per channel")
st.dataframe(d["manual_validation_sample"], use_container_width=True, hide_index=True)
st.caption("This is the fixed review sample generated by main.py. The manual error rate must be recorded after human checking.")

# ---------- AI investigator ----------
st.subheader("AI ticket investigator")
all_tickets = d["ticket_sla"]
selected_ticket = st.selectbox("Choose a ticket", all_tickets["ticket_id"].tolist())
row = all_tickets.loc[all_tickets["ticket_id"] == selected_ticket].iloc[0]

facts = pd.DataFrame(
    {
        "Field": [
            "Channel",
            "Priority",
            "Created (IST)",
            "First response (IST)",
            "Response time (min)",
            "SLA target (min)",
            "Breach",
            "Status",
            "Resolver",
        ],
        "Value": [
            row["channel"],
            row["priority"],
            str(row["created_at_ist"]),
            str(row["first_response_at_ist"]),
            f"{row['response_minutes']:.1f}",
            f"{row['sla_target_minutes']:.0f}",
            str(bool(row["breach"])),
            row["status"],
            row["agent_id"],
        ],
    }
)
st.dataframe(facts, use_container_width=True, hide_index=True)

if st.button("Ask Groq to investigate this ticket"):
    try:
        with st.spinner("Calling Groq..."):
            answer, input_tokens, output_tokens = ai_investigate(row)
        st.markdown(answer)
        st.caption(f"API usage: input={input_tokens}, output={output_tokens} tokens.")
    except Exception as exc:
        st.error(f"AI investigator unavailable: {exc}")
