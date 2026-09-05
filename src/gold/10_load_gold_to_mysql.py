from __future__ import annotations

import json
import os
import re
from pathlib import Path

import numpy as np
import pandas as pd

try:
    import mysql.connector
except ImportError as exc:
    raise SystemExit(
        "mysql-connector-python is not installed.\n"
        "Install it with:\n"
        "python -m pip install mysql-connector-python"
    ) from exc


# =============================================================================
# CONFIG
# =============================================================================

ROOT = Path(__file__).resolve().parents[2]

GOLD_DIR = (
    ROOT
    / "data"
    / "gold"
    / "nyc_311_2026_ytd"
)

SQL_DIR = ROOT / "sql"

SQL_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

MANIFEST_PATH = (
    GOLD_DIR
    / "gold_manifest.json"
)


MYSQL_HOST = os.getenv(
    "MYSQL_HOST",
    "localhost",
)

MYSQL_PORT = int(
    os.getenv(
        "MYSQL_PORT",
        "3306",
    )
)

MYSQL_USER = os.getenv(
    "MYSQL_USER",
    "root",
)

MYSQL_PASSWORD = os.getenv(
    "MYSQL_PASSWORD",
    "",
)

MYSQL_DATABASE = os.getenv(
    "MYSQL_DATABASE",
    "urban_service_reliability",
)


EXPECTED_TOTAL = 2_644_153
EXPECTED_BACKLOG = 186_436
EXPECTED_VALID_RESOLUTION = 2_457_340

BATCH_SIZE = 5_000


# =============================================================================
# HELPERS
# =============================================================================

def section(
    title: str,
) -> None:

    print()
    print("=" * 118)
    print(title)
    print("=" * 118)


def validate_identifier(
    value: str,
    label: str,
) -> str:

    if not re.fullmatch(
        r"[A-Za-z0-9_]+",
        value,
    ):

        raise ValueError(
            f"{label} must contain only letters, "
            f"numbers, and underscores: {value!r}"
        )

    return value


def py_value(value):

    if value is None:
        return None

    try:

        if pd.isna(value):
            return None

    except TypeError:
        pass


    if isinstance(
        value,
        pd.Timestamp,
    ):

        if (
            value.hour == 0
            and value.minute == 0
            and value.second == 0
            and value.microsecond == 0
        ):

            return value.date()

        return value.to_pydatetime()


    if isinstance(
        value,
        np.generic,
    ):

        value = value.item()


    if isinstance(
        value,
        bool,
    ):

        return int(value)


    return value


def execute_ddl(
    cursor,
    ddl: str,
) -> None:

    statements = [

        statement.strip()

        for statement
        in ddl.split(";")

        if statement.strip()
    ]


    for statement in statements:

        if statement.upper().startswith(
            "USE "
        ):
            continue

        cursor.execute(
            statement
        )


def load_dataframe(
    cursor,
    table_name: str,
    df: pd.DataFrame,
) -> None:

    columns = list(
        df.columns
    )


    column_sql = ", ".join(
        f"`{column}`"
        for column
        in columns
    )


    placeholders = ", ".join(
        ["%s"] * len(columns)
    )


    insert_sql = (
        f"INSERT INTO `{table_name}` "
        f"({column_sql}) "
        f"VALUES ({placeholders})"
    )


    total = len(df)


    for start in range(
        0,
        total,
        BATCH_SIZE,
    ):

        batch = df.iloc[
            start:
            start + BATCH_SIZE
        ]


        rows = [

            tuple(
                py_value(value)
                for value
                in row
            )

            for row
            in batch.itertuples(
                index=False,
                name=None,
            )
        ]


        cursor.executemany(
            insert_sql,
            rows,
        )


def scalar(
    cursor,
    sql: str,
):

    cursor.execute(
        sql
    )

    row = cursor.fetchone()

    return row[0]


# =============================================================================
# VALIDATE CONFIG
# =============================================================================

