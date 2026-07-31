USE SupportTicketDB;
GO

/* One row per ticket, describing the team that first picked it up
   and whether it arrived inside business hours.
   Built for Power BI, so the BI layer doesn't have to do this join. */

CREATE OR ALTER VIEW vw_ticket_first_assignment AS
SELECT
    t.ticket_id,
    g.group_name  AS first_group_name,
    g.shift_model AS first_group_shift,
    g.tier        AS first_group_tier,
    CASE WHEN d.is_weekend = 1
              OR DATEPART(HOUR, t.created_datetime) < 9
              OR DATEPART(HOUR, t.created_datetime) >= 18
         THEN 'Out of hours'
         ELSE 'Business hours'
    END AS arrival_window
FROM fact_ticket t
JOIN dim_date d
     ON t.created_date_key = d.date_key
JOIN fact_ticket_assignment a
     ON t.ticket_id = a.ticket_id AND a.assignment_seq = 1
JOIN dim_assignment_group g
     ON a.group_key = g.group_key;
GO