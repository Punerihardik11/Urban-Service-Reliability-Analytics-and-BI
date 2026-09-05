CREATE DATABASE IF NOT EXISTS `urban_service_reliability` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE `urban_service_reliability`;



CREATE TABLE IF NOT EXISTS `gold_city_snapshot` (

    `scope_id`
        VARCHAR(128)
        NOT NULL,

    `scope_start_date`
        DATE
        NOT NULL,

    `scope_end_exclusive`
        DATE
        NOT NULL,

    `scope_last_included_date`
        DATE
        NOT NULL,

    `observed_calendar_days`
        INT
        NOT NULL,

    `total_requests`
        BIGINT
        NOT NULL,

    `closed_requests`
        BIGINT
        NOT NULL,

    `current_backlog`
        BIGINT
        NOT NULL,

    `backlog_rate_pct`
        DOUBLE
        NULL,

    `requests_per_observed_day`
        DOUBLE
        NULL,

    `median_backlog_age_days`
        DOUBLE
        NULL,

    `p75_backlog_age_days`
        DOUBLE
        NULL,

    `p90_backlog_age_days`
        DOUBLE
        NULL,

    `backlog_30d_plus`
        BIGINT
        NOT NULL,

    `backlog_60d_plus`
        BIGINT
        NOT NULL,

    `backlog_90d_plus`
        BIGINT
        NOT NULL,

    `backlog_180d_plus`
        BIGINT
        NOT NULL,

    `old_backlog_share_60d_plus_pct`
        DOUBLE
        NULL,

    `valid_resolution_count`
        BIGINT
        NOT NULL,

    `median_resolution_hours`
        DOUBLE
        NULL,

    `p75_resolution_hours`
        DOUBLE
        NULL,

    `p90_resolution_hours`
        DOUBLE
        NULL,

    `median_resolution_days`
        DOUBLE
        NULL,

    `p90_resolution_days`
        DOUBLE
        NULL,

    `resolution_59_5_60_5_count`
        BIGINT
        NOT NULL,

    `resolution_59_5_60_5_share_pct`
        DOUBLE
        NULL,

    PRIMARY KEY (
        `scope_id`
    )

)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_bin;


CREATE TABLE IF NOT EXISTS `gold_service_snapshot` (

    `agency`
        VARCHAR(32)
        NOT NULL,

    `service_problem`
        VARCHAR(128)
        NOT NULL,

    `request_count`
        BIGINT
        NOT NULL,

    `backlog_count`
        BIGINT
        NOT NULL,

    `backlog_rate_pct`
        DOUBLE
        NULL,

    `share_of_city_requests_pct`
        DOUBLE
        NULL,

    `share_of_city_backlog_pct`
        DOUBLE
        NULL,

    `median_backlog_age_days`
        DOUBLE
        NULL,

    `p75_backlog_age_days`
        DOUBLE
        NULL,

    `p90_backlog_age_days`
        DOUBLE
        NULL,

    `backlog_30d_plus`
        BIGINT
        NOT NULL,

    `backlog_60d_plus`
        BIGINT
        NOT NULL,

    `backlog_90d_plus`
        BIGINT
        NOT NULL,

    `backlog_180d_plus`
        BIGINT
        NOT NULL,

    `old_backlog_share_60d_plus_pct`
        DOUBLE
        NULL,

    `valid_resolution_count`
        BIGINT
        NOT NULL,

    `median_resolution_hours`
        DOUBLE
        NULL,

    `p75_resolution_hours`
        DOUBLE
        NULL,

    `p90_resolution_hours`
        DOUBLE
        NULL,

    `median_resolution_days`
        DOUBLE
        NULL,

    `p90_resolution_days`
        DOUBLE
        NULL,

    `resolution_59_5_60_5_count`
        BIGINT
        NOT NULL,

    `resolution_59_5_60_5_share_pct`
        DOUBLE
        NULL,

    `is_structural_lifecycle_exception`
        TINYINT(1)
        NOT NULL,

    `has_systematic_60d_closure_pattern`
        TINYINT(1)
        NOT NULL,

    PRIMARY KEY (
        `agency`,
        `service_problem`
    ),

    KEY `idx_service_snapshot_backlog`
        (`backlog_count`)

)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_bin;


CREATE TABLE IF NOT EXISTS `gold_service_daily` (

    `created_date`
        DATE
        NOT NULL,

    `agency`
        VARCHAR(32)
        NOT NULL,

    `service_problem`
        VARCHAR(128)
        NOT NULL,

    `request_count`
        BIGINT
        NOT NULL,

    `current_backlog_count`
        BIGINT
        NOT NULL,

    `current_open_share_pct`
        DOUBLE
        NULL,

    `day_of_week`
        VARCHAR(16)
        NOT NULL,

    `month`
        CHAR(7)
        NOT NULL,

    PRIMARY KEY (
        `created_date`,
        `agency`,
        `service_problem`
    ),

    KEY `idx_service_daily_service`
        (`agency`, `service_problem`),

    KEY `idx_service_daily_month`
        (`month`)

)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_bin;


