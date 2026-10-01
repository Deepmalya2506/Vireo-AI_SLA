# Decision Log — Vireo Audio SLA Assessment

## Confirmed policy facts
- First response = first human agent reply, measured from ticket creation.
- SLA targets are channel-based: chat 15 min, voice callback 2 h, social 4 h, email 8 h.
- A breach is strictly `first_response_time > target`.
- Each breach issues a Rs 350 store credit on resolution.
- Breaches are reported against the resolving agent.
- Shifts are IST: Morning 06:00–14:00, Day 14:00–22:00, Night 22:00–06:00.
- Tier 2 agents are not to be compared with Tier 1 on volume metrics.

## Implementation decisions
- Canonicalize migration duplicates by `ticket_id`, preferring the `helpdesk` row when the same ticket also exists as `legacy_fd`.
- Keep the duplicate count as a QA metric rather than silently hiding it.
- Convert UTC timestamps to IST before week and roster analysis.
- Use Monday–Sunday as the reporting week; the policy does not define a week boundary, so this is an explicit assumption.
- Use the resolver's effective-dated roster assignment at resolution for final agent/shift attribution, because the policy says breaches are reported against the resolving agent.
- Exclude open/pending tickets from final agent/shift accountability because they have no completed resolution event. Keep them in the overall SLA KPI because they do have a recorded first response.
- Normalize legacy `csat_score = 0` to missing.
- Do not use refund/replacement costs as if they were SLA costs. The policy directly links an SLA breach to a Rs 350 SLA credit; refund/replacement costs are separate support economics.
- The supplied dataset is a historical sample of 11,200 unique tickets, while the client states roughly 650 tickets/week for current operating volume. Any quarterly money estimate must label 650/week as the client-provided projection volume.

## Initial observed baseline from the supplied data
- Raw ticket rows: 11,816
- Unique ticket IDs: 11,200
- Migration duplicate IDs: 616
- Overall first-response breach rate: 21.79%
- Overall breaches: 2,440
- Tier 1 completed tickets: 9,910? (see generated output for current run)
- Projected quarterly SLA credits at 650 tickets/week and current observed breach rate: about Rs 6.44 lakh
- Projected quarterly SLA credits at 15% breach rate: about Rs 4.44 lakh
- Difference: about Rs 2.01 lakh/quarter

These figures are baseline calculations only. The final business case should be finalized after QA, weekly trend analysis, and the validated agent/shift report.
