# Findings — Support Ticket SLA Analysis

Data as at 2025-12-31. 50,000 tickets, of which 48,733 resolved and 1,267 still
open. Overall SLA breach rate: **13.31%** (6,487 breaches).

---

## Headline findings

1. **40% of all breaches come from a coverage gap, not from difficulty.** Tickets
   arriving outside business hours at teams without out-of-hours cover breach at
   29.87%, against 8.15% in hours. Teams with 24x7 cover show no difference at
   all (7.64% vs 7.67%), which isolates coverage as the cause rather than the
   time of day.

2. **Tickets handed over two or more times are 20% of volume but cause 52% of
   breaches.** Risk doubles at the second handover and reaches 59% by the fourth.

3. **Problem type matters 18-fold.** Integration failures breach at 24.92%,
   password resets at 1.39%, on near-identical ticket volumes.

---

## Q1. What is the overall SLA breach rate, and how does it vary by priority?

**Answer: 13.31% overall. High-priority tickets breach more often than low, which
is the opposite of what most people expect.**

| Priority | SLA target | Tickets | % of volume | Breached | Breach rate | % of all breaches |
|---|---|---|---|---|---|---|
| P1 Critical | 240 min | 935 | 1.9% | 141 | 15.08% | 2.2% |
| P2 High | 480 min | 6,332 | 13.0% | 1,147 | 18.11% | 17.7% |
| P3 Medium | 1,440 min | 21,978 | 45.1% | 3,044 | 13.85% | 46.9% |
| P4 Low | 4,320 min | 19,488 | 40.0% | 2,155 | 11.06% | 33.2% |

**Why high priority fails more.** Breach depends on what share of the allowed
window a ticket consumes, not on absolute duration. Fixed overhead - noticing,
triaging, finding an available specialist - eats a large fraction of an
eight-hour target and a negligible fraction of a seventy-two-hour one.

**Rate and volume disagree.** P2 has the worst rate (18.11%). P3 has the worst
absolute impact - 3,044 breaches, 46.9% of the total - because it carries 45% of
volume. Improving P2 fixes the worst percentage; improving P3 reduces the largest
number of broken promises.

**Recommendation.** Review whether the eight-hour P2 target is achievable. A
target missed one time in five stops functioning as a commitment.

---

## Q2. Does reassignment count predict SLA breach, and at what point does risk jump?

Hypothesis from production support experience: every handover loses context and
restarts investigation. Expect a threshold, not a smooth increase.

**Answer: yes, and the threshold is the second handover.**

| Handovers | Tickets | Breached | Breach rate |
|---|---|---|---|
| 0 | 26,748 | 1,599 | 5.98% |
| 1 | 12,254 | 1,493 | 12.18% |
| 2 | 5,315 | 1,284 | 24.16% |
| 3 | 2,957 | 1,243 | 42.04% |
| 4 | 1,459 | 868 | 59.49% |

**Headline:** tickets handed over two or more times are 20.0% of volume but cause
52.3% of all breaches. Tickets with three or more handovers breach at 8.0 times
the rate of first-touch tickets.

**Where the threshold sits.** In percentage points the increases are +6.2, +12.0,
+17.9, +17.5. Risk doubles at the second handover and again by the third.

**A caution against over-reacting.** The breach counts are strikingly even across
groups: 1,599 / 1,493 / 1,284 / 1,243 / 868. First-touch tickets have the lowest
rate by far but the highest volume, so they still produce the largest single
block of breaches. Eliminating every handover would remove roughly half of all
breaches, not all of them.

**Recommendation.** The damage concentrates at the second handover, so the
intervention belongs at the front of the process: better initial categorisation
and routing. As an operational control, flag any ticket reaching its second
handover for team lead review.

---

## Q3. Which categories breach most, after adjusting for ticket volume?

**Answer: breach rates vary nearly 18-fold across problem types, from 24.92% on
integration failures to 1.39% on password resets.**

Ticket volume is near-identical across all fifteen subcategories (3,109 to 3,324),
so this ranking reflects difficulty rather than workload.

| Subcategory | Tickets | Breached | Breach rate |
|---|---|---|---|
| Integration Failure | 3,238 | 807 | 24.92% |
| Job Failure | 3,314 | 707 | 21.33% |
| Query Performance | 3,212 | 666 | 20.73% |
| Performance | 3,281 | 656 | 19.99% |
| Data Correction | 3,109 | 559 | 17.98% |
| Data Error | 3,271 | 548 | 16.75% |
| Firewall | 3,181 | 453 | 14.24% |
| Laptop | 3,265 | 443 | 13.57% |
| Connectivity | 3,251 | 391 | 12.03% |
| Account Provisioning | 3,278 | 292 | 8.91% |
| VPN | 3,282 | 277 | 8.44% |
| Permissions | 3,238 | 248 | 7.66% |
| Login / SSO | 3,324 | 219 | 6.59% |
| Peripheral | 3,248 | 176 | 5.42% |
| Password Reset | 3,241 | 45 | 1.39% |

**Rolled up:**

| Category | % of volume | % of all breaches | Breach rate |
|---|---|---|---|
| Database | 19.8% | 29.8% | 20.05% |
| Application | 26.9% | 34.4% | 17.00% |
| Network | 19.9% | 17.3% | 11.54% |
| Hardware | 13.4% | 9.5% | 9.50% |
| Access | 20.0% | 9.0% | 6.00% |

