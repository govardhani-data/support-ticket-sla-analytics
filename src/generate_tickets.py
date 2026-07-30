"""
generate_tickets.py

Builds the synthetic support ticket dataset:
  - fact_ticket             one row per ticket
  - fact_ticket_assignment  one row per assignment event

Data is synthetic. No client or production data is used.
Every behavioural parameter is an explicit assumption, set in the
CONFIGURATION block below, and can be changed without touching the logic.
"""

import random
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# CONFIGURATION - all behavioural assumptions live here
# ---------------------------------------------------------------------------

RANDOM_SEED = 42
random.seed(RANDOM_SEED)
rng = np.random.default_rng(RANDOM_SEED)

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"

TICKET_COUNT = 50_000
START = datetime(2023, 1, 1)
END = datetime(2025, 12, 31, 23, 59)

# Share of tickets at each priority level
PRIORITY_MIX = {"P1": 0.02, "P2": 0.13, "P3": 0.45, "P4": 0.40}

# Typical resolution time as a fraction of that priority's SLA target.
# Below 1.0 means most tickets are comfortably inside SLA.
#WORK_MEDIAN_VS_SLA = {"P1": 0.55, "P2": 0.60, "P3": 0.50, "P4": 0.40}
#WORK_MEDIAN_VS_SLA = {"P1": 0.40, "P2": 0.42, "P3": 0.35, "P4": 0.30}

WORK_MEDIAN_VS_SLA = {"P1": 0.27, "P2": 0.28, "P3": 0.24, "P4": 0.21}



# Spread of resolution times. Higher = longer tail of slow tickets.
#WORK_SPREAD = 0.75
WORK_SPREAD = 0.65

# How many times a ticket changes hands
REASSIGNMENT_MIX = {0: 0.55, 1: 0.25, 2: 0.11, 3: 0.06, 4: 0.03}

# Of all reassignments, share that are escalations (tier up)
# rather than lateral (wrong team first time)
ESCALATION_SHARE = 0.45

# How much longer work takes after N handovers. Non-linear on purpose:
# context loss compounds.
REASSIGNMENT_TIME_MULTIPLIER = {0: 1.0, 1: 1.4, 2: 2.1, 3: 3.2, 4: 4.5}

# Waiting on the customer
HOLD_PROBABILITY = 0.32
HOLD_MEDIAN_MINUTES = 480          # 8 hours
HOLD_SPREAD = 1.0

# First response, as a fraction of the response SLA target
RESPONSE_MEDIAN_VS_SLA = 0.50
RESPONSE_SPREAD = 0.8

REOPEN_ONCE_PROBABILITY = 0.06
REOPEN_TWICE_PROBABILITY = 0.01

#STILL_OPEN_SHARE = 0.03
# Business hours for teams that are not 24x7
BUSINESS_START_HOUR = 9
BUSINESS_END_HOUR = 18

# Work takes this much longer when a ticket lands with a business-hours-only
# team outside their working window - it waits for cover.
OUT_OF_HOURS_MULTIPLIER = 2.2

# Relative ticket volume by hour of day (0 to 23). Morning peak, quiet night.
HOURLY_ARRIVAL_WEIGHTS = [
    0.3, 0.2, 0.2, 0.2, 0.3, 0.5,      # 00-05  overnight
    1.0, 2.0, 3.5, 5.0, 4.5, 3.5,      # 06-11  morning ramp, peak at 09:00
    2.5, 3.0, 3.5, 3.2, 2.8, 2.2,      # 12-17  afternoon
    1.5, 1.0, 0.8, 0.6, 0.5, 0.4,      # 18-23  evening decline
]

# Chance a ticket is still open, by how old it is.
# Recent tickets are often still in progress; old ones rarely are.
BACKLOG_OPEN_RATES = [
    (30,  0.45),     # created in the last 30 days
    (90,  0.15),     # 31 to 90 days ago
    (180, 0.03),     # 91 to 180 days ago
]
BACKLOG_OLD_OPEN_RATE = 0.002   # older than 180 days

