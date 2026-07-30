USE SupportTicketDB;
GO

DROP TABLE IF EXISTS fact_ticket_assignment;
DROP TABLE IF EXISTS fact_ticket;
DROP TABLE IF EXISTS dim_date;
DROP TABLE IF EXISTS dim_priority;
DROP TABLE IF EXISTS dim_category;
DROP TABLE IF EXISTS dim_assignment_group;
DROP TABLE IF EXISTS dim_engineer;
DROP TABLE IF EXISTS dim_channel;
DROP TABLE IF EXISTS dim_region;
DROP TABLE IF EXISTS dim_root_cause;
GO

CREATE TABLE dim_date (
    date_key        INT          NOT NULL PRIMARY KEY,
    full_date       DATE         NOT NULL,
    day_of_week     TINYINT      NOT NULL,
    day_name        VARCHAR(9)   NOT NULL,
    iso_year        SMALLINT     NOT NULL,
    week_of_year    TINYINT      NOT NULL,
    month           TINYINT      NOT NULL,
    month_name      VARCHAR(9)   NOT NULL,
    quarter         TINYINT      NOT NULL,
    year            SMALLINT     NOT NULL,
    is_weekend      BIT          NOT NULL,
    is_holiday      BIT          NOT NULL,
    is_working_day  BIT          NOT NULL
);

CREATE TABLE dim_priority (
    priority_key            INT          NOT NULL PRIMARY KEY,
    impact                  VARCHAR(10)  NOT NULL,
    urgency                 VARCHAR(10)  NOT NULL,
    priority_code           CHAR(2)      NOT NULL,
    priority_name           VARCHAR(20)  NOT NULL,
    response_sla_minutes    INT          NOT NULL,
    resolution_sla_minutes  INT          NOT NULL
);

CREATE TABLE dim_category (
    category_key  INT          NOT NULL PRIMARY KEY,
    category      VARCHAR(30)  NOT NULL,
    subcategory   VARCHAR(40)  NOT NULL
);

CREATE TABLE dim_assignment_group (
    group_key     INT          NOT NULL PRIMARY KEY,
    group_name    VARCHAR(40)  NOT NULL,
    tier          TINYINT      NOT NULL,
    region        VARCHAR(20)  NOT NULL,
    shift_model   VARCHAR(20)  NOT NULL
);

CREATE TABLE dim_engineer (
    engineer_key   INT          NOT NULL PRIMARY KEY,
    engineer_name  VARCHAR(60)  NOT NULL,
    seniority      VARCHAR(10)  NOT NULL
);

CREATE TABLE dim_channel (
    channel_key   INT          NOT NULL PRIMARY KEY,
    channel_name  VARCHAR(30)  NOT NULL
);

CREATE TABLE dim_region (
    region_key   INT          NOT NULL PRIMARY KEY,
    region_name  VARCHAR(20)  NOT NULL,
    timezone     VARCHAR(30)  NOT NULL
);

CREATE TABLE dim_root_cause (
    root_cause_key   INT          NOT NULL PRIMARY KEY,
    root_cause_name  VARCHAR(40)  NOT NULL
);
GO

CREATE TABLE fact_ticket (
    ticket_key                  INT          NOT NULL PRIMARY KEY,
    ticket_id                   VARCHAR(12)  NOT NULL UNIQUE,

    created_date_key            INT          NOT NULL,
    created_datetime            DATETIME2    NOT NULL,
    first_response_datetime     DATETIME2    NULL,
    resolved_datetime           DATETIME2    NULL,

    priority_key                INT          NOT NULL,
    category_key                INT          NOT NULL,
    final_group_key             INT          NOT NULL,
    engineer_key                INT          NOT NULL,
    channel_key                 INT          NOT NULL,
    region_key                  INT          NOT NULL,
    root_cause_key              INT          NULL,

    total_elapsed_minutes       INT          NULL,
    hold_minutes                INT          NULL,
    sla_adjusted_minutes        INT          NULL,
    first_response_minutes      INT          NULL,

    lateral_reassignment_count  TINYINT      NOT NULL,
    escalation_count            TINYINT      NOT NULL,
    max_tier_reached            TINYINT      NOT NULL,
    reopen_count                TINYINT      NOT NULL,

    is_response_sla_met         BIT          NULL,
    is_resolution_sla_met       BIT          NULL,
    is_resolved                 BIT          NOT NULL,

    CONSTRAINT fk_ticket_date      FOREIGN KEY (created_date_key) REFERENCES dim_date(date_key),
    CONSTRAINT fk_ticket_priority  FOREIGN KEY (priority_key)     REFERENCES dim_priority(priority_key),
    CONSTRAINT fk_ticket_category  FOREIGN KEY (category_key)     REFERENCES dim_category(category_key),
    CONSTRAINT fk_ticket_group     FOREIGN KEY (final_group_key)  REFERENCES dim_assignment_group(group_key),
    CONSTRAINT fk_ticket_engineer  FOREIGN KEY (engineer_key)     REFERENCES dim_engineer(engineer_key),
    CONSTRAINT fk_ticket_channel   FOREIGN KEY (channel_key)      REFERENCES dim_channel(channel_key),
    CONSTRAINT fk_ticket_region    FOREIGN KEY (region_key)       REFERENCES dim_region(region_key),
    CONSTRAINT fk_ticket_cause     FOREIGN KEY (root_cause_key)   REFERENCES dim_root_cause(root_cause_key),

    CONSTRAINT ck_ticket_time_flows_forward
        CHECK (resolved_datetime IS NULL OR resolved_datetime >= created_datetime),

    CONSTRAINT ck_ticket_minutes_add_up
        CHECK (total_elapsed_minutes IS NULL
               OR total_elapsed_minutes = sla_adjusted_minutes + hold_minutes)
);
GO
CREATE TABLE fact_ticket_assignment (
    assignment_key     INT          NOT NULL PRIMARY KEY,
    ticket_id          VARCHAR(12)  NOT NULL,
    assignment_seq     TINYINT      NOT NULL,
    group_key          INT          NOT NULL,
    engineer_key       INT          NOT NULL,
    assigned_datetime  DATETIME2    NOT NULL,
    left_datetime      DATETIME2    NULL,
    minutes_in_group   INT          NULL,
    is_escalation      BIT          NOT NULL,

    CONSTRAINT fk_assign_ticket    FOREIGN KEY (ticket_id)    REFERENCES fact_ticket(ticket_id),
    CONSTRAINT fk_assign_group     FOREIGN KEY (group_key)    REFERENCES dim_assignment_group(group_key),
    CONSTRAINT fk_assign_engineer  FOREIGN KEY (engineer_key) REFERENCES dim_engineer(engineer_key),

    CONSTRAINT ck_assign_seq_positive CHECK (assignment_seq >= 1),

    CONSTRAINT ck_assign_time_flows_forward
        CHECK (left_datetime IS NULL OR left_datetime >= assigned_datetime)
);
GO

CREATE INDEX ix_ticket_created_date  ON fact_ticket (created_date_key);
CREATE INDEX ix_ticket_priority      ON fact_ticket (priority_key);
CREATE INDEX ix_ticket_category      ON fact_ticket (category_key);
CREATE INDEX ix_ticket_group         ON fact_ticket (final_group_key);
CREATE INDEX ix_assign_ticket        ON fact_ticket_assignment (ticket_id);
GO

PRINT 'Schema created successfully.';