MYSQL_DATABASE = validate_identifier(
    MYSQL_DATABASE,
    "MYSQL_DATABASE",
)


section(
    "URBAN SERVICE RELIABILITY - LOAD GOLD LAYER TO MYSQL"
)


# =============================================================================
# LOAD GOLD FILES
# =============================================================================

if not MANIFEST_PATH.exists():

    raise FileNotFoundError(
        f"Gold manifest not found:\n"
        f"{MANIFEST_PATH}\n"
        f"Run Step 9 first."
    )


manifest = json.loads(
    MANIFEST_PATH.read_text(
        encoding="utf-8"
    )
)


table_names = [

    "gold_city_snapshot",

    "gold_service_snapshot",

    "gold_service_daily",

    "gold_zip_snapshot",

    "gold_service_zip_snapshot",

    "gold_service_zip_recurrence",

    "gold_lifecycle_flags",
]


gold_frames: dict[
    str,
    pd.DataFrame,
] = {}


for table_name in table_names:

    path = (
        GOLD_DIR
        / f"{table_name}.parquet"
    )


    if not path.exists():

        raise FileNotFoundError(
            f"Missing Gold table:\n"
            f"{path}"
        )


    gold_frames[
        table_name
    ] = pd.read_parquet(
        path,
        engine="pyarrow",
    )


print(
    f"Gold directory:          "
    f"{GOLD_DIR}"
)

print(
    f"MySQL host:              "
    f"{MYSQL_HOST}:{MYSQL_PORT}"
)

print(
    f"MySQL user:              "
    f"{MYSQL_USER}"
)

print(
    f"MySQL database:          "
    f"{MYSQL_DATABASE}"
)

print(
    "Gold files:              PASS"
)


# =============================================================================
# MYSQL DDL
# =============================================================================

DDL = f"""

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

"""


# =============================================================================
# WRITE SQL FILE FOR REPOSITORY
# =============================================================================

ddl_path = (
    SQL_DIR
    / "10_create_gold_schema.sql"
)


ddl_path.write_text(

    (
        f"CREATE DATABASE IF NOT EXISTS "
        f"`{MYSQL_DATABASE}` "
        f"CHARACTER SET utf8mb4 "
        f"COLLATE utf8mb4_unicode_ci;\n\n"

        f"USE `{MYSQL_DATABASE}`;\n\n"

        + DDL
    ),

    encoding="utf-8",
)


# =============================================================================
# CONNECT TO MYSQL SERVER
# =============================================================================

section(
    "1 - CONNECTING TO MYSQL"
)


try:

    server_conn = (
        mysql.connector.connect(

            host=MYSQL_HOST,

            port=MYSQL_PORT,

            user=MYSQL_USER,

            password=MYSQL_PASSWORD,

            autocommit=True,
        )
    )


except mysql.connector.Error as exc:

    raise SystemExit(

        "\nCould not connect to MySQL.\n"
        "Check MYSQL_HOST, MYSQL_PORT, "
        "MYSQL_USER and MYSQL_PASSWORD.\n"
        f"MySQL error: {exc}"

    ) from exc


server_cursor = (
    server_conn.cursor()
)


server_cursor.execute(
    f"""
    CREATE DATABASE IF NOT EXISTS
    `{MYSQL_DATABASE}`
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci
    """
)


server_cursor.close()

server_conn.close()


# =============================================================================
# CONNECT TO PROJECT DATABASE
# =============================================================================

conn = mysql.connector.connect(

    host=MYSQL_HOST,

    port=MYSQL_PORT,

    user=MYSQL_USER,

    password=MYSQL_PASSWORD,

    database=MYSQL_DATABASE,

    autocommit=False,
)


cursor = conn.cursor()


print(
    "MySQL connection:        PASS"
)

print(
    "Database available:      PASS"
)

print(
    f"DDL file written:        "
    f"{ddl_path}"
)