CREATE TABLE IF NOT EXISTS `gold_zip_snapshot` (

    `incident_zip`
        VARCHAR(20)
        NOT NULL,

    `zip_is_valid_5_digit`
        TINYINT(1)
        NOT NULL,

    `request_count`
        BIGINT
        NOT NULL,

    `backlog_count`
        BIGINT
        NOT NULL,

    `backlog_rate_pct`
        DOUBLE
        NULL,

    `share_of_city_requests_pct`
        DOUBLE
        NULL,

    `share_of_city_backlog_pct`
        DOUBLE
        NULL,

    `median_backlog_age_days`
        DOUBLE
        NULL,

    `p75_backlog_age_days`
        DOUBLE
        NULL,

    `p90_backlog_age_days`
        DOUBLE
        NULL,

    `backlog_30d_plus`
        BIGINT
        NOT NULL,

    `backlog_60d_plus`
        BIGINT
        NOT NULL,

    `backlog_90d_plus`
        BIGINT
        NOT NULL,

    `backlog_180d_plus`
        BIGINT
        NOT NULL,

    `old_backlog_share_60d_plus_pct`
        DOUBLE
        NULL,

    PRIMARY KEY (
        `incident_zip`
    ),

    KEY `idx_zip_snapshot_backlog`
        (`backlog_count`)

)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_bin;


CREATE TABLE IF NOT EXISTS `gold_service_zip_snapshot` (

    `agency`
        VARCHAR(32)
        NOT NULL,

    `service_problem`
        VARCHAR(128)
        NOT NULL,

    `incident_zip`
        VARCHAR(20)
        NOT NULL,

    `zip_is_valid_5_digit`
        TINYINT(1)
        NOT NULL,

    `request_count`
        BIGINT
        NOT NULL,

    `backlog_count`
        BIGINT
        NOT NULL,

    `backlog_rate_pct`
        DOUBLE
        NULL,

    `share_of_city_requests_pct`
        DOUBLE
        NULL,

    `share_of_city_backlog_pct`
        DOUBLE
        NULL,

    `median_backlog_age_days`
        DOUBLE
        NULL,

    `p75_backlog_age_days`
        DOUBLE
        NULL,

    `p90_backlog_age_days`
        DOUBLE
        NULL,

    `backlog_30d_plus`
        BIGINT
        NOT NULL,

    `backlog_60d_plus`
        BIGINT
        NOT NULL,

    `backlog_90d_plus`
        BIGINT
        NOT NULL,

    `backlog_180d_plus`
        BIGINT
        NOT NULL,

    `old_backlog_share_60d_plus_pct`
        DOUBLE
        NULL,

    PRIMARY KEY (
        `agency`,
        `service_problem`,
        `incident_zip`
    ),

    KEY `idx_service_zip_zip`
        (`incident_zip`),

    KEY `idx_service_zip_backlog`
        (`backlog_count`)

)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_bin;


CREATE TABLE IF NOT EXISTS `gold_service_zip_recurrence` (

    `agency`
        VARCHAR(32)
        NOT NULL,

    `service_problem`
        VARCHAR(128)
        NOT NULL,

    `incident_zip`
        VARCHAR(20)
        NOT NULL,

    `zip_is_valid_5_digit`
        TINYINT(1)
        NOT NULL,

    `request_count`
        BIGINT
        NOT NULL,

    `active_days`
        INT
        NOT NULL,

    `active_day_rate_pct`
        DOUBLE
        NULL,

    `active_weeks`
        INT
        NOT NULL,

    `active_months`
        INT
        NOT NULL,

    `first_request_date`
        DATE
        NOT NULL,

    `last_request_date`
        DATE
        NOT NULL,

    `requests_per_active_day`
        DOUBLE
        NULL,

    `median_requests_per_active_day`
        DOUBLE
        NULL,

    `p90_requests_per_active_day`
        DOUBLE
        NULL,

    `max_daily_requests`
        BIGINT
        NOT NULL,

    `top_day_share_pct`
        DOUBLE
        NULL,

    `top_5_days_share_pct`
        DOUBLE
        NULL,

    `backlog_count`
        BIGINT
        NOT NULL,

    `backlog_rate_pct`
        DOUBLE
        NULL,

    `median_backlog_age_days`
        DOUBLE
        NULL,

    `backlog_60d_plus`
        BIGINT
        NOT NULL,

    `old_backlog_share_60d_plus_pct`
        DOUBLE
        NULL,

    PRIMARY KEY (
        `agency`,
        `service_problem`,
        `incident_zip`
    ),

    KEY `idx_recurrence_active_days`
        (`active_days`),

    KEY `idx_recurrence_zip`
        (`incident_zip`)

)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_bin;


CREATE TABLE IF NOT EXISTS `gold_lifecycle_flags` (

    `agency`
        VARCHAR(32)
        NOT NULL,

    `service_problem`
        VARCHAR(128)
        NOT NULL,

    `request_count`
        BIGINT
        NOT NULL,

    `backlog_count`
        BIGINT
        NOT NULL,

    `backlog_rate_pct`
        DOUBLE
        NULL,

    `valid_resolution_count`
        BIGINT
        NOT NULL,

    `resolution_59_5_60_5_share_pct`
        DOUBLE
        NULL,

    `is_structural_lifecycle_exception`
        TINYINT(1)
        NOT NULL,

    `has_systematic_60d_closure_pattern`
        TINYINT(1)
        NOT NULL,

    `lifecycle_interpretation`
        TEXT
        NOT NULL,

    PRIMARY KEY (
        `agency`,
        `service_problem`
    ),

    KEY `idx_lifecycle_structural`
        (`is_structural_lifecycle_exception`),

    KEY `idx_lifecycle_60d`
        (`has_systematic_60d_closure_pattern`)

)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_bin;

