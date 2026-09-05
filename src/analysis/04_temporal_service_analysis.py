from __future__ import annotations

from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[2]

SILVER_DIR = ROOT / "data" / "silver" / "service_requests_2026_ytd"
OUTPUT_DIR = ROOT / "outputs" / "analysis" / "day2"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

EXPECTED_TOTAL = 2_644_153
EXPECTED_CLOSED = 2_457_717
EXPECTED_BACKLOG = 186_436
EXPECTED_OBSERVED_DAYS = 241


def resolve_column(columns, candidates, label):
    for candidate in candidates:
        if candidate in columns:
            return candidate

    raise KeyError(
        f"Could not resolve '{label}'. "
        f"Tried {candidates}.\n"
        f"Available columns:\n{columns}"
    )


def safe_label(series, unknown="Unknown"):
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
    print("=" * 112)
    print(title)
    print("=" * 112)


# =============================================================================
# DISCOVER SILVER
# =============================================================================

parts = sorted(
    SILVER_DIR.glob("part_*.parquet")
)

if not parts:
    raise FileNotFoundError(
        f"No Silver parquet parts found in:\n{SILVER_DIR}"
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

STATUS_COL = resolve_column(
    columns,
    ["status"],
    "status",
)


section(
    "URBAN SERVICE RELIABILITY - DAY 2 TEMPORAL x SERVICE ANALYSIS"
)

print(f"Silver directory:        {SILVER_DIR}")
print(f"Silver parts:            {len(parts)}")
print(f"Created column:          {CREATED_COL}")
print(f"Service column:          {SERVICE_COL}")
print(f"Status column:           {STATUS_COL}")


# =============================================================================
# SCAN SILVER
# =============================================================================

total_rows = 0
closed_rows = 0
backlog_rows = 0
invalid_created_rows = 0

date_counts = Counter()
month_counts = Counter()
weekday_counts = Counter()
hour_counts = Counter()

service_counts = Counter()
service_month_counts = Counter()
service_day_counts = Counter()

backlog_month_counts = Counter()
service_month_backlog_counts = Counter()

observed_dates = set()


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
            STATUS_COL,
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

    status = safe_label(
        df[STATUS_COL]
    )

    invalid_created_rows += int(
        created.isna().sum()
    )

    # Locked Day 1 rule:
    # backlog = Status is not Closed
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

    valid = created.notna()

    created = created.loc[valid]
    service = service.loc[valid]
    is_backlog = is_backlog.loc[valid]

    dates = created.dt.date

    months = (
        created
        .dt
        .to_period("M")
        .astype(str)
    )

    weekdays = created.dt.day_name()
    hours = created.dt.hour

    observed_dates.update(
        dates.unique().tolist()
    )

    date_counts.update(
        dates.value_counts().to_dict()
    )

    month_counts.update(
        months.value_counts().to_dict()
    )

    weekday_counts.update(
        weekdays.value_counts().to_dict()
    )

    hour_counts.update(
        hours.value_counts().to_dict()
    )

    service_counts.update(
        service.value_counts().to_dict()
    )

    service_month_counts.update(
        pd.DataFrame(
            {
                "service_problem":
                    service.values,

                "month":
                    months.values,
            }
        )
        .value_counts()
        .to_dict()
    )

    service_day_counts.update(
        pd.DataFrame(
            {
                "service_problem":
                    service.values,

                "date":
                    dates.values,
            }
        )
        .value_counts()
        .to_dict()
    )

    backlog_month_counts.update(
        months
        .loc[is_backlog]
        .value_counts()
        .to_dict()
    )

    service_month_backlog_counts.update(
        pd.DataFrame(
            {
                "service_problem":
                    service
                    .loc[is_backlog]
                    .values,

                "month":
                    months
                    .loc[is_backlog]
                    .values,
            }
        )
        .value_counts()
        .to_dict()
    )


# =============================================================================
# RECONCILIATION
# =============================================================================

section("1 - RECONCILIATION")

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

    "Daily request sum":
        sum(
            date_counts.values()
        )
        == total_rows,

    "Monthly request sum":
        sum(
            month_counts.values()
        )
        == total_rows,

    "Weekday request sum":
        sum(
            weekday_counts.values()
        )
        == total_rows,

    "Hourly request sum":
        sum(
            hour_counts.values()
        )
        == total_rows,

    "Service x month request sum":
        sum(
            service_month_counts.values()
        )
        == total_rows,

    "Service x day request sum":
        sum(
            service_day_counts.values()
        )
        == total_rows,

    "Backlog month sum":
        sum(
            backlog_month_counts.values()
        )
        == backlog_rows,

    "Service x month backlog sum":
        sum(
            service_month_backlog_counts.values()
        )
        == backlog_rows,

    "Observed calendar days":
        observed_days
        == EXPECTED_OBSERVED_DAYS,
}


