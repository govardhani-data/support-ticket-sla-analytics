USE SupportTicketDB;

/* Data quality report - every check in one result.
   Run this after any reload. */

SELECT 1 AS seq,
       'Ticket row count' AS check_name,
       CAST((SELECT COUNT(*) FROM fact_ticket) AS DECIMAL(12,2)) AS actual,
       '50000' AS expected

UNION ALL
SELECT 2, 'Assignment row count',
       CAST((SELECT COUNT(*) FROM fact_ticket_assignment) AS DECIMAL(12,2)),
       '88212'

UNION ALL
SELECT 3, 'Tickets resolved before they were created',
       CAST((SELECT COUNT(*) FROM fact_ticket
             WHERE resolved_datetime < created_datetime) AS DECIMAL(12,2)),
       '0'

UNION ALL
SELECT 4, 'Tickets pointing at a priority that does not exist',
       CAST((SELECT COUNT(*) FROM fact_ticket t
             LEFT JOIN dim_priority p ON t.priority_key = p.priority_key
             WHERE p.priority_key IS NULL) AS DECIMAL(12,2)),
       '0'

UNION ALL
SELECT 5, 'Tickets where minutes do not add up',
       CAST((SELECT COUNT(*) FROM fact_ticket
             WHERE is_resolved = 1
               AND total_elapsed_minutes <> sla_adjusted_minutes + hold_minutes) AS DECIMAL(12,2)),
       '0'

UNION ALL
SELECT 6, 'Percent of tickets still open',
       CAST((SELECT 100.0 * SUM(CASE WHEN resolved_datetime IS NULL THEN 1 ELSE 0 END)
                    / COUNT(*) FROM fact_ticket) AS DECIMAL(12,2)),
       'about 3'

UNION ALL
SELECT 7, 'Overall SLA breach percent',
       CAST((SELECT 100.0 * SUM(CASE WHEN is_resolution_sla_met = 0 THEN 1 ELSE 0 END)
                    / COUNT(*) FROM fact_ticket WHERE is_resolved = 1) AS DECIMAL(12,2)),
       '12 to 16'

ORDER BY seq;