# =============================================================================
# CREATE TABLES
# =============================================================================

section(
    "2 - CREATING MYSQL GOLD TABLES"
)

# Rebuild only the project Gold tables.
# This clears any partial state from a previous failed load
# and applies the case-sensitive table collation.

for table_name in reversed(table_names):

    cursor.execute(
        f"DROP TABLE IF EXISTS `{table_name}`"
    )

conn.commit()

execute_ddl(
    cursor,
    DDL,
)


print(
    f"Gold tables created in "
    f"`{MYSQL_DATABASE}`"
)


# =============================================================================
# LOAD GOLD TABLES
# =============================================================================

section(
    "3 - LOADING GOLD TABLES"
)


try:

    cursor.execute(
        "SET FOREIGN_KEY_CHECKS = 0"
    )


    for table_name in table_names:

        df = gold_frames[
            table_name
        ]


        cursor.execute(
            f"DELETE FROM `{table_name}`"
        )


        load_dataframe(
            cursor,
            table_name,
            df,
        )


        print(
            f"{table_name:<34} "
            f"{len(df):>10,} rows loaded"
        )


    cursor.execute(
        "SET FOREIGN_KEY_CHECKS = 1"
    )


    conn.commit()


except Exception:

    conn.rollback()

    raise


# =============================================================================
# ROW-COUNT RECONCILIATION
# =============================================================================

section(
    "4 - MYSQL ROW-COUNT RECONCILIATION"
)


row_checks = {}


for table_name in table_names:

    mysql_rows = int(
        scalar(
            cursor,
            f"SELECT COUNT(*) "
            f"FROM `{table_name}`"
        )
    )


    expected_rows = int(
        manifest[
            "tables"
        ][table_name]
    )


    passed = (
        mysql_rows
        == expected_rows
    )


    row_checks[
        table_name
    ] = passed


    print(
        f"{table_name:<34} "
        f"MySQL={mysql_rows:>8,}  "
        f"Gold={expected_rows:>8,}  "
        f"{'PASS' if passed else 'FAIL'}"
    )


# =============================================================================
# BUSINESS METRIC RECONCILIATION
# =============================================================================

section(
    "5 - BUSINESS METRIC RECONCILIATION"
)


