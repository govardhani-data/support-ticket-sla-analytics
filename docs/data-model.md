# Data Model — Support Ticket SLA Analysis

## Grain

The most important statement in this document:

- **`fact_ticket`** — one row per ticket.
- **`fact_ticket_assignment`** — one row per assignment event (each time a ticket
  arrives in a queue).

Every column in a table must describe that table's grain and nothing else.
Mixing grains causes silent double-counting.

## Schema shape

Star schema. Every dimension connects **directly** to a fact table. No dimension
connects to another dimension — that would be a snowflake, which creates
ambiguous join paths and slower models in Power BI.

```
                            dim_date
                                |
        dim_priority            |            dim_category
                   \            |            /
                    \           |           /
    dim_channel ------+---- fact_ticket ----+------ dim_assignment_group
                    /           |           \
                   /            |            \
        dim_region              |             dim_engineer
                                |
                         dim_root_cause


    fact_ticket ---< fact_ticket_assignment >--- dim_assignment_group
                                |
                          dim_engineer
```

Two fact tables sharing dimensions is called a **galaxy** (or constellation)
schema.

## Fact tables

### `fact_ticket` — grain: one ticket

| Column | Type | Notes |
|---|---|---|
| `ticket_key` | INT | Surrogate primary key |
| `ticket_id` | VARCHAR(20) | Business ID, e.g. INC0012345 |
| `created_date_key` | INT | FK → dim_date |
| `created_datetime` | DATETIME2 | |
| `first_response_datetime` | DATETIME2 | NULL if never responded |
| `resolved_datetime` | DATETIME2 | NULL if still open |
| `priority_key` | INT | FK → dim_priority |
| `category_key` | INT | FK → dim_category |
| `final_group_key` | INT | FK → dim_assignment_group |
| `engineer_key` | INT | FK → dim_engineer (resolver) |
| `channel_key` | INT | FK → dim_channel |
| `region_key` | INT | FK → dim_region (requester) |
| `root_cause_key` | INT | FK → dim_root_cause |
| `total_elapsed_minutes` | INT | Wall-clock: create → resolve |
| `hold_minutes` | INT | Time paused awaiting customer |
| `sla_adjusted_minutes` | INT | total_elapsed − hold |
| `first_response_minutes` | INT | |
| `lateral_reassignment_count` | INT | Same-tier handovers |
| `escalation_count` | INT | Tier increases (L1→L2→L3) |
| `max_tier_reached` | TINYINT | 1, 2 or 3 |
| `reopen_count` | INT | |
| `is_response_sla_met` | BIT | |
| `is_resolution_sla_met` | BIT | Based on sla_adjusted_minutes |
| `is_resolved` | BIT | |

### `fact_ticket_assignment` — grain: one assignment event

| Column | Type | Notes |
|---|---|---|
| `assignment_key` | INT | Surrogate primary key |
| `ticket_key` | INT | FK → fact_ticket |
| `assignment_seq` | INT | 1 = first queue, 2 = second... |
| `group_key` | INT | FK → dim_assignment_group |
| `engineer_key` | INT | FK → dim_engineer |
| `assigned_datetime` | DATETIME2 | |
| `left_datetime` | DATETIME2 | NULL if currently held |
| `minutes_in_group` | INT | |
| `is_escalation` | BIT | 1 = tier increased, 0 = lateral |

This table exists because a ticket reassigned four times has four events, and
four of anything cannot fit in a one-row-per-ticket table. It is what allows us
to identify *which* handover caused the delay, not merely that handovers
correlate with delay.

## Dimensions

### `dim_date`
`date_key`, `full_date`, `day_of_week`, `day_name`, `week_of_year`, `month`,
`month_name`, `quarter`, `year`, `is_weekend`, `is_holiday`

A dedicated date table lets us group by concepts SQL doesn't know (Indian public
holidays, working days) and is **mandatory** for Power BI time intelligence
functions to work.

### `dim_priority`
`priority_key`, `impact`, `urgency`, `priority_code`, `priority_name`,
`response_sla_minutes`, `resolution_sla_minutes`

Under ITIL, priority is not entered directly — it is derived from an
**impact × urgency** matrix. One row per combination. Response and resolution
are two separate SLA clocks with separate targets.

### `dim_category`
`category_key`, `category`, `subcategory`

### `dim_assignment_group`
`group_key`, `group_name`, `tier` (1/2/3), `region`, `shift_model`

### `dim_engineer`
`engineer_key`, `engineer_name`, `seniority`, `date_joined`

Used for workload and span-of-support analysis. Deliberately **not** used to
rank individuals by speed — on synthetic data that finding is meaningless, and
on real data it is an analysis that invites misuse.

### `dim_channel`
`channel_key`, `channel_name` — Phone, Email, Self-service portal,
Auto-generated alert

### `dim_region`
`region_key`, `region_name`, `timezone`

### `dim_root_cause`
`root_cause_key`, `root_cause_name` — Network Failure, Software Bug,
Configuration Error, User Error, Hardware Failure, Third-party Outage

## Why surrogate keys

Every dimension has an integer `_key` alongside its business value. Two reasons:

1. **Performance** — integer joins are faster than text joins.
2. **Stability** — business values change. If "Network Support" is renamed
   "Infrastructure Support" and we joined on the name, history breaks. The
   surrogate key stays constant while the label changes.

## SLA methodology — the hold-time decision

### The problem

| Event | Time |
|---|---|
| Opened | Monday 09:00 |
| Engineer responded | Monday 10:00 |
| Set to Awaiting Customer | Monday 11:00 |
| Customer replied | Wednesday 11:00 |
| Resolved | Wednesday 14:00 |

Total elapsed: **53 hours**. Time excluding customer wait: **5 hours**.
Against an 8-hour target, one of those is a breach and the other is not.

### The decision: calculate both

**`sla_adjusted_minutes`** excludes hold time. This is how Jira Service
Management, ServiceNow and Cherwell measure SLA, and it is the fair basis for
holding a support team accountable — they cannot control how fast a customer
replies. `is_resolution_sla_met` is based on this.

**`total_elapsed_minutes`** includes everything. This is what the customer
actually experienced. They waited 53 hours regardless of whose fault it was.

### Why reporting only the adjusted figure would be a mistake

Excluding hold time from the only reported metric hides customer pain, and it
creates an incentive to game: moving a ticket to "Awaiting Customer" stops the
clock. This is a well-documented behaviour in SLA-pressured support
organisations.

We therefore also track **hold ratio** (`hold_minutes / total_elapsed_minutes`)
per assignment group. Groups with unusually high hold ratios are flagged — not
as proof of gaming, but as a question worth asking.

## Note on data

This dataset is synthetic, produced by `src/generate_tickets.py`. No client or
production data has been used. The generator reflects behaviour patterns
observed across four years of enterprise application support.