Database and Application together are 46.7% of volume but produce 64.2% of all
breaches. Access work is 20% of volume and 9% of breaches.

**Recommendation.** SLA targets are currently uniform across problem types, so a
password reset and an integration failure are held to the same standard. Either
set category-aware targets, or route high-difficulty categories directly to
specialists rather than through general triage.

---

## Q4. Is there a time-of-day, day-of-week or shift pattern in breaches?

**Answer: yes, and it is the single largest driver in this dataset. It is not
about when tickets arrive - it is about whether the receiving team is working.**

### By day of week

| Day | Tickets | Breach rate |
|---|---|---|
| Monday | 8,773 | 12.91% |
| Tuesday | 8,830 | 11.99% |
| Wednesday | 9,113 | 12.53% |
| Thursday | 8,793 | 11.59% |
| Friday | 8,792 | 12.56% |
| Saturday | 2,249 | 21.83% |
| Sunday | 2,183 | 24.69% |

Weekend volume is about a quarter of a weekday, but weekend breach rate is
roughly double.

### By hour of arrival

Breach rate holds between 8.4% and 9.9% for every hour from 09:00 to 17:00, then
jumps to between 18% and 25% for every hour outside that window. The transition
is abrupt at 09:00 and 18:00 - it is a step, not a gradient, which points at a
working-hours boundary rather than anything about the tickets themselves.

### The actual cause

| Team coverage | Ticket arrived | Tickets | Breached | Breach rate |
|---|---|---|---|---|
| 24x7 | Business hours | 10,451 | 798 | 7.64% |
| 24x7 | Out of hours | 5,749 | 441 | 7.67% |
| Business hours only | Business hours | 20,582 | 1,678 | 8.15% |
| Business hours only | Out of hours | 11,951 | 3,570 | 29.87% |

Teams with 24x7 cover act as a control group: they handle the same nights and
weekends and their breach rate does not move at all (7.64% vs 7.67%). Teams
without out-of-hours cover breach 3.7 times more often on tickets that arrive
outside their working window.

**Impact.** If out-of-hours tickets at business-hours-only teams performed like
their in-hours tickets, 2,596 fewer tickets would have breached - **40.0% of every
breach in the dataset**.

**Recommendation.** This is the cheapest lever available, because it requires a
rota change rather than a skills change. Options: extend cover for the two or
three highest-volume business-hours teams, route out-of-hours arrivals to the
24x7 service desk for holding action, or pause the SLA clock outside the
receiving team's contracted hours so the metric reflects what was actually
promised.

---

## Q5. Is the open backlog ageing?

**Answer: 1,267 tickets are open. Most are recent, but 210 of them - one in six -
have been open more than 90 days.**

| Age band | Open tickets | Share of backlog |
|---|---|---|
| 0-7 days | 163 | 12.9% |
| 8-30 days | 517 | 40.8% |
| 31-90 days | 377 | 29.8% |
| 91-180 days | 126 | 9.9% |
| Over 180 days | 84 | 6.6% |

| Priority | Open | Average age (days) | Oldest (days) | Open over 90 days |
|---|---|---|---|---|
| P1 | 26 | 84 | 738 | 4 |
| P2 | 156 | 66 | 1,002 | 23 |
| P3 | 569 | 86 | 1,022 | 106 |
| P4 | 516 | 87 | 1,069 | 77 |

**Why this question matters separately from the others.** Average resolution time
only counts tickets that closed. A team can report a healthy average while its
hardest tickets sit open indefinitely, because those never enter the average at
all. Backlog age is what exposes that.

**The concerning finding is not the volume, it is the tail.** 84 tickets have been
open more than six months, and 4 of them are P1 - tickets originally classified
as critical incidents. A P1 open for two years is not a critical incident any
more; it is a record nobody closed. That is a data hygiene problem as much as a
delivery one.

**Recommendation.** Introduce a backlog review at 90 days: close, re-prioritise or
escalate. Any P1 open beyond 30 days should be reviewed automatically, because
either the priority was wrong or the incident was never genuinely critical.

---

## Limitations

**The data is synthetic.** It was generated by `src/generate_tickets.py`. No
client or production data was used. Every behavioural parameter is an explicit
assumption set in one configuration block at the top of that script.

**Some findings are consequences of assumptions, not discoveries.** Category
difficulty and the out-of-hours penalty are inputs to the model. The analysis
quantifies their consequences; it cannot validate whether the input ratios are
correct. That would require real ticket data.

**Correlation is not cause.** On real data, tickets that are reassigned more may
simply be harder to begin with. Ticket complexity would need controlling for
before claiming that handovers cause breaches.

**Holidays are simplified.** Only fixed-date public holidays are modelled. Diwali,
Eid and other moving festivals are not, so working-day calculations around those
dates would be wrong.

**A small number of very old open tickets persist.** Four P1s open beyond two
years are an artefact of the backlog model, which allows a low constant
probability of a ticket remaining open indefinitely. Real ITSM systems usually
auto-close these.

---

## Method note

An earlier version of this dataset did not model category difficulty or shift
coverage. The Q3 and Q4 queries then returned differences smaller than random
variation at this sample size - no finding. Those null results are what prompted
adding both factors to the model. The sequence is documented here because
recognising a null result, understanding why it occurred, and correcting the
model is part of the work.