metric_checks = {

    "City total requests":

        int(
            scalar(
                cursor,
                """
                SELECT total_requests
                FROM gold_city_snapshot
                LIMIT 1
                """
            )
        )
        == EXPECTED_TOTAL,


    "City backlog":

        int(
            scalar(
                cursor,
                """
                SELECT current_backlog
                FROM gold_city_snapshot
                LIMIT 1
                """
            )
        )
        == EXPECTED_BACKLOG,


    "City valid resolutions":

        int(
            scalar(
                cursor,
                """
                SELECT valid_resolution_count
                FROM gold_city_snapshot
                LIMIT 1
                """
            )
        )
        == EXPECTED_VALID_RESOLUTION,


    "Service request sum":

        int(
            scalar(
                cursor,
                """
                SELECT SUM(request_count)
                FROM gold_service_snapshot
                """
            )
        )
        == EXPECTED_TOTAL,


    "Service backlog sum":

        int(
            scalar(
                cursor,
                """
                SELECT SUM(backlog_count)
                FROM gold_service_snapshot
                """
            )
        )
        == EXPECTED_BACKLOG,


    "Service resolution sum":

        int(
            scalar(
                cursor,
                """
                SELECT SUM(valid_resolution_count)
                FROM gold_service_snapshot
                """
            )
        )
        == EXPECTED_VALID_RESOLUTION,


    "Service daily request sum":

        int(
            scalar(
                cursor,
                """
                SELECT SUM(request_count)
                FROM gold_service_daily
                """
            )
        )
        == EXPECTED_TOTAL,


    "Service daily backlog sum":

        int(
            scalar(
                cursor,
                """
                SELECT SUM(current_backlog_count)
                FROM gold_service_daily
                """
            )
        )
        == EXPECTED_BACKLOG,


    "ZIP request sum":

        int(
            scalar(
                cursor,
                """
                SELECT SUM(request_count)
                FROM gold_zip_snapshot
                """
            )
        )
        == EXPECTED_TOTAL,


    "ZIP backlog sum":

        int(
            scalar(
                cursor,
                """
                SELECT SUM(backlog_count)
                FROM gold_zip_snapshot
                """
            )
        )
        == EXPECTED_BACKLOG,


    "Service ZIP request sum":

        int(
            scalar(
                cursor,
                """
                SELECT SUM(request_count)
                FROM gold_service_zip_snapshot
                """
            )
        )
        == EXPECTED_TOTAL,


    "Service ZIP backlog sum":

        int(
            scalar(
                cursor,
                """
                SELECT SUM(backlog_count)
                FROM gold_service_zip_snapshot
                """
            )
        )
        == EXPECTED_BACKLOG,


    "Recurrence request sum":

        int(
            scalar(
                cursor,
                """
                SELECT SUM(request_count)
                FROM gold_service_zip_recurrence
                """
            )
        )
        == EXPECTED_TOTAL,


    "Recurrence backlog sum":

        int(
            scalar(
                cursor,
                """
                SELECT SUM(backlog_count)
                FROM gold_service_zip_recurrence
                """
            )
        )
        == EXPECTED_BACKLOG,


    "One structural lifecycle exception":

        int(
            scalar(
                cursor,
                """
                SELECT COUNT(*)
                FROM gold_lifecycle_flags
                WHERE
                    is_structural_lifecycle_exception = 1
                """
            )
        )
        == 1,
}


for label, passed in metric_checks.items():

    print(
        f"{label:<44} "
        f"{'PASS' if passed else 'FAIL'}"
    )


if not (
    all(
        row_checks.values()
    )
    and
    all(
        metric_checks.values()
    )
):

    raise RuntimeError(
        "\nMYSQL GOLD LOAD FAILED RECONCILIATION."
    )


# =============================================================================
# SANITY CHECKS
# =============================================================================

section(
    "6 - MYSQL SANITY CHECKS"
)


cursor.execute(
    """
    SELECT
        agency,
        service_problem,
        backlog_count,
        ROUND(
            backlog_rate_pct,
            2
        ),
        ROUND(
            median_backlog_age_days,
            2
        )
    FROM gold_service_snapshot
    ORDER BY backlog_count DESC
    LIMIT 10
    """
)


print(
    "Largest workflow backlogs:"
)


for row in cursor.fetchall():

    print(row)


print()


cursor.execute(
    """
    SELECT
        agency,
        service_problem,
        is_structural_lifecycle_exception,
        has_systematic_60d_closure_pattern,
        ROUND(
            resolution_59_5_60_5_share_pct,
            2
        )
    FROM gold_lifecycle_flags
    WHERE
        is_structural_lifecycle_exception = 1
        OR
        has_systematic_60d_closure_pattern = 1
    ORDER BY
        is_structural_lifecycle_exception DESC,
        resolution_59_5_60_5_share_pct DESC
    """
)


print(
    "Lifecycle flags:"
)


for row in cursor.fetchall():

    print(row)


# =============================================================================
# CLOSE
# =============================================================================

cursor.close()

conn.close()


# =============================================================================
# COMPLETE
# =============================================================================

section(
    "DAY 2 STEP 10 COMPLETE"
)


print(
    f"MySQL database:          "
    f"{MYSQL_DATABASE}"
)

print(
    f"DDL file:                "
    f"{ddl_path}"
)

print()

print(
    "MYSQL GOLD LOAD AND RECONCILIATION PASSED"
)

print()

print(
    "DAY 2 IMPLEMENTATION COMPLETE"
)