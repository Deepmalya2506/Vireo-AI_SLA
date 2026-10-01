from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict

import pandas as pd
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RAW_SUBDIR = DATA_DIR / "raw"
OUTPUT_DIR = BASE_DIR / "outputs"
IST = "Asia/Kolkata"

SLA_MINUTES = {
    "chat": 15,
    "voice": 120,
    "social": 240,
    "email": 480,
}

WEEKLY_VOLUME = 650
WEEKS_PER_QUARTER = 13
SLA_CREDIT_INR = 350


def resolve_data_dir() -> Path:
    required = [
        "tickets.csv",
        "agents.csv",
        "orders.csv",
        "customers.csv",
        "products.csv",
    ]

    for candidate in (RAW_SUBDIR, DATA_DIR):
        if all((candidate / name).exists() for name in required):
            return candidate

    raise FileNotFoundError(
        "Could not find the Vireo CSV pack. Put tickets.csv, agents.csv, "
        "orders.csv, customers.csv and products.csv in data/ or data/raw/."
    )


def get_shift(hour: int) -> str:
    if 6 <= hour < 14:
        return "Morning"
    if 14 <= hour < 22:
        return "Day"
    return "Night"


def canonicalize_tickets(tickets: pd.DataFrame) -> pd.DataFrame:
    """One row per ticket_id; migration duplicates prefer helpdesk."""
    out = tickets.copy()
    source_priority = {"helpdesk": 0, "legacy_fd": 1}
    out["_source_priority"] = out["source_system"].map(source_priority)

    if out["_source_priority"].isna().any():
        raise ValueError("Unexpected source_system value found.")

    out = (
        out.sort_values(["ticket_id", "_source_priority"])
        .drop_duplicates("ticket_id", keep="first")
        .drop(columns="_source_priority")
        .reset_index(drop=True)
    )

    legacy_zero = (
        (out["source_system"] == "legacy_fd")
        & (out["csat_score"] == 0)
    )
    out.loc[legacy_zero, "csat_score"] = pd.NA
    return out


def attach_roster(
    tickets: pd.DataFrame,
    agents: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.Series]:
    """Attach exactly one effective roster row to completed tickets."""
    roster = agents.copy()
    roster["from_date"] = pd.to_datetime(roster["from_date"]).dt.normalize()
    roster["to_date"] = pd.to_datetime(roster["to_date"]).dt.normalize()

    completed = tickets[
        tickets["status"].isin(["resolved", "closed"])
    ].copy()

    completed["resolved_date"] = (
        completed["resolved_at_ist"]
        .dt.tz_localize(None)
        .dt.normalize()
    )

    candidate = completed.merge(
        roster,
        on="agent_id",
        how="left",
        suffixes=("", "_roster"),
    )

    valid = candidate[
        (candidate["resolved_date"] >= candidate["from_date"])
        & (
            candidate["to_date"].isna()
            | (candidate["resolved_date"] <= candidate["to_date"])
        )
    ].copy()

    match_counts = valid["ticket_id"].value_counts()

    if (
        not (match_counts == 1).all()
        or len(valid) != completed["ticket_id"].nunique()
    ):
        missing = (
            completed["ticket_id"].nunique()
            - valid["ticket_id"].nunique()
        )
        multiple = int((match_counts > 1).sum())
        raise ValueError(
            f"Roster validation failed: missing matches={missing}, "
            f"multiple matches={multiple}."
        )

    return valid, match_counts