print(f"Total Silver rows:       {total_rows:,}")
print(f"Closed requests:         {closed_rows:,}")
print(f"Current backlog:         {backlog_rows:,}")
print(f"Observed calendar days:  {observed_days:,}")
print(f"Invalid Created rows:    {invalid_created_rows:,}")

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
        "\nDAY 2 STEP 4 STOPPED.\n"
        "Temporal analysis does not reconcile "
        "with the locked Day 1 state."
    )


# =============================================================================
# DAILY PROFILE
# =============================================================================

daily_profile = pd.DataFrame(
    [
        {
            "date":
                pd.Timestamp(day),

            "request_count":
                count,
        }

        for day, count
        in date_counts.items()
    ]
)


daily_profile = (
    daily_profile
    .sort_values("date")
    .reset_index(drop=True)
)


daily_profile[
    "day_of_week"
] = (
    daily_profile["date"]
    .dt
    .day_name()
)


daily_profile[
    "month"
] = (
    daily_profile["date"]
    .dt
    .to_period("M")
    .astype(str)
)


# =============================================================================
# MONTHLY PROFILE
# =============================================================================

month_day_counts = (
    daily_profile
    .groupby("month")
    .size()
    .rename("observed_days")
    .reset_index()
)


monthly_profile = pd.DataFrame(
    [
        {
            "month":
                month,

            "request_count":
                count,

            "backlog_count":
                backlog_month_counts.get(
                    month,
                    0,
                ),
        }

        for month, count
        in month_counts.items()
    ]
)


monthly_profile = (
    monthly_profile
    .merge(
        month_day_counts,
        on="month",
        how="left",
    )
)


monthly_profile[
    "requests_per_observed_day"
] = (
    monthly_profile[
        "request_count"
    ]
    / monthly_profile[
        "observed_days"
    ]
)


monthly_profile[
    "current_open_share_pct"
] = (
    monthly_profile[
        "backlog_count"
    ]
    / monthly_profile[
        "request_count"
    ]
    * 100
)


monthly_profile[
    "share_of_total_demand_pct"
] = (
    monthly_profile[
        "request_count"
    ]
    / total_rows
    * 100
)


monthly_profile = (
    monthly_profile
    .sort_values("month")
    .reset_index(drop=True)
)


# =============================================================================
# WEEKDAY PROFILE
# =============================================================================

weekday_order = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


weekday_day_counts = Counter(
    pd.Series(
        sorted(
            observed_dates
        )
    )
    .map(
        lambda d:
        pd.Timestamp(d).day_name()
    )
    .value_counts()
    .to_dict()
)


weekday_profile = pd.DataFrame(
    [
        {
            "day_of_week":
                day,

            "request_count":
                weekday_counts.get(
                    day,
                    0,
                ),

            "observed_days":
                weekday_day_counts.get(
                    day,
                    0,
                ),
        }

        for day in weekday_order
    ]
)


weekday_profile[
    "requests_per_observed_day"
] = np.where(
    weekday_profile[
        "observed_days"
    ] > 0,

    weekday_profile[
        "request_count"
    ]
    / weekday_profile[
        "observed_days"
    ],

    np.nan,
)


weekday_profile[
    "share_of_total_demand_pct"
] = (
    weekday_profile[
        "request_count"
    ]
    / total_rows
    * 100
)


# =============================================================================
# HOURLY PROFILE
# =============================================================================

hourly_profile = pd.DataFrame(
    [
        {
            "hour":
                hour,

            "request_count":
                hour_counts.get(
                    hour,
                    0,
                ),
        }

        for hour
        in range(24)
    ]
)


hourly_profile[
    "share_of_total_demand_pct"
] = (
    hourly_profile[
        "request_count"
    ]
    / total_rows
    * 100
)


