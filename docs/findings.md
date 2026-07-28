# Findings — Support Ticket SLA Analysis

> Status: questions defined, analysis not yet run.
> Answers will be filled in as each query is completed.

## The questions this project answers

### Q1. What is the overall SLA breach rate, and how does it vary by priority?
Baseline. Everything else is measured against this.
**Answer:** _pending_

### Q2. Does reassignment count predict SLA breach, and at what point does risk jump?
Hypothesis from four years of production support: every handover loses context
and restarts investigation. Expect a threshold rather than a smooth increase.
**Answer:** _pending_

### Q3. Which categories breach most, after adjusting for ticket volume?
Raw breach counts will simply rank the busiest categories. The real question is
which categories breach at a rate above their share of volume.
**Answer:** _pending_

### Q4. Is there a time-of-day, day-of-week, or shift pattern in breaches?
Tickets raised near a shift handover or late on Friday may be structurally
disadvantaged regardless of complexity.
**Answer:** _pending_

### Q5. Is the open backlog ageing over time?
MTTR only counts closed tickets, so a team can post a healthy MTTR while its
hardest tickets sit open indefinitely. Backlog age exposes what MTTR hides.
**Answer:** _pending_

## Definitions

- **SLA breach** — resolution time exceeded the target for that ticket's priority.
- **MTTR** — mean time to resolve, measured from creation to closure, closed tickets only.
- **Backlog age** — time elapsed since creation for tickets still open.
- **Reassignment count** — number of times a ticket changed assignment group.

## Note on data

This dataset is synthetic, produced by `src/generate_tickets.py`. No client or
production data has been used. The generator was designed to reflect behaviour
patterns observed across four years of enterprise application support.