def build_analysis(data_dir: Path = DATA_DIR) -> Dict[str, object]:
    tickets_raw = pd.read_csv(data_dir / "tickets.csv")
    agents = pd.read_csv(data_dir / "agents.csv")

    for filename in ["orders.csv", "customers.csv", "products.csv"]:
        pd.read_csv(data_dir / filename)

    tickets = canonicalize_tickets(tickets_raw)

    for col in ["created_at", "first_response_at", "resolved_at"]:
        tickets[f"{col}_utc"] = pd.to_datetime(
            tickets[col], utc=True
        )

    tickets["created_at_ist"] = (
        tickets["created_at_utc"].dt.tz_convert(IST)
    )
    tickets["first_response_at_ist"] = (
        tickets["first_response_at_utc"].dt.tz_convert(IST)
    )
    tickets["resolved_at_ist"] = (
        tickets["resolved_at_utc"].dt.tz_convert(IST)
    )

    # Ticket-level timing context discovered during notebook analysis.
    tickets["arrival_hour"] = tickets["created_at_ist"].dt.hour
    tickets["arrival_shift"] = tickets["arrival_hour"].map(get_shift)
    tickets["response_hour"] = tickets["first_response_at_ist"].dt.hour
    tickets["response_shift"] = tickets["response_hour"].map(get_shift)

    tickets["response_minutes"] = (
        tickets["first_response_at_utc"]
        - tickets["created_at_utc"]
    ).dt.total_seconds() / 60

    tickets["sla_target_minutes"] = tickets["channel"].map(
        SLA_MINUTES
    )

    if tickets["sla_target_minutes"].isna().any():
        raise ValueError("Found a channel without an SLA target.")

    if (tickets["response_minutes"] < 0).any():
        raise ValueError("Found a negative first-response time.")

    # Policy: a breach occurs only when response time is later than target.
    tickets["breach"] = (
        tickets["response_minutes"]
        > tickets["sla_target_minutes"]
    )

    tickets["report_week"] = (
        tickets["created_at_ist"].dt.strftime("%G-W%V")
    )

    valid, match_counts = attach_roster(tickets, agents)

    # Tier 1 is the comparable population for agent/shift analysis.
    tier1 = valid[valid["tier"] == 1].copy()

    # ---------- Core summaries ----------
    channel = (
        tickets.groupby("channel")
        .agg(
            tickets=("ticket_id", "count"),
            breaches=("breach", "sum"),
            breach_rate=("breach", "mean"),
        )
        .reset_index()
    )
    channel["breach_rate"] *= 100

    total_breaches = int(tier1["breach"].sum())

    shift = (
        tier1.groupby("shift")
        .agg(
            tickets=("ticket_id", "count"),
            breaches=("breach", "sum"),
            breach_rate=("breach", "mean"),
        )
        .reset_index()
    )
    shift["breach_rate"] *= 100

    shift_contribution = shift.copy()
    shift_contribution["breach_share_pct"] = (
        shift_contribution["breaches"]
        / total_breaches
        * 100
    )

    shift_channel = (
        tier1.groupby(["shift", "channel"])
        .agg(
            tickets=("ticket_id", "count"),
            breaches=("breach", "sum"),
            breach_rate=("breach", "mean"),
        )
        .reset_index()
    )
    shift_channel["breach_rate"] *= 100

    weekly = (
        tickets.groupby("report_week")
        .agg(
            tickets=("ticket_id", "count"),
            breaches=("breach", "sum"),
            breach_rate=("breach", "mean"),
        )
        .reset_index()
    )
    weekly["breach_rate"] *= 100
    weekly["rolling_4wk"] = (
        weekly["breach_rate"].rolling(4).mean()
    )

    agent = (
        tier1.groupby(["shift", "agent_id"])
        .agg(
            tickets=("ticket_id", "count"),
            breaches=("breach", "sum"),
            breach_rate=("breach", "mean"),
        )
        .reset_index()
    )
    agent["breach_rate"] *= 100

    shift_breaches = agent.groupby("shift")["breaches"].transform(
        "sum"
    )
    agent["shift_breach_share_pct"] = (
        agent["breaches"] / shift_breaches * 100
    )

    team_shift = (
        tier1.groupby(["shift", "team"])
        .agg(
            tickets=("ticket_id", "count"),
            breaches=("breach", "sum"),
            breach_rate=("breach", "mean"),
        )
        .reset_index()
    )
    team_shift["breach_rate"] *= 100

    hourly = (
        tier1.groupby("arrival_hour")
        .agg(
            tickets=("ticket_id", "count"),
            breaches=("breach", "sum"),
            breach_rate=("breach", "mean"),
            median_response=("response_minutes", "median"),
        )
        .reset_index()
    )
    hourly["breach_rate"] *= 100

    arrival_summary = (
        tier1.groupby("arrival_shift")
        .agg(
            tickets=("ticket_id", "count"),
            breaches=("breach", "sum"),
            breach_rate=("breach", "mean"),
        )
        .reset_index()
    )
    arrival_summary["breach_rate"] *= 100

    arrival_contribution = arrival_summary.copy()
    arrival_contribution["breach_share_pct"] = (
        arrival_contribution["breaches"]
        / total_breaches
        * 100
    )

    flow = (
        tier1.groupby(["arrival_shift", "shift"])
        .agg(
            tickets=("ticket_id", "count"),
            breaches=("breach", "sum"),
            breach_rate=("breach", "mean"),
        )
        .reset_index()
    )
    flow["breach_rate"] *= 100

    response_flow = (
        pd.crosstab(
            tier1["arrival_shift"],
            tier1["response_shift"],
            normalize="index",
        )
        * 100
    ).reset_index()

    # ---------- Channel contribution ----------
    channel_contribution = (
        tickets.groupby("channel")
        .agg(
            tickets=("ticket_id", "count"),
            breaches=("breach", "sum"),
            breach_rate=("breach", "mean"),
        )
        .reset_index()
    )
    channel_contribution["breach_rate"] *= 100
    total_company_breaches = int(tickets["breach"].sum())
    channel_contribution["breach_share_pct"] = (
        channel_contribution["breaches"]
        / total_company_breaches
        * 100
    )

    # ---------- Timing diagnostic ----------
    night = tier1[tier1["arrival_shift"] == "Night"]
    non_night = tier1[tier1["arrival_shift"] != "Night"]

    night_rate = float(night["breach"].mean())
    non_night_rate = float(non_night["breach"].mean())
    night_excess = (
        len(night)
        * (night_rate - non_night_rate)
    )

    night_response_flow = pd.crosstab(
        tier1["arrival_shift"],
        tier1["response_shift"],
        normalize="index",
    ) * 100

    night_to_morning_response_pct = float(
        night_response_flow.loc["Night", "Morning"]
        if "Morning" in night_response_flow.columns
        else 0.0
    )

    morning_resolver = tier1[tier1["shift"] == "Morning"]
    night_to_morning_resolver_pct = (
        len(
            tier1[
                (tier1["arrival_shift"] == "Night")
                & (tier1["shift"] == "Morning")
            ]
        )
        / len(night)
        * 100
    )

    morning_from_night_pct = (
        len(
            tier1[
                (tier1["arrival_shift"] == "Night")
                & (tier1["shift"] == "Morning")
            ]
        )
        / len(morning_resolver)
        * 100
    )

    # ---------- Channel-mix test for Morning ----------
    # Question: if Morning had the same channel mix it actually has,
    # but each channel retained the Tier-1 overall channel breach rate,
    # what breach rate would we expect?
    tier1_channel_rate = tier1.groupby("channel")["breach"].mean()
    morning_channel_mix = (
        morning_resolver["channel"]
        .value_counts(normalize=True)
    )

    morning_expected_rate = float(
        sum(
            morning_channel_mix.get(ch, 0.0)
            * tier1_channel_rate.get(ch, 0.0)
            for ch in tier1_channel_rate.index
        )
    )

    morning_actual_rate = float(
        morning_resolver["breach"].mean()
    )

    morning_mix_detail = pd.DataFrame({
        "channel": sorted(tier1_channel_rate.index),
    })
    morning_mix_detail["morning_ticket_share_pct"] = (
        morning_mix_detail["channel"]
        .map(morning_channel_mix)
        .fillna(0)
        * 100
    )
    morning_mix_detail["tier1_channel_breach_rate_pct"] = (
        morning_mix_detail["channel"]
        .map(tier1_channel_rate)
        * 100
    )
    morning_mix_detail["expected_morning_breach_contribution_pct"] = (
        morning_mix_detail["morning_ticket_share_pct"] / 100
        * morning_mix_detail["tier1_channel_breach_rate_pct"]
    )

    morning_diagnostic = pd.DataFrame({
        "metric": [
            "Actual Morning resolver breach rate",
            "Expected Morning breach rate from channel mix",
            "Actual minus expected gap (percentage points)",
            "Night-created share of Morning-attributed tickets",
            "Night-created first responses occurring in Morning",
        ],
        "value": [
            morning_actual_rate * 100,
            morning_expected_rate * 100,
            (morning_actual_rate - morning_expected_rate) * 100,
            morning_from_night_pct,
            night_to_morning_response_pct,
        ],
    })

    # ---------- Financial impact ----------
    realized = tickets[
        tickets["breach"]
        & tickets["status"].isin(["resolved", "closed"])
    ]

    realized_breaches = len(realized)
    realized_credits = realized_breaches * SLA_CREDIT_INR

    projected_quarterly_credits = (
        WEEKLY_VOLUME
        * WEEKS_PER_QUARTER
        * float(tickets["breach"].mean())
        * SLA_CREDIT_INR
    )

    overall = pd.DataFrame({
        "metric": [
            "raw_rows",
            "unique_tickets",
            "duplicate_ticket_ids",
            "overall_breaches",
            "overall_breach_rate_pct",
            "realized_breaches_resolved_closed",
            "realized_sla_credits_inr",
            "projected_quarterly_credits_inr_at_650_week",
        ],
        "value": [
            len(tickets_raw),
            tickets["ticket_id"].nunique(),
            tickets_raw["ticket_id"].duplicated().sum(),
            int(tickets["breach"].sum()),
            float(tickets["breach"].mean() * 100),
            realized_breaches,
            realized_credits,
            projected_quarterly_credits,
        ],
    })

    # ---------- Validation records ----------
    independent_target = tickets["channel"].map(SLA_MINUTES)
    independent_breach = (
        tickets["response_minutes"] > independent_target
    )

    validation = pd.DataFrame({
        "check": [
            "1 row per canonical ticket",
            "No negative response times",
            "All tickets have SLA target",
            "All tickets have arrival shift",
            "All tickets with first response have response shift",
            "Independent SLA flags match",
            "Completed tickets have exactly one roster match",
            "No response occurs after resolution for completed tickets",
        ],
        "pass": [
            tickets["ticket_id"].is_unique,
            (tickets["response_minutes"] >= 0).all(),
            tickets["sla_target_minutes"].notna().all(),
            tickets["arrival_shift"].notna().all(),
            tickets.loc[
                tickets["first_response_at_ist"].notna(),
                "response_shift",
            ].notna().all(),
            (independent_breach == tickets["breach"]).all(),
            (match_counts == 1).all(),
            (
                valid["first_response_at_ist"]
                <= valid["resolved_at_ist"]
            ).all(),
        ],
    })

    business_case = pd.DataFrame({
        "metric": [
            "overall_breach_rate_pct",
            "weekly_operating_volume",
            "weeks_per_quarter",
            "sla_credit_per_breach_inr",
            "projected_quarterly_sla_credit_exposure_inr",
            "night_created_tier1_breach_rate_pct",
            "non_night_created_tier1_breach_rate_pct",
            "night_created_sample_tickets",
            "counterfactual_avoided_breaches_if_night_matched_non_night",
        ],
        "value": [
            tickets["breach"].mean() * 100,
            WEEKLY_VOLUME,
            WEEKS_PER_QUARTER,
            SLA_CREDIT_INR,
            projected_quarterly_credits,
            night_rate * 100,
            non_night_rate * 100,
            len(night),
            night_excess,
        ],
    })

    # Kept for backward compatibility with previous project versions.
    validation_sample = (
        tickets.groupby("channel", group_keys=False)
        .sample(n=8, random_state=42)
        [
            [
                "ticket_id",
                "channel",
                "created_at_ist",
                "first_response_at_ist",
                "response_minutes",
                "sla_target_minutes",
                "breach",
            ]
        ]
        .reset_index(drop=True)
    )

    return {
        "tickets_raw": tickets_raw,
        "tickets": tickets,
        "agents": agents,
        "valid": valid,
        "tier1": tier1,
        "match_counts": match_counts,
        "overall": overall,
        "channel": channel,
        "channel_contribution": channel_contribution,
        "shift": shift,
        "shift_contribution": shift_contribution,
        "shift_channel": shift_channel,
        "weekly": weekly,
        "agent": agent,
        "team_shift": team_shift,
        "hourly": hourly,
        "arrival_summary": arrival_summary,
        "arrival_contribution": arrival_contribution,
        "flow": flow,
        "response_flow": response_flow,
        "morning_mix_detail": morning_mix_detail,
        "morning_diagnostic": morning_diagnostic,
        "night_rate": night_rate,
        "non_night_rate": non_night_rate,
        "night_excess_breaches_sample": night_excess,
        "realized_breaches": realized_breaches,
        "realized_credits": realized_credits,
        "quarterly_projection": projected_quarterly_credits,
        "validation": validation,
        "business_case": business_case,
        "validation_sample": validation_sample,
    }