# Tickets are raised less on weekends
WEEKEND_VOLUME_FACTOR = 0.25

# Which channels tickets arrive through
CHANNEL_MIX = {
    "Phone": 0.20,
    "Email": 0.28,
    "Self-service Portal": 0.34,
    "Auto-generated Alert": 0.12,
    "Chat": 0.06,
}

REGION_MIX = {"India": 0.45, "Europe": 0.25, "US East": 0.22, "APAC": 0.08}

# Root cause depends loosely on category, so this is a simple overall mix
ROOT_CAUSE_MIX = {
    "Configuration Error": 0.20,
    "User Error": 0.19,
    "Software Bug": 0.17,
    "Network Failure": 0.12,
    "Hardware Failure": 0.09,
    "Third-party Outage": 0.08,
    "Capacity / Resource Limit": 0.07,
    "Change-related": 0.05,
    "Unknown / Not Reproducible": 0.03,
}

CATEGORY_DIFFICULTY = {
    "Connectivity":          0.95,
    "VPN":                   0.80,
    "Firewall":              1.15,
    "Login / SSO":           0.70,
    "Performance":           1.30,
    "Data Error":            1.20,
    "Integration Failure":   1.55,
    "Account Provisioning":  0.85,
    "Permissions":           0.75,
    "Password Reset":        0.40,
    "Laptop":                1.05,
    "Peripheral":            0.65,
    "Query Performance":     1.40,
    "Data Correction":       1.25,
    "Job Failure":           1.40,
}


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def pick(mix: dict):
    """Choose one key from a dict of {option: probability}."""
    options = list(mix.keys())
    weights = list(mix.values())
    return random.choices(options, weights=weights)[0]


def lognormal_minutes(median: float, spread: float) -> int:
    """
    A duration with a long right tail: most values near the median,
    a few much larger. This is how real task durations behave -
    a normal bell curve would be wrong here.
    """
    value = rng.lognormal(mean=np.log(median), sigma=spread)
    return max(1, int(value))


def is_out_of_hours(moment: datetime) -> bool:
    """True if this moment is outside Monday-Friday business hours."""
    if moment.isoweekday() >= 6:
        return True
    return moment.hour < BUSINESS_START_HOUR or moment.hour >= BUSINESS_END_HOUR


def still_open_probability(created: datetime) -> float:
    """Recent tickets are much more likely to still be open."""
    age_days = (END - created).days
    for cutoff, rate in BACKLOG_OPEN_RATES:
        if age_days <= cutoff:
            return rate
    return BACKLOG_OLD_OPEN_RATE


def random_created_datetime() -> datetime:
    """A random moment: quiet at weekends, with a morning peak on weekdays."""
    total_days = (END.date() - START.date()).days

    while True:
        day_offset = int(rng.integers(0, total_days + 1))
        day = START.date() + timedelta(days=day_offset)

        if day.isoweekday() >= 6 and random.random() > WEEKEND_VOLUME_FACTOR:
            continue

        hour = random.choices(range(24), weights=HOURLY_ARRIVAL_WEIGHTS)[0]
        minute = int(rng.integers(0, 60))
        return datetime(day.year, day.month, day.day, hour, minute)


# ---------------------------------------------------------------------------
# LOAD THE LOOKUP TABLES
# ---------------------------------------------------------------------------

def load_dimensions() -> dict:
    names = [
        "dim_priority", "dim_category", "dim_assignment_group",
        "dim_engineer", "dim_channel", "dim_region", "dim_root_cause",
    ]
    return {n: pd.read_csv(DATA_DIR / f"{n}.csv") for n in names}


# ---------------------------------------------------------------------------
# BUILD ONE TICKET
# ---------------------------------------------------------------------------

