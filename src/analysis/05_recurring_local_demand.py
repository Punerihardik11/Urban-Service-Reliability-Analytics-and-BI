from __future__ import annotations

from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq


# =============================================================================
# CONFIG
# =============================================================================

ROOT = Path(__file__).resolve().parents[2]

SILVER_DIR = ROOT / "data" / "silver" / "service_requests_2026_ytd"
OUTPUT_DIR = ROOT / "outputs" / "analysis" / "day2"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

EXPECTED_TOTAL = 2_644_153
EXPECTED_CLOSED = 2_457_717
EXPECTED_BACKLOG = 186_436
EXPECTED_OBSERVED_DAYS = 241

# Diagnostic threshold only.
# Not an SLA or performance rule.
MATERIAL_PAIR_REQUESTS = 200


# =============================================================================
# HELPERS
# =============================================================================

def resolve_column(
    columns,
    candidates,
    label,
):
    for candidate in candidates:
        if candidate in columns:
            return candidate

    raise KeyError(
        f"Could not resolve '{label}'. "
        f"Tried {candidates}.\n"
        f"Available columns:\n{columns}"
    )


def safe_label(
    series,
    unknown="Unknown",
):
    result = (
        series
        .astype("string")
        .str.strip()
        .fillna(unknown)
    )

    return result.mask(
        result.eq(""),
        unknown,
    )


def section(title):
    print()
    print("=" * 118)
    print(title)
    print("=" * 118)


# =============================================================================
# DISCOVER SILVER
# =============================================================================

parts = sorted(
    SILVER_DIR.glob("part_*.parquet")
)

if not parts:
    raise FileNotFoundError(
        f"No Silver parquet parts found in:\n"
        f"{SILVER_DIR}"
    )


columns = (
    pq.ParquetFile(parts[0])
    .schema_arrow
    .names
)


CREATED_COL = resolve_column(
    columns,
    ["created_at", "created_date"],
    "created timestamp",
)


SERVICE_COL = resolve_column(
    columns,
    ["service_problem", "complaint_type"],
    "service problem",
)


ZIP_COL = resolve_column(
    columns,
    ["incident_zip", "zip_code"],
    "incident ZIP",
)


STATUS_COL = resolve_column(
    columns,
    ["status"],
    "status",
)


AGE_COL = resolve_column(
    columns,
    ["request_age_days"],
    "request age",
)


section(
    "URBAN SERVICE RELIABILITY - DAY 2 RECURRING LOCAL DEMAND"
)


print(
    f"Silver directory:        "
    f"{SILVER_DIR}"
)

print(
    f"Silver parts:            "
    f"{len(parts)}"
)

print(
    f"Created column:          "
    f"{CREATED_COL}"
)

print(
    f"Service column:          "
    f"{SERVICE_COL}"
)

print(
    f"ZIP column:              "
    f"{ZIP_COL}"
)

print(
    f"Status column:           "
    f"{STATUS_COL}"
)

print(
    f"Request age column:      "
    f"{AGE_COL}"
)


# =============================================================================
# SCAN SILVER
# =============================================================================

total_rows = 0
closed_rows = 0
backlog_rows = 0
invalid_created_rows = 0

observed_dates = set()

pair_counts = Counter()
pair_day_counts = Counter()

backlog_parts = []