def save_outputs(
    d: Dict[str, object],
    output_dir: Path = OUTPUT_DIR,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    exports = {
        "ticket_sla.csv": d["tickets"],
        "channel_summary.csv": d["channel"],
        "channel_contribution.csv": d["channel_contribution"],
        "shift_summary.csv": d["shift"],
        "shift_contribution.csv": d["shift_contribution"],
        "shift_channel_summary.csv": d["shift_channel"],
        "weekly_summary.csv": d["weekly"],
        "agent_summary.csv": d["agent"],
        "team_shift_summary.csv": d["team_shift"],
        "hourly_risk.csv": d["hourly"],
        "arrival_summary.csv": d["arrival_summary"],
        "arrival_contribution.csv": d["arrival_contribution"],
        "arrival_to_response_shift.csv": d["response_flow"],
        "shift_flow_detail.csv": d["flow"],
        "morning_mix_detail.csv": d["morning_mix_detail"],
        "morning_diagnostic.csv": d["morning_diagnostic"],
        "overall_kpis.csv": d["overall"],
        "business_case.csv": d["business_case"],
        "validation_checks.csv": d["validation"],
        "manual_validation_sample.csv": d["validation_sample"],
    }

    for filename, frame in exports.items():
        frame.to_csv(output_dir / filename, index=False)


def redact_for_ai(text: str) -> str:
    text = re.sub(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        "[EMAIL]",
        text,
    )
    text = re.sub(
        r"\+?\d[\d\s().-]{8,}\d",
        "[PHONE]",
        text,
    )
    return text[:4000]


def ai_investigate(
    row: pd.Series,
) -> tuple[str, int | None, int | None]:
    """Groq is advisory only; deterministic SLA fields remain authoritative."""
    from groq import Groq

    load_dotenv(BASE_DIR / ".env")

    api_key = os.getenv("GROQ_API_KEY")
    model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Add it to .env before using "
            "the AI investigator."
        )

    client = Groq(api_key=api_key)

    prompt = f"""
The deterministic SLA engine has already calculated the SLA result.
Do NOT recalculate or override it.

You are assisting a support operations analyst. Using only the
supplied ticket text and metadata, identify plausible operational
factors associated with the delayed first response.

Do not invent facts. Clearly distinguish evidence from hypothesis.

Return exactly four sections:
1. Issue type
2. Evidence from customer text / agent note
3. Possible operational factor
4. Uncertainty / limitation

Ticket metadata:
Channel: {row["channel"]}
Priority: {row["priority"]}
Transfers: {row["transfers"]}
Arrival shift: {row["arrival_shift"]}
Response shift: {row["response_shift"]}
Response minutes: {row["response_minutes"]:.1f}
SLA target minutes: {row["sla_target_minutes"]:.1f}
Breach: {bool(row["breach"])}

Customer message:
{redact_for_ai(str(row["customer_message"]))}

Agent note:
{redact_for_ai(str(row["agent_notes"]))}
"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are a cautious support-operations analyst.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
        max_tokens=500,
    )

    content = (
        response.choices[0].message.content
        or "No response content returned."
    )

    usage = getattr(response, "usage", None)
    input_tokens = (
        getattr(usage, "prompt_tokens", None)
        if usage
        else None
    )
    output_tokens = (
        getattr(usage, "completion_tokens", None)
        if usage
        else None
    )

    return content, input_tokens, output_tokens


def run_pipeline() -> Dict[str, object]:
    data_dir = resolve_data_dir()
    result = build_analysis(data_dir)
    save_outputs(result)

    print(f"Input data: {data_dir}")
    print(f"Outputs:    {OUTPUT_DIR}")
    print(f"Canonical tickets: {len(result['tickets']):,}")
    print(
        "Overall breach rate: "
        f"{result['tickets']['breach'].mean() * 100:.2f}%"
    )

    print(
        "Morning resolver breach rate: "
        f"{result['morning_diagnostic'].loc[0, 'value']:.2f}%"
    )
    print(
        "Expected Morning rate from channel mix: "
        f"{result['morning_diagnostic'].loc[1, 'value']:.2f}%"
    )
    print(
        "Night-created Tier-1 breach rate: "
        f"{result['night_rate'] * 100:.2f}%"
    )

    return result


if __name__ == "__main__":
    run_pipeline()