def build_ticket(ticket_num: int, dims: dict, lookups: dict) -> tuple:
    """Returns (ticket_row, list_of_assignment_rows)."""

    ticket_id = f"INC{ticket_num:07d}"
    created = random_created_datetime()

    # --- priority -----------------------------------------------------
    code = pick(PRIORITY_MIX)
    candidates = lookups["priority_by_code"][code]
    priority = random.choice(candidates)

    response_target = priority["response_sla_minutes"]
    resolution_target = priority["resolution_sla_minutes"]

    # --- descriptive attributes ---------------------------------------
    category = random.choice(lookups["categories"])
    channel = lookups["channel_by_name"][pick(CHANNEL_MIX)]
    region = lookups["region_by_name"][pick(REGION_MIX)]
    root_cause = lookups["root_cause_by_name"][pick(ROOT_CAUSE_MIX)]

    # --- how many handovers -------------------------------------------
    hops = pick(REASSIGNMENT_MIX)

    
    # --- which team picks it up first ---------------------------------
    chain = build_assignment_chain(hops, lookups)
    first_group = chain[0]["group"]

    # --- how long the actual work took --------------------------------
    base_work = lognormal_minutes(
        median=resolution_target
               * WORK_MEDIAN_VS_SLA[code]
               * CATEGORY_DIFFICULTY[category["subcategory"]],
        spread=WORK_SPREAD,
    )
    work_minutes = int(base_work * REASSIGNMENT_TIME_MULTIPLIER[hops])

    # A business-hours-only team cannot start until the next working day
    if first_group["shift_model"] != "24x7" and is_out_of_hours(created):
        work_minutes = int(work_minutes * OUT_OF_HOURS_MULTIPLIER)

    # --- waiting on the customer --------------------------------------
    if random.random() < HOLD_PROBABILITY:
        hold_minutes = lognormal_minutes(HOLD_MEDIAN_MINUTES, HOLD_SPREAD)
    else:
        hold_minutes = 0

    total_elapsed = work_minutes + hold_minutes

    # --- first response ------------------------------------------------
    first_response = lognormal_minutes(
        median=response_target * RESPONSE_MEDIAN_VS_SLA,
        spread=RESPONSE_SPREAD,
    )
    first_response = min(first_response, work_minutes)

    # --- reopens -------------------------------------------------------
    roll = random.random()
    if roll < REOPEN_TWICE_PROBABILITY:
        reopen_count = 2
    elif roll < REOPEN_TWICE_PROBABILITY + REOPEN_ONCE_PROBABILITY:
        reopen_count = 1
    else:
        reopen_count = 0

    # --- is it still open? ---------------------------------------------
   # still_open = random.random() < STILL_OPEN_SHARE
    still_open = random.random() < still_open_probability(created)
    resolved = None if still_open else created + timedelta(minutes=total_elapsed)

    # --- the chain of teams that handled it ----------------------------
    #chain = build_assignment_chain(hops, lookups)
    assignments = split_time_across_chain(
        chain, created, work_minutes, hold_minutes, lookups, still_open
    )

    lateral = sum(1 for a in assignments[1:] if a["is_escalation"] == 0)
    escalations = sum(1 for a in assignments[1:] if a["is_escalation"] == 1)
    max_tier = max(a["tier"] for a in assignments)

    ticket = {
        "ticket_id": ticket_id,
        "created_date_key": int(created.strftime("%Y%m%d")),
        "created_datetime": created,
        "first_response_datetime": created + timedelta(minutes=first_response),
        "resolved_datetime": resolved,
        "priority_key": priority["priority_key"],
        "category_key": category["category_key"],
        "final_group_key": assignments[-1]["group_key"],
        "engineer_key": assignments[-1]["engineer_key"],
        "channel_key": channel["channel_key"],
        "region_key": region["region_key"],
        "root_cause_key": None if still_open else root_cause["root_cause_key"],
        "total_elapsed_minutes": None if still_open else total_elapsed,
        "hold_minutes": None if still_open else hold_minutes,
        "sla_adjusted_minutes": None if still_open else work_minutes,
        "first_response_minutes": first_response,
        "lateral_reassignment_count": lateral,
        "escalation_count": escalations,
        "max_tier_reached": max_tier,
        "reopen_count": reopen_count,
        "is_response_sla_met": int(first_response <= response_target),
        "is_resolution_sla_met": None if still_open else int(work_minutes <= resolution_target),
        "is_resolved": int(not still_open),
    }

    return ticket, assignments