for i, part in enumerate(
    parts,
    start=1,
):

    print(
        f"[{i:02d}/{len(parts):02d}] "
        f"{part.name}"
    )

    df = pd.read_parquet(
        part,
        columns=[
            CREATED_COL,
            SERVICE_COL,
            ZIP_COL,
            STATUS_COL,
            AGE_COL,
        ],
        engine="pyarrow",
    )

    total_rows += len(df)

    created = pd.to_datetime(
        df[CREATED_COL],
        errors="coerce",
    )

    service = safe_label(
        df[SERVICE_COL]
    )

    incident_zip = safe_label(
        df[ZIP_COL]
    )

    status = safe_label(
        df[STATUS_COL]
    )


    invalid_created_rows += int(
        created.isna().sum()
    )


    # -------------------------------------------------------------------------
    # LOCKED DAY 1 BUSINESS RULE
    #
    # Current request state comes from Status.
    # Backlog = Status is NOT Closed.
    # -------------------------------------------------------------------------

    is_closed = (
        status
        .str
        .casefold()
        .eq("closed")
    )

    is_backlog = ~is_closed


    closed_rows += int(
        is_closed.sum()
    )

    backlog_rows += int(
        is_backlog.sum()
    )


    # -------------------------------------------------------------------------
    # VALID CREATED-DATE ROWS
    # -------------------------------------------------------------------------

    valid_created = created.notna()


    if valid_created.any():

        valid_dates = (
            created
            .loc[valid_created]
            .dt
            .date
        )

        valid_service = (
            service
            .loc[valid_created]
        )

        valid_zip = (
            incident_zip
            .loc[valid_created]
        )


        observed_dates.update(
            valid_dates
            .unique()
            .tolist()
        )


        # ---------------------------------------------------------------------
        # SERVICE x ZIP COUNTS
        # ---------------------------------------------------------------------

        pair_frame = pd.DataFrame(
            {
                "service_problem":
                    valid_service.values,

                "incident_zip":
                    valid_zip.values,
            }
        )


        pair_counts.update(
            pair_frame
            .value_counts()
            .to_dict()
        )


        # ---------------------------------------------------------------------
        # SERVICE x ZIP x DAY COUNTS
        # ---------------------------------------------------------------------

        pair_day_frame = pd.DataFrame(
            {
                "service_problem":
                    valid_service.values,

                "incident_zip":
                    valid_zip.values,

                "date":
                    valid_dates.values,
            }
        )


        pair_day_counts.update(
            pair_day_frame
            .value_counts()
            .to_dict()
        )


    # -------------------------------------------------------------------------
    # BACKLOG CONTEXT
    # -------------------------------------------------------------------------

    backlog_parts.append(
        pd.DataFrame(
            {
                "service_problem":
                    service
                    .loc[is_backlog]
                    .values,

                "incident_zip":
                    incident_zip
                    .loc[is_backlog]
                    .values,

                "backlog_age_days":
                    pd.to_numeric(
                        df.loc[
                            is_backlog,
                            AGE_COL,
                        ],
                        errors="coerce",
                    )
                    .values,
            }
        )
    )


# =============================================================================
# RECONCILIATION
# =============================================================================

section(
    "1 - RECONCILIATION"
)


observed_days = len(
    observed_dates
)


checks = {

    "Closed + Backlog = Total":
        closed_rows
        + backlog_rows
        == total_rows,

    "Day 1 total match":
        total_rows
        == EXPECTED_TOTAL,

    "Day 1 closed match":
        closed_rows
        == EXPECTED_CLOSED,

    "Day 1 backlog match":
        backlog_rows
        == EXPECTED_BACKLOG,

    "Created timestamps valid":
        invalid_created_rows
        == 0,

    "Service x ZIP request sum":
        sum(
            pair_counts.values()
        )
        == total_rows,

    "Service x ZIP x day sum":
        sum(
            pair_day_counts.values()
        )
        == total_rows,

    "Observed calendar days":
        observed_days
        == EXPECTED_OBSERVED_DAYS,
}


print(
    f"Total Silver rows:       "
    f"{total_rows:,}"
)

print(
    f"Closed requests:         "
    f"{closed_rows:,}"
)

print(
    f"Current backlog:         "
    f"{backlog_rows:,}"
)

print(
    f"Observed calendar days:  "
    f"{observed_days:,}"
)

print(
    f"Invalid Created rows:    "
    f"{invalid_created_rows:,}"
)

print()


for label, passed in checks.items():

    print(
        f"{label:<34} "
        f"{'PASS' if passed else 'FAIL'}"
    )


if not all(
    checks.values()
):

    raise RuntimeError(
        "\nDAY 2 STEP 5 STOPPED.\n"
        "Recurring local demand analysis does not reconcile "
        "with the locked project state."
    )


# =============================================================================
# BACKLOG DATASET
# =============================================================================

backlog = pd.concat(
    backlog_parts,
    ignore_index=True,
)


if len(backlog) != EXPECTED_BACKLOG:

    raise RuntimeError(
        "Backlog row count does not match "
        "the locked Day 1 backlog."
    )


valid_backlog_age = (
    backlog[
        "backlog_age_days"
    ].notna()
    & backlog[
        "backlog_age_days"
    ].ge(0)
)


print()

print(
    f"Valid backlog ages:      "
    f"{int(valid_backlog_age.sum()):,}"
)

print(
    f"Invalid backlog ages:    "
    f"{int((~valid_backlog_age).sum()):,}"
)


# =============================================================================
# DAILY SERVICE x ZIP TABLE
# =============================================================================

daily_rows = [

    {
        "service_problem":
            service,

        "incident_zip":
            incident_zip,

        "date":
            pd.Timestamp(day),

        "request_count":
            count,
    }

    for (
        service,
        incident_zip,
        day,
    ), count

    in pair_day_counts.items()
]


daily_profile = pd.DataFrame(
    daily_rows
)


daily_profile[
    "month"
] = (
    daily_profile[
        "date"
    ]
    .dt
    .to_period("M")
    .astype(str)
)


