USE SupportTicketDB;

-- Check the ITIL priority matrix loaded correctly
SELECT * FROM dim_priority;

-- Priorities ordered by how long we get to fix them
SELECT priority_code, priority_name, resolution_sla_minutes
FROM dim_priority
ORDER BY resolution_sla_minutes DESC;

-- Verify the ISO year fix: 1 Jan 2023 belongs to week 52 of 2022
SELECT TOP 5 date_key, full_date, day_name, iso_year, year, week_of_year
FROM dim_date
ORDER BY date_key;