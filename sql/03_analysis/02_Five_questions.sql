/* ===========================================================================
   02_five_questions.sql
   Answers the five questions defined in docs/findings.md.
   Data as at 2025-12-31. Overall breach rate 13.31%.
   =========================================================================== */

USE SupportTicketDB;


/* --- Q1: breach rate by priority ---------------------------------------- */

SELECT
    p.priority_code,
    p.priority_name,
    p.resolution_sla_minutes,
    COUNT(*) AS tickets,
    SUM(CASE WHEN t.is_resolution_sla_met = 0 THEN 1 ELSE 0 END) AS breached,
    CAST(100.0 * SUM(CASE WHEN t.is_resolution_sla_met = 0 THEN 1 ELSE 0 END)
         / COUNT(*) AS DECIMAL(5,2)) AS breach_pct
FROM fact_ticket t
JOIN dim_priority p ON t.priority_key = p.priority_key
WHERE t.is_resolved = 1
GROUP BY p.priority_code, p.priority_name, p.resolution_sla_minutes
ORDER BY p.priority_code;


/* --- Q2: breach rate by number of handovers ----------------------------- */

SELECT
    lateral_reassignment_count + escalation_count AS handovers,
    COUNT(*) AS tickets,
    SUM(CASE WHEN is_resolution_sla_met = 0 THEN 1 ELSE 0 END) AS breached,
    CAST(100.0 * SUM(CASE WHEN is_resolution_sla_met = 0 THEN 1 ELSE 0 END)
         / COUNT(*) AS DECIMAL(5,2)) AS breach_pct
FROM fact_ticket
WHERE is_resolved = 1
GROUP BY lateral_reassignment_count + escalation_count
ORDER BY handovers;


/* --- Q3: breach rate by problem type ------------------------------------ */

SELECT
    c.category,
    c.subcategory,
    COUNT(*) AS tickets,
    SUM(CASE WHEN t.is_resolution_sla_met = 0 THEN 1 ELSE 0 END) AS breached,
    CAST(100.0 * SUM(CASE WHEN t.is_resolution_sla_met = 0 THEN 1 ELSE 0 END)
         / COUNT(*) AS DECIMAL(5,2)) AS breach_pct
FROM fact_ticket t
JOIN dim_category c ON t.category_key = c.category_key
WHERE t.is_resolved = 1
GROUP BY c.category, c.subcategory
HAVING COUNT(*) >= 500
ORDER BY breach_pct DESC;


/* --- Q4a: volume and breach by day of week ------------------------------ */

SELECT
    d.day_of_week,
    d.day_name,
    COUNT(*) AS tickets,
    CAST(100.0 * SUM(CASE WHEN t.is_resolution_sla_met = 0 THEN 1 ELSE 0 END)
         / COUNT(*) AS DECIMAL(5,2)) AS breach_pct
FROM fact_ticket t
JOIN dim_date d ON t.created_date_key = d.date_key
WHERE t.is_resolved = 1
GROUP BY d.day_of_week, d.day_name
ORDER BY d.day_of_week;


/* --- Q4b: volume and breach by hour of arrival -------------------------- */

SELECT
    DATEPART(HOUR, created_datetime) AS hour_of_day,
    COUNT(*) AS tickets,
    CAST(100.0 * SUM(CASE WHEN is_resolution_sla_met = 0 THEN 1 ELSE 0 END)
         / COUNT(*) AS DECIMAL(5,2)) AS breach_pct
FROM fact_ticket
WHERE is_resolved = 1
GROUP BY DATEPART(HOUR, created_datetime)
ORDER BY hour_of_day;


/* --- Q4c: the real driver - arrival window vs team coverage ------------- */

SELECT
    g.shift_model,
    CASE WHEN d.is_weekend = 1
              OR DATEPART(HOUR, t.created_datetime) < 9
              OR DATEPART(HOUR, t.created_datetime) >= 18
         THEN 'Out of hours'
         ELSE 'Business hours'
    END AS arrival_window,
    COUNT(*) AS tickets,
    SUM(CASE WHEN t.is_resolution_sla_met = 0 THEN 1 ELSE 0 END) AS breached,
    CAST(100.0 * SUM(CASE WHEN t.is_resolution_sla_met = 0 THEN 1 ELSE 0 END)
         / COUNT(*) AS DECIMAL(5,2)) AS breach_pct
FROM fact_ticket t
JOIN dim_date d ON t.created_date_key = d.date_key
JOIN fact_ticket_assignment a
     ON t.ticket_id = a.ticket_id AND a.assignment_seq = 1
JOIN dim_assignment_group g ON a.group_key = g.group_key
WHERE t.is_resolved = 1
GROUP BY g.shift_model,
         CASE WHEN d.is_weekend = 1
                   OR DATEPART(HOUR, t.created_datetime) < 9
                   OR DATEPART(HOUR, t.created_datetime) >= 18
              THEN 'Out of hours'
              ELSE 'Business hours'
         END
ORDER BY g.shift_model, arrival_window;


/* --- Q5a: how old is the open backlog ----------------------------------- */

SELECT
    CASE
        WHEN DATEDIFF(DAY, created_datetime, '2025-12-31') <= 7   THEN '1. 0-7 days'
        WHEN DATEDIFF(DAY, created_datetime, '2025-12-31') <= 30  THEN '2. 8-30 days'
        WHEN DATEDIFF(DAY, created_datetime, '2025-12-31') <= 90  THEN '3. 31-90 days'
        WHEN DATEDIFF(DAY, created_datetime, '2025-12-31') <= 180 THEN '4. 91-180 days'
        ELSE '5. over 180 days'
    END AS age_band,
    COUNT(*) AS open_tickets
FROM fact_ticket
WHERE is_resolved = 0
GROUP BY
    CASE
        WHEN DATEDIFF(DAY, created_datetime, '2025-12-31') <= 7   THEN '1. 0-7 days'
        WHEN DATEDIFF(DAY, created_datetime, '2025-12-31') <= 30  THEN '2. 8-30 days'
        WHEN DATEDIFF(DAY, created_datetime, '2025-12-31') <= 90  THEN '3. 31-90 days'
        WHEN DATEDIFF(DAY, created_datetime, '2025-12-31') <= 180 THEN '4. 91-180 days'
        ELSE '5. over 180 days'
    END
ORDER BY age_band;


/* --- Q5b: the ones that should worry a manager -------------------------- */

SELECT
    p.priority_code,
    COUNT(*) AS open_tickets,
    MAX(DATEDIFF(DAY, t.created_datetime, '2025-12-31')) AS oldest_days,
    AVG(DATEDIFF(DAY, t.created_datetime, '2025-12-31')) AS avg_age_days,
    SUM(CASE WHEN DATEDIFF(DAY, t.created_datetime, '2025-12-31') > 90
             THEN 1 ELSE 0 END) AS open_over_90_days
FROM fact_ticket t
JOIN dim_priority p ON t.priority_key = p.priority_key
WHERE t.is_resolved = 0
GROUP BY p.priority_code
ORDER BY p.priority_code;