# =============================================================================
# SERVICE x MONTH PROFILE
# =============================================================================

service_month_profile = pd.DataFrame(
    [
        {
            "service_problem":
                service,

            "month":
                month,

            "request_count":
                request_count,

            "backlog_count":
                service_month_backlog_counts.get(
                    (
                        service,
                        month,
                    ),
                    0,
                ),
        }

        for (
            service,
            month,
        ), request_count
        in service_month_counts.items()
    ]
)


service_totals = pd.DataFrame(
    [
        {
            "service_problem":
                service,

            "service_request_count":
                count,
        }

        for service, count
        in service_counts.items()
    ]
)


month_context = (
    monthly_profile[
        [
            "month",
            "request_count",
            "observed_days",
        ]
    ]
    .rename(
        columns={
            "request_count":
                "month_request_count",
        }
    )
)


service_month_profile = (
    service_month_profile
    .merge(
        service_totals,
        on="service_problem",
        how="left",
    )
    .merge(
        month_context,
        on="month",
        how="left",
    )
)


service_month_profile[
    "requests_per_observed_day"
] = (
    service_month_profile[
        "request_count"
    ]
    / service_month_profile[
        "observed_days"
    ]
)


service_month_profile[
    "current_open_share_pct"
] = (
    service_month_profile[
        "backlog_count"
    ]
    / service_month_profile[
        "request_count"
    ]
    * 100
)


service_month_profile[
    "share_of_service_demand_pct"
] = (
    service_month_profile[
        "request_count"
    ]
    / service_month_profile[
        "service_request_count"
    ]
    * 100
)


service_month_profile[
    "share_of_month_demand_pct"
] = (
    service_month_profile[
        "request_count"
    ]
    / service_month_profile[
        "month_request_count"
    ]
    * 100
)


service_month_profile = (
    service_month_profile
    .sort_values(
        [
            "service_problem",
            "month",
        ]
    )
    .reset_index(drop=True)
)


# =============================================================================
# SERVICE x DAY PROFILE
# =============================================================================

service_day_profile = pd.DataFrame(
    [
        {
            "service_problem":
                service,

            "date":
                pd.Timestamp(day),

            "request_count":
                count,
        }

        for (
            service,
            day,
        ), count
        in service_day_counts.items()
    ]
)


service_day_profile[
    "month"
] = (
    service_day_profile[
        "date"
    ]
    .dt
    .to_period("M")
    .astype(str)
)


service_day_profile = (
    service_day_profile
    .sort_values(
        [
            "date",
            "request_count",
        ],
        ascending=[
            True,
            False,
        ],
    )
    .reset_index(drop=True)
)


# =============================================================================
# TOP-DAY SERVICE CONTRIBUTORS
# =============================================================================

top_days = (
    daily_profile
    .sort_values(
        "request_count",
        ascending=False,
    )
    .head(20)
    .copy()
)


top_day_service_contributors = (
    service_day_profile[
        service_day_profile[
            "date"
        ]
        .isin(
            set(
                top_days["date"]
            )
        )
    ]
    .merge(
        daily_profile[
            [
                "date",
                "request_count",
            ]
        ]
        .rename(
            columns={
                "request_count":
                    "day_request_count",
            }
        ),
        on="date",
        how="left",
    )
)


top_day_service_contributors[
    "share_of_day_demand_pct"
] = (
    top_day_service_contributors[
        "request_count"
    ]
    / top_day_service_contributors[
        "day_request_count"
    ]
    * 100
)


top_day_service_contributors = (
    top_day_service_contributors
    .sort_values(
        [
            "date",
            "request_count",
        ],
        ascending=[
            True,
            False,
        ],
    )
    .groupby(
        "date",
        group_keys=False,
    )
    .head(5)
    .reset_index(drop=True)
)


# =============================================================================
# OUTPUTS
# =============================================================================

daily_profile.to_csv(
    OUTPUT_DIR
    / "temporal_daily_profile.csv",
    index=False,
)


monthly_profile.to_csv(
    OUTPUT_DIR
    / "temporal_monthly_profile.csv",
    index=False,
)


weekday_profile.to_csv(
    OUTPUT_DIR
    / "temporal_weekday_profile.csv",
    index=False,
)


