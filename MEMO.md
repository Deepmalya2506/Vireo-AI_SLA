# To: Neha Kulkarni, Support Operations Manager
## Subject: First-response SLA breach analysis

### Headline
The supplied ticket export shows a **21.79% first-response SLA breach rate** after removing 616 migration/re-import duplicates. At Vireo's stated ~650 tickets/week and ₹350 credit per breached ticket, that corresponds to approximately **₹644,313 of quarterly SLA-credit exposure**.

### What the data show
The Tier-1 breach rate attributed to the resolving agent is 32.25% for Morning, versus 8.54% for Day and 10.59% for Night. Channel mix does not fully explain this difference: Morning remains substantially higher within Chat, Email and Social.

The strongest timing signal is overnight. Tier-1 tickets created during the 22:00–06:00 IST window breach at **65.72%**, versus **9.27%** for non-night arrivals. **83.18%** of Night-created Tier-1 tickets receive their first response during Morning, and 35.42% of Morning-attributed Tier-1 tickets were created during Night.

### What I would investigate first
Review overnight queue coverage and the Night-to-Morning handoff path, especially for Chat, Social and Email. The supplied export supports a strong association between overnight creation and later first response, but it does not contain complete queue/event history, so it cannot prove that a specific handoff caused an individual breach.

### What this means for agent conversations
The policy requires breach reporting against the resolving agent. Agent-level rates are therefore shown for operational follow-up, but the data should not be treated as proof of individual causation when a substantial share of the workload originated in a different shift.

### Business context
The dataset contains 2,320 resolved/closed breached tickets, corresponding to ₹812,000 of realized SLA credits. The 650 tickets/week figure is used only to scale the overall observed breach rate for a quarterly exposure scenario.

### Recommendation for next operational step
Pilot and measure an overnight/next-shift handoff intervention, then compare the Night-created breach rate before and after the change. Use the resulting measured reduction to set a real target rather than assuming a 15% overall rate in advance.
