# Vireo Audio — First-Response SLA Analyser

## What this project does

This project analyses Vireo Audio support-ticket data to determine where first-response SLA breaches are concentrated, with emphasis on weekly trends, resolver shift, channel, team and agent context.

The core SLA calculation is deterministic. The optional AI component is only used to investigate a selected ticket's free-text fields; it does **not** determine the SLA result.

## Business question

Neha Kulkarni asked for a weekly breach report by agent and shift so the support team can focus operational follow-up.

## Policy rules implemented

- Chat first response target: 15 minutes
- Voice callback: 2 hours
- Social: 4 hours
- Email: 8 hours
- SLA breach = first response later than target
- Breaches are reported against the resolving agent
- Tier-2 agents are not compared with Tier-1 on volume metrics
- Shifts are defined in IST: Morning 06:00–14:00, Day 14:00–22:00, Night 22:00–06:00
- Legacy CSAT `0` means no survey response and is treated as missing

## Data handling

The assessment pack contains personal/customer information, so the raw CSV files are intentionally **not committed to the public GitHub repository**.

Place the assessment files in `data/`:

```text
data/
├── tickets.csv
└── agents.csv
```

The dashboard's core analysis only requires these two files. The other assessment files remain available for notebook-side investigation when needed.

## Reproduction

Create and activate a virtual environment, then:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Run the notebook separately for the exploratory audit and reasoning trail.

## Current analytical findings

From the supplied assessment dataset:

- 11,816 raw ticket rows
- 616 duplicated ticket IDs created by migration/re-import
- 11,200 canonical tickets after deterministic deduplication
- 2,440 first-response breaches
- Overall first-response breach rate: **21.79%**
- Tier-1 Morning resolver breach rate: **32.25%**
- Tier-1 Day resolver breach rate: **8.54%**
- Tier-1 Night resolver breach rate: **10.59%**
- Night-created Tier-1 breach rate: **65.72%**
- Non-night Tier-1 breach rate: **9.27%**
- 83.18% of Night-created Tier-1 tickets received their first response during Morning
- 35.42% of Morning-attributed Tier-1 tickets were created during Night

These are descriptive observations. The export does not contain complete queue/event history, so the results should not be interpreted as proof that a specific handoff or individual caused each breach.

## Financial framing

Vireo's stated operating volume is approximately 650 tickets/week. This is **not** the volume represented by the supplied dataset; it is used only for a scenario projection.

Current projected quarterly SLA-credit exposure:

```text
650 tickets/week
× 13 weeks/quarter
× 21.79% observed breach rate
× ₹350 credit/breach
= ₹644,312.50 per quarter
```

Observed resolved/closed breached tickets in the supplied dataset: 2,320, corresponding to ₹812,000 of realized SLA credits.

A separate benchmark scenario shows that if Night-created Tier-1 tickets performed at the observed non-night Tier-1 breach rate, the supplied sample would contain about 1,235 fewer breaches. This is a counterfactual benchmark, not a forecast, and is not directly annualized to Vireo's 650/week volume because that would require additional assumptions about the Tier-1/night share of current production volume.

## Validation

The app performs structural checks and an independent recomputation of the deterministic SLA flag.

The notebook should also retain the fixed manual review sample of 8 tickets per channel. The submission should report the manual error rate only after those records have actually been checked.

## AI-assisted investigator

Set your own API credentials in the environment:

```text
OPENAI_API_KEY=<your key>
OPENAI_MODEL=<model available to your account>
```

The app uses the OpenAI Responses API for the optional ticket investigator. The model receives the selected ticket's structured context and redacted text, and is explicitly instructed not to recalculate or override the deterministic SLA result.

## Known limitations

1. The export attributes breaches to the resolving agent, as specified by policy, but does not provide the full first-response queue event history.
2. The final ISO week is partial because the export ends 30 June 2026.
3. The 650 tickets/week figure is a client-stated operating volume, not the sample's observed weekly average.
4. The AI investigation is advisory; it is not used for the KPI calculations.




----

Vireo Audio — Support SLA Analysis

A reproducible support-operations analysis for Vireo Audio's first-response SLA problem.

What it does

main.py is the processing/orchestration layer. It:

Loads the supplied assessment CSV pack from data/ or data/raw/.

Canonicalizes migration duplicates, preferring the helpdesk copy.

Parses API timestamps as UTC and creates IST views.

Applies Vireo policy SLA targets: chat 15 min, voice 120 min, social 240 min, email 480 min.

Calculates deterministic first-response breaches.

Maps completed tickets to the resolver's effective-dated roster assignment.

Produces weekly, shift, channel, team, agent, hourly and shift-handoff outputs.

Writes all derived CSVs to outputs/.

Generates a fixed 32-ticket manual-validation sample.

Provides an optional Groq ticket investigator; the LLM never determines SLA status.

app.py only renders the Streamlit UI and reads the outputs produced by main.py.

Input data

The five assessment CSVs are source inputs and therefore cannot be generated by the program. Keep the provided pack in either:

data/

or:

data/raw/

The program auto-detects either location.

Do not commit the raw CSVs to a public repository.

Run on a clean machine

python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
python main.py
streamlit run app.py

python main.py is the reproducible pipeline. It creates the outputs/ directory and all derived artifacts automatically.

Optional AI investigator (Groq)

Copy .env.example to .env and fill in GROQ_API_KEY. Optionally set GROQ_MODEL.

Current Groq documentation shows the official Python SDK using from groq import Groq, the GROQ_API_KEY environment variable, and client.chat.completions.create(...). The current supported-model catalogue lists openai/gpt-oss-20b as a production model. Costs vary by model; record the actual usage shown by the API for the submission.

Core analytical decisions

One canonical row per ticket_id; migration duplicates prefer helpdesk.

Missing values are interpreted by business meaning, not globally imputed.

CSAT 0 in legacy rows means no survey response and is excluded from CSAT averages.

SLA uses first human response minus ticket creation.

Breach is response_time > target (exactly at target is not a breach).

Breach attribution follows Vireo's policy: the resolving agent.

Tier 1 is the comparable population for agent/shift accountability; Tier 2 is reported separately.

Resolver shift is determined from the effective roster assignment at resolution.

Night/Morning findings are descriptive operational associations, not causal proof.

The source dataset contains ~11.2k canonical tickets; Vireo's ~650 tickets/week is used only for operating-volume projection.

Reproduction outputs

main.py generates:

ticket_sla.csv

weekly_summary.csv

shift_summary.csv

shift_channel_summary.csv

agent_summary.csv

team_shift_summary.csv

hourly_risk.csv

arrival_summary.csv

arrival_to_response_shift.csv

shift_flow_detail.csv

overall_kpis.csv

business_case.csv

validation_checks.csv

manual_validation_sample.csv

Scope deliberately excluded

No Spark/Databricks, MongoDB, Supabase, Oracle dependency, predictive ML model, encoder-decoder architecture, or deep-learning breach model is required for this dataset and question. These would add infrastructure without improving the core decision in the five-hour assessment window.