def build_assignment_chain(hops: int, lookups: dict) -> list:
    """Which teams touched this ticket, in order."""
    by_tier = lookups["groups_by_tier"]

    current = random.choice(by_tier[1])
    chain = [{"group": current, "is_escalation": 0}]
    tier = 1

    for _ in range(hops):
        escalate = random.random() < ESCALATION_SHARE and tier < 3

        if escalate:
            tier += 1
            nxt = random.choice(by_tier[tier])
            chain.append({"group": nxt, "is_escalation": 1})
        else:
            same_tier = [g for g in by_tier[tier] if g["group_key"] != chain[-1]["group"]["group_key"]]
            nxt = random.choice(same_tier) if same_tier else chain[-1]["group"]
            chain.append({"group": nxt, "is_escalation": 0})

    return chain


def split_time_across_chain(chain, created, work_minutes, hold_minutes,
                            lookups, still_open) -> list:
    """Divide the elapsed time between the teams that held the ticket."""
    n = len(chain)
    shares = rng.dirichlet(np.ones(n))       # random split that sums to 1
    total = work_minutes + hold_minutes

    rows = []
    cursor = created

    for i, (link, share) in enumerate(zip(chain, shares), start=1):
        minutes = max(1, int(total * share))
        left = None if (still_open and i == n) else cursor + timedelta(minutes=minutes)

        rows.append({
            "ticket_id": None,                      # filled in by the caller
            "assignment_seq": i,
            "group_key": link["group"]["group_key"],
            "tier": link["group"]["tier"],
            "engineer_key": random.choice(lookups["engineer_keys"]),
            "assigned_datetime": cursor,
            "left_datetime": left,
            "minutes_in_group": None if left is None else minutes,
            "is_escalation": link["is_escalation"],
        })

        if left is None:
            break
        cursor = left

    return rows


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main() -> None:
    dims = load_dimensions()

    priority_by_code = {}
    for row in dims["dim_priority"].to_dict("records"):
        priority_by_code.setdefault(row["priority_code"], []).append(row)

    groups_by_tier = {}
    for row in dims["dim_assignment_group"].to_dict("records"):
        groups_by_tier.setdefault(row["tier"], []).append(row)

    lookups = {
        "priority_by_code": priority_by_code,
        "categories": dims["dim_category"].to_dict("records"),
        "groups_by_tier": groups_by_tier,
        "engineer_keys": dims["dim_engineer"]["engineer_key"].tolist(),
        "channel_by_name": {r["channel_name"]: r for r in dims["dim_channel"].to_dict("records")},
        "region_by_name": {r["region_name"]: r for r in dims["dim_region"].to_dict("records")},
        "root_cause_by_name": {r["root_cause_name"]: r for r in dims["dim_root_cause"].to_dict("records")},
    }

    tickets = []
    assignments = []

    print(f"Generating {TICKET_COUNT:,} tickets...")

    for i in range(1, TICKET_COUNT + 1):
        ticket, rows = build_ticket(i, dims, lookups)
        tickets.append(ticket)

        for r in rows:
            r["ticket_id"] = ticket["ticket_id"]
            assignments.append(r)

        if i % 10_000 == 0:
            print(f"  {i:,} done")

    fact_ticket = pd.DataFrame(tickets)
    fact_ticket.insert(0, "ticket_key", range(1, len(fact_ticket) + 1))

    fact_assignment = pd.DataFrame(assignments)
    fact_assignment.insert(0, "assignment_key", range(1, len(fact_assignment) + 1))
    fact_assignment = fact_assignment.drop(columns=["tier"])

    fact_ticket.to_csv(DATA_DIR / "fact_ticket.csv", index=False)
    fact_assignment.to_csv(DATA_DIR / "fact_ticket_assignment.csv", index=False)

    print(f"\n  fact_ticket             {len(fact_ticket):7,} rows")
    print(f"  fact_ticket_assignment  {len(fact_assignment):7,} rows")
    print("\nDone.")


if __name__ == "__main__":
    main()