hourly_profile.to_csv(
    OUTPUT_DIR
    / "temporal_hourly_profile.csv",
    index=False,
)


service_month_profile.to_csv(
    OUTPUT_DIR
    / "temporal_service_month_profile.csv",
    index=False,
)


service_day_profile.to_csv(
    OUTPUT_DIR
    / "temporal_service_day_profile.csv",
    index=False,
)


top_day_service_contributors.to_csv(
    OUTPUT_DIR
    / "temporal_top_day_service_contributors.csv",
    index=False,
)


# =============================================================================
# PRINT RESULTS
# =============================================================================

section(
    "2 - MONTHLY DEMAND"
)


print(
    monthly_profile[
        [
            "month",
            "request_count",
            "observed_days",
            "requests_per_observed_day",
            "backlog_count",
            "current_open_share_pct",
        ]
    ]
    .to_string(
        index=False
    )
)


section(
    "3 - DAY-OF-WEEK DEMAND"
)


print(
    weekday_profile[
        [
            "day_of_week",
            "request_count",
            "observed_days",
            "requests_per_observed_day",
            "share_of_total_demand_pct",
        ]
    ]
    .to_string(
        index=False
    )
)


section(
    "4 - HOURLY DEMAND"
)


print(
    hourly_profile[
        [
            "hour",
            "request_count",
            "share_of_total_demand_pct",
        ]
    ]
    .to_string(
        index=False
    )
)


section(
    "5 - HIGHEST-DEMAND INDIVIDUAL DAYS"
)


print(
    top_days[
        [
            "date",
            "day_of_week",
            "request_count",
        ]
    ]
    .to_string(
        index=False
    )
)


section(
    "6 - TOP SERVICE CONTRIBUTORS ON HIGHEST-DEMAND DAYS"
)


print(
    top_day_service_contributors[
        [
            "date",
            "service_problem",
            "request_count",
            "day_request_count",
            "share_of_day_demand_pct",
        ]
    ]
    .sort_values(
        [
            "date",
            "request_count",
        ],
        ascending=[
            True,
            False,
        ],
    )
    .to_string(
        index=False
    )
)


section(
    "7 - HIGHEST SERVICE x MONTH DEMAND"
)


top_service_month = (
    service_month_profile
    .sort_values(
        "request_count",
        ascending=False,
    )
    .head(30)
)


print(
    top_service_month[
        [
            "service_problem",
            "month",
            "request_count",
            "requests_per_observed_day",
            "share_of_month_demand_pct",
            "current_open_share_pct",
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

    "URBAN SERVICE RELIABILITY - DAY 2 TEMPORAL x SERVICE ANALYSIS",

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

    f"Invalid Created rows:    "
    f"{invalid_created_rows:,}",

    "",

    "INTERPRETATION RULES",

    "- August is partial through August 29; "
    "use requests per observed day for fairer month comparison.",

    "- Current-open share by creation month is a cohort measure, "
    "not a universal performance rate.",

    "- Recent creation cohorts have had less time to close "
    "than older cohorts.",

    "- Individual demand spikes remain descriptive until their "
    "service composition is investigated.",

    "- Partial-year data cannot establish full annual seasonality.",
]


(
    OUTPUT_DIR
    / "temporal_service_analysis_summary.txt"
).write_text(
    "\n".join(
        summary_lines
    ),
    encoding="utf-8",
)


section(
    "DAY 2 - STEP 4 ANALYSIS COMPLETE"
)


print(
    "Outputs written:"
)

print(
    OUTPUT_DIR
    / "temporal_daily_profile.csv"
)

print(
    OUTPUT_DIR
    / "temporal_monthly_profile.csv"
)

print(
    OUTPUT_DIR
    / "temporal_weekday_profile.csv"
)

print(
    OUTPUT_DIR
    / "temporal_hourly_profile.csv"
)

print(
    OUTPUT_DIR
    / "temporal_service_month_profile.csv"
)

print(
    OUTPUT_DIR
    / "temporal_service_day_profile.csv"
)

print(
    OUTPUT_DIR
    / "temporal_top_day_service_contributors.csv"
)

print(
    OUTPUT_DIR
    / "temporal_service_analysis_summary.txt"
)

print()

print(
    "TEMPORAL x SERVICE ANALYSIS PASSED"
)