daily_profile[
    "week_start"
] = (
    daily_profile[
        "date"
    ]
    - pd.to_timedelta(
        daily_profile[
            "date"
        ]
        .dt
        .dayofweek,
        unit="D",
    )
)


# =============================================================================
# RECURRING DEMAND METRICS
# =============================================================================

recurring_rows = []


for (
    service_name,
    zip_name,
), group in daily_profile.groupby(
    [
        "service_problem",
        "incident_zip",
    ],
    dropna=False,
):

    counts = (
        group[
            "request_count"
        ]
        .astype(float)
    )


    request_count = int(
        counts.sum()
    )


    active_days = len(
        group
    )


    first_date = (
        group[
            "date"
        ]
        .min()
    )


    last_date = (
        group[
            "date"
        ]
        .max()
    )


    active_weeks = int(
        group[
            "week_start"
        ]
        .nunique()
    )


    active_months = int(
        group[
            "month"
        ]
        .nunique()
    )


    max_daily = int(
        counts.max()
    )


    top_5_total = int(
        counts
        .nlargest(
            min(
                5,
                len(counts),
            )
        )
        .sum()
    )


    recurring_rows.append(
        {
            "service_problem":
                service_name,

            "incident_zip":
                zip_name,

            "request_count":
                request_count,

            "active_days":
                active_days,

            "active_day_rate_pct":
                active_days
                / observed_days
                * 100,

            "active_weeks":
                active_weeks,

            "active_months":
                active_months,

            "first_request_date":
                first_date,

            "last_request_date":
                last_date,

            "requests_per_active_day":
                request_count
                / active_days,

            "median_requests_per_active_day":
                float(
                    counts.median()
                ),

            "p90_requests_per_active_day":
                float(
                    counts.quantile(
                        0.90
                    )
                ),

            "max_daily_requests":
                max_daily,

            "top_day_share_pct":
                max_daily
                / request_count
                * 100,

            "top_5_days_share_pct":
                top_5_total
                / request_count
                * 100,
        }
    )


recurring_profile = pd.DataFrame(
    recurring_rows
)


# =============================================================================
# BACKLOG CONTEXT BY SERVICE x ZIP
# =============================================================================

backlog_rows_out = []


for (
    service_name,
    zip_name,
), group in backlog.groupby(
    [
        "service_problem",
        "incident_zip",
    ],
    dropna=False,
):

    ages = group.loc[
        group[
            "backlog_age_days"
        ].notna()
        & group[
            "backlog_age_days"
        ].ge(0),

        "backlog_age_days",
    ]


    backlog_count = len(
        group
    )


    backlog_60d = int(
        (ages >= 60)
        .sum()
    )


    backlog_rows_out.append(
        {
            "service_problem":
                service_name,

            "incident_zip":
                zip_name,

            "backlog_count":
                backlog_count,

            "median_backlog_age_days":
                (
                    float(
                        ages.median()
                    )
                    if not ages.empty
                    else np.nan
                ),

            "backlog_60d_plus":
                backlog_60d,

            "old_backlog_share_60d_plus_pct":
                (
                    backlog_60d
                    / backlog_count
                    * 100
                    if backlog_count
                    else np.nan
                ),
        }
    )


backlog_profile = pd.DataFrame(
    backlog_rows_out
)


recurring_profile = (
    recurring_profile
    .merge(
        backlog_profile,
        on=[
            "service_problem",
            "incident_zip",
        ],
        how="left",
    )
)


recurring_profile[
    "backlog_count"
] = (
    recurring_profile[
        "backlog_count"
    ]
    .fillna(0)
    .astype(int)
)


recurring_profile[
    "backlog_60d_plus"
] = (
    recurring_profile[
        "backlog_60d_plus"
    ]
    .fillna(0)
    .astype(int)
)


recurring_profile[
    "backlog_rate_pct"
] = (
    recurring_profile[
        "backlog_count"
    ]
    / recurring_profile[
        "request_count"
    ]
    * 100
)


recurring_profile[
    "zip_is_valid_5_digit"
] = (
    recurring_profile[
        "incident_zip"
    ]
    .astype("string")
    .str
    .fullmatch(
        r"\d{5}",
        na=False,
    )
)


recurring_profile = (
    recurring_profile
    .sort_values(
        [
            "request_count",
            "active_days",
        ],
        ascending=False,
    )
    .reset_index(
        drop=True
    )
)


# =============================================================================
# MATERIAL PAIRS
# =============================================================================

material = (
    recurring_profile
    .loc[
        recurring_profile[
            "zip_is_valid_5_digit"
        ]
        & recurring_profile[
            "request_count"
        ].ge(
            MATERIAL_PAIR_REQUESTS
        )
    ]
    .copy()
)


# =============================================================================
# OUTPUTS
# =============================================================================

