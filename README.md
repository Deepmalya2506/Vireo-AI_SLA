# Vireo Audio | First-Response SLA Analysis

**A reproducible analysis and interactive dashboard for locating first-response SLA breaches, understanding when they occur, and identifying what Operations should investigate next.**

First response means the first human agent reply. The SLA result is calculated deterministically from ticket data. An optional Groq-powered investigator can summarize a selected ticket's text, but it does not set or change SLA outcomes.

latest-release: [prod_02](https://github.com/Deepmalya2506/Vireo-AI_SLA/releases/tag/prod_02)

## Executive summary

After removing migration duplicates, the supplied export contains **11,200 unique tickets** and **2,440 first-response breaches** (**21.79%**). The clearest concentration is in Tier-1 tickets created overnight: **65.72%** breached, compared with **9.27%** of non-night arrivals. This is a strong signal for investigation, not evidence that a specific shift, handoff, or agent caused a breach.

| Finding | Result |
| --- | ---: |
| Raw rows → canonical tickets | 11,816 → 11,200 |
| Duplicate ticket IDs removed | 616 |
| First-response breaches | 2,440 (21.79%) |
| Tier-1 resolver breach rate: Morning / Day / Night | 32.25% / 8.54% / 10.59% |
| Tier-1 arrival breach rate: Night / non-night | 65.72% / 9.27% |
| Night-created Tier-1 tickets first answered during Morning | 83.18% |

**Credit context:** 2,320 resolved or closed breached tickets correspond to **₹812,000** in credits in the supplied data. Separately, applying the observed overall rate to the stated operating volume of 650 tickets per week gives a **planning scenario of ₹644,312.50 per quarter** (650 × 13 × 21.79% × ₹350). This is a projection, not observed quarterly spend, and 650 tickets per week is not the sample's measured volume.

## What the dashboard covers

The Streamlit app presents six views:

- **Concentration:** breach contribution and rates by channel and operating group.
- **Timing & handoffs:** arrival hour, creation shift, response shift, and cross-shift flow.
- **Agents & teams:** resolver-attributed performance with Tier-1 comparisons kept separate from Tier-2.
- **Trend:** weekly rates for monitoring patterns over time.
- **Ticket investigator:** optional text-based context for one selected ticket.
- **Validation:** structural checks, independent recomputation results, and the generated validation report.

The main question is operational: **where should Support Operations investigate first?** The data point toward overnight coverage and the Night-to-Morning response path. The export does not include complete queue-event history, so it cannot establish the cause of an individual delay.

## How the analysis works

- Duplicate `ticket_id` records are canonicalized, preferring the `helpdesk` row over `legacy_fd`.
- Source timestamps are parsed as UTC and converted to IST for arrival, response, shift, and reporting views.
- First-response targets are channel based: chat **15 minutes**, voice **120 minutes**, social **240 minutes**, and email **480 minutes**.
- A breach means first response is **later than** the target; a response exactly at the target is not a breach.
- Completed-ticket agent and shift reporting follows the effective-dated roster assignment of the resolving agent, as required by the stated policy.
- Tier-1 is the comparable population for agent and shift rates; Tier-2 is not mixed into those comparisons.
- Legacy CSAT values of `0` are treated as missing survey responses.

## Data and privacy

The current repository checkout includes the five source CSVs under `vireo_sla/data/`: `tickets.csv`, `agents.csv`, `orders.csv`, `customers.csv`, and `products.csv`. The pipeline requires this complete pack and also supports placing it in `vireo_sla/data/raw/`.

These files contain customer and ticket information. Confirm authorization, repository visibility, and access controls before sharing or redistributing the repository. The optional investigator sends selected ticket context to Groq after basic email and phone-pattern redaction; that pattern-based redaction is not a guarantee of anonymization. Use the feature only when permitted by your data-handling requirements.

Generated artifacts are written to `vireo_sla/outputs/` when the pipeline runs. That directory is ignored by Git and is not needed as a separate input.

## Run locally

Run these commands from the repository root. Python dependencies are listed in `vireo_sla/requirements.txt`.

```powershell
python -m venv vireo_sla/.venv
.\vireo_sla\.venv\Scripts\Activate.ps1
python -m pip install -r vireo_sla/requirements.txt
python vireo_sla/main.py
streamlit run vireo_sla/app.py
```

On macOS or Linux, activate the environment with `source vireo_sla/.venv/bin/activate` instead. The pipeline reads the bundled input pack and regenerates the derived outputs before the dashboard uses them.

Run the independent validation and unit tests from the repository root:

```bash
python vireo_sla/tests/validation.py
```

```bash
cd vireo_sla
python -m pytest tests/test_main.py -q
```

The exploratory notebook is at `vireo_sla/notebooks/01_vireo_sla_analysis.ipynb`.

## Validation status

The current generated validation report records zero mismatches in the independent full-population comparison of the computed ticket fields, zero mismatches in its reproducible 32-ticket stratified code audit (8 per channel), and passing SLA boundary checks. This is computational validation against the supplied data; it is **not** a human review of 32 tickets.

## Optional ticket investigator

The core pipeline and dashboard do not require an API key. To enable the investigator, copy `vireo_sla/env.example` to `vireo_sla/.env` and set `GROQ_API_KEY`; `GROQ_MODEL` is optional. The `.env` file is ignored by Git. The model's response is advisory and is not used in KPI calculations or breach classification.

## Limitations

- The export lacks complete queue and handoff event history. Resolver attribution follows policy but is not proof of individual causation.
- The final ISO reporting week is partial; the export ends on 30 June 2026.
- The 650-ticket weekly volume is a stated operating assumption used only for the quarterly planning scenario.
- The Night versus non-night comparison and the estimate of about 1,235 fewer sample breaches if the Night-created Tier-1 rate matched the observed non-night rate are descriptive counterfactuals, not causal effects or forecasts.