daily_profile.to_csv(
    OUTPUT_DIR
    / "recurring_service_zip_daily.csv",
    index=False,
)


recurring_profile.to_csv(
    OUTPUT_DIR
    / "recurring_service_zip_profile.csv",
    index=False,
)


material.to_csv(
    OUTPUT_DIR
    / "recurring_service_zip_material_pairs.csv",
    index=False,
)


# =============================================================================
# PRINT RESULTS
# =============================================================================

section(
    "2 - MOST RECURRENT LOCAL SERVICE PATTERNS"
)


most_recurrent = (
    material
    .sort_values(
        [
            "active_days",
            "request_count",
        ],
        ascending=False,
    )
    .head(30)
)


print(
    most_recurrent[
        [
            "service_problem",
            "incident_zip",
            "request_count",
            "active_days",
            "active_day_rate_pct",
            "active_weeks",
            "active_months",
            "requests_per_active_day",
            "top_5_days_share_pct",
        ]
    ]
    .to_string(
        index=False
    )
)


# =============================================================================

section(
    "3 - HIGHEST SUSTAINED DAILY INTENSITY"
)


sustained = (
    material
    .loc[
        material[
            "active_days"
        ].ge(60)
    ]
    .sort_values(
        [
            "requests_per_active_day",
            "active_days",
        ],
        ascending=False,
    )
    .head(30)
)


print(
    sustained[
        [
            "service_problem",
            "incident_zip",
            "request_count",
            "active_days",
            "active_day_rate_pct",
            "requests_per_active_day",
            "median_requests_per_active_day",
            "p90_requests_per_active_day",
            "max_daily_requests",
        ]
    ]
    .to_string(
        index=False
    )
)


# =============================================================================

section(
    "4 - MOST BURST-CONCENTRATED MATERIAL PATTERNS"
)


burst = (
    material
    .sort_values(
        [
            "top_5_days_share_pct",
            "request_count",
        ],
        ascending=False,
    )
    .head(30)
)


print(
    burst[
        [
            "service_problem",
            "incident_zip",
            "request_count",
            "active_days",
            "top_day_share_pct",
            "top_5_days_share_pct",
            "max_daily_requests",
        ]
    ]
    .to_string(
        index=False
    )
)


# =============================================================================

section(
    "5 - RECURRING LOCAL DEMAND WITH CURRENT BACKLOG"
)


recurring_backlog = (
    material
    .loc[
        material[
            "backlog_count"
        ].gt(0)
    ]
    .sort_values(
        [
            "backlog_count",
            "active_days",
        ],
        ascending=False,
    )
    .head(30)
)


print(
    recurring_backlog[
        [
            "service_problem",
            "incident_zip",
            "request_count",
            "active_days",
            "backlog_count",
            "backlog_rate_pct",
            "median_backlog_age_days",
            "backlog_60d_plus",
            "old_backlog_share_60d_plus_pct",
        ]
    ]
    .to_string(
        index=False
    )
)


# =============================================================================
# SUMMARY
# =============================================================================

summary_lines = [

    "URBAN SERVICE RELIABILITY - DAY 2 RECURRING LOCAL DEMAND",

    "=" * 78,

    "",

    "RECONCILIATION",

    f"Total Silver rows:       "
    f"{total_rows:,}",

    f"Closed requests:         "
    f"{closed_rows:,}",

    f"Current backlog:         "
    f"{backlog_rows:,}",

    f"Observed calendar days:  "
    f"{observed_days:,}",

    "",

    "INTERPRETATION RULES",

    "- Recurrence is measured from repeated Service x ZIP activity "
    "across observed days.",

    "- Raw ZIP counts are not population-adjusted service burden.",

    "- High recurrence indicates repeated local demand, "
    "not necessarily repeated requests from the same resident or address.",

    "- Burst concentration distinguishes sustained demand "
    "from event-driven spikes.",

    "- Material-pair thresholds are diagnostic only, "
    "not SLA or performance rules.",
]


(
    OUTPUT_DIR
    / "recurring_local_demand_summary.txt"
).write_text(
    "\n".join(
        summary_lines
    ),
    encoding="utf-8",
)


# =============================================================================
# COMPLETE
# =============================================================================

section(
    "DAY 2 - STEP 5 ANALYSIS COMPLETE"
)


print(
    "Outputs written:"
)

print(
    OUTPUT_DIR
    / "recurring_service_zip_daily.csv"
)

print(
    OUTPUT_DIR
    / "recurring_service_zip_profile.csv"
)

print(
    OUTPUT_DIR
    / "recurring_service_zip_material_pairs.csv"
)

print(
    OUTPUT_DIR
    / "recurring_local_demand_summary.txt"
)

print()

print(
    "RECURRING LOCAL DEMAND ANALYSIS PASSED"
)