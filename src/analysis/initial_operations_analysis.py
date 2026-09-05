from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

SILVER_DIR = (
    PROJECT_ROOT
    / "data"
    / "silver"
    / "service_requests_2026_ytd"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "analysis"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# ANALYTICAL THRESHOLDS
# ============================================================

# Avoid drawing conclusions from tiny service categories.
MIN_SERVICE_REQUESTS_FOR_RATE = 5_000

MIN_VALID_RESOLUTIONS_FOR_DURATION = 2_000


# ============================================================
# HELPERS
# ============================================================

def update_counter(
    counter: Counter,
    series: pd.Series,
) -> None:

    values = (
        series
        .fillna("<UNKNOWN>")
        .astype(str)
        .value_counts()
        .to_dict()
    )

    counter.update(values)


def concatenate_arrays(
    arrays: list[np.ndarray],
) -> np.ndarray:

    if not arrays:
        return np.array(
            [],
            dtype="float64",
        )

    return np.concatenate(arrays)


def percentile(
    values: np.ndarray,
    q: float,
) -> float | None:

    if len(values) == 0:
        return None

    return float(
        np.percentile(
            values,
            q,
        )
    )


def safe_pct(
    numerator: int,
    denominator: int,
) -> float:

    if denominator == 0:
        return 0.0

    return (
        numerator
        / denominator
        * 100
    )


# ============================================================
# FILES
# ============================================================

part_files = sorted(
    SILVER_DIR.glob("part_*.parquet")
)

if not part_files:
    raise RuntimeError(
        f"No Silver files found in {SILVER_DIR}"
    )


# ============================================================
# COUNTERS
# ============================================================

total_requests = 0
closed_requests = 0
backlog_requests = 0
valid_resolution_requests = 0


status_counts = Counter()

service_total = Counter()
service_closed = Counter()
service_backlog = Counter()

agency_total = Counter()
agency_closed = Counter()
agency_backlog = Counter()

borough_total = Counter()
borough_backlog = Counter()

zip_total = Counter()
service_zip_total = Counter()

daily_counts = Counter()
day_of_week_counts = Counter()
hour_counts = Counter()
month_counts = Counter()


# ============================================================
# DISTRIBUTION ARRAYS
# ============================================================

resolution_arrays = []

resolution_by_service = defaultdict(list)
resolution_by_agency = defaultdict(list)
resolution_by_borough = defaultdict(list)

backlog_age_arrays = []
backlog_age_by_service = defaultdict(list)


# ============================================================
# READ SILVER
# ============================================================

print("\n" + "=" * 84)
print("URBAN SERVICE RELIABILITY — INITIAL OPERATIONS ANALYSIS")
print("=" * 84)

print(f"Silver parts: {len(part_files)}")


columns = [
    "unique_key",
    "created_at",
    "status",

    "agency",
    "service_problem",

    "borough",
    "incident_zip_clean",

    "is_closed",
    "is_backlog",

    "resolution_duration_valid",
    "resolution_hours",

    "request_age_days",
]


for part_number, file_path in enumerate(
    part_files,
    start=1,
):

    print(
        f"[{part_number:02d}/{len(part_files):02d}] "
        f"{file_path.name}"
    )

    df = pd.read_parquet(
        file_path,
        columns=columns,
    )

    rows = len(df)

    total_requests += rows


    # --------------------------------------------------------
    # SAFE WORKING DIMENSIONS
    # --------------------------------------------------------

    service = (
        df["service_problem"]
        .fillna("<UNKNOWN>")
        .astype(str)
    )

    agency = (
        df["agency"]
        .fillna("<UNKNOWN>")
        .astype(str)
    )

    borough = (
        df["borough"]
        .fillna("<UNKNOWN>")
        .astype(str)
    )

    status = (
        df["status"]
        .fillna("<UNKNOWN>")
        .astype(str)
    )


    # --------------------------------------------------------
    # BASIC COUNTS
    # --------------------------------------------------------

    closed_mask = (
        df["is_closed"]
        .fillna(False)
        .astype(bool)
    )

    backlog_mask = (
        df["is_backlog"]
        .fillna(False)
        .astype(bool)
    )


    closed_requests += int(
        closed_mask.sum()
    )

    backlog_requests += int(
        backlog_mask.sum()
    )


    update_counter(
        status_counts,
        status,
    )

    update_counter(
        service_total,
        service,
    )

    update_counter(
        agency_total,
        agency,
    )

    update_counter(
        borough_total,
        borough,
    )


    # --------------------------------------------------------
    # CLOSED COUNTS
    # --------------------------------------------------------

    if closed_mask.any():

        update_counter(
            service_closed,
            service[closed_mask],
        )

        update_counter(
            agency_closed,
            agency[closed_mask],
        )


    # --------------------------------------------------------
    # BACKLOG COUNTS
    # --------------------------------------------------------

    if backlog_mask.any():

        update_counter(
            service_backlog,
            service[backlog_mask],
        )

        update_counter(
            agency_backlog,
            agency[backlog_mask],
        )

        update_counter(
            borough_backlog,
            borough[backlog_mask],
        )


        backlog_age = pd.to_numeric(
            df.loc[
                backlog_mask,
                "request_age_days",
            ],
            errors="coerce",
        )

        valid_age = (
            backlog_age
            .dropna()
            .to_numpy(
                dtype="float64"
            )
        )

        if len(valid_age):
            backlog_age_arrays.append(
                valid_age
            )


        backlog_temp = pd.DataFrame(
            {
                "service":
                    service[backlog_mask],

                "age":
                    backlog_age,
            }
        )

        for service_name, group in (
            backlog_temp
            .dropna(
                subset=["age"]
            )
            .groupby(
                "service",
                sort=False,
            )
        ):

            backlog_age_by_service[
                str(service_name)
            ].append(
                group["age"]
                .to_numpy(
                    dtype="float64"
                )
            )


    # --------------------------------------------------------
    # RESOLUTION DURATION
    # --------------------------------------------------------

    valid_resolution_mask = (
        df[
            "resolution_duration_valid"
        ]
        .fillna(False)
        .astype(bool)
    )


    valid_resolution_requests += int(
        valid_resolution_mask.sum()
    )


    if valid_resolution_mask.any():

        resolution_temp = pd.DataFrame(
            {
                "service":
                    service[
                        valid_resolution_mask
                    ],

                "agency":
                    agency[
                        valid_resolution_mask
                    ],

                "borough":
                    borough[
                        valid_resolution_mask
                    ],

                "resolution_hours":
                    pd.to_numeric(
                        df.loc[
                            valid_resolution_mask,
                            "resolution_hours",
                        ],
                        errors="coerce",
                    ),
            }
        ).dropna(
            subset=["resolution_hours"]
        )


        all_values = (
            resolution_temp[
                "resolution_hours"
            ]
            .to_numpy(
                dtype="float64"
            )
        )

        if len(all_values):
            resolution_arrays.append(
                all_values
            )


        for service_name, group in (
            resolution_temp.groupby(
                "service",
                sort=False,
            )
        ):

            resolution_by_service[
                str(service_name)
            ].append(
                group[
                    "resolution_hours"
                ].to_numpy(
                    dtype="float64"
                )
            )


        for agency_name, group in (
            resolution_temp.groupby(
                "agency",
                sort=False,
            )
        ):

            resolution_by_agency[
                str(agency_name)
            ].append(
                group[
                    "resolution_hours"
                ].to_numpy(
                    dtype="float64"
                )
            )


        for borough_name, group in (
            resolution_temp.groupby(
                "borough",
                sort=False,
            )
        ):

            resolution_by_borough[
                str(borough_name)
            ].append(
                group[
                    "resolution_hours"
                ].to_numpy(
                    dtype="float64"
                )
            )


    # --------------------------------------------------------
    # GEOGRAPHIC REQUEST COUNTS
    # --------------------------------------------------------

    zip_series = (
        df["incident_zip_clean"]
        .astype("string")
    )

    valid_zip = (
        zip_series.notna()
    )


    if valid_zip.any():

        update_counter(
            zip_total,
            zip_series[
                valid_zip
            ],
        )


        service_zip_df = pd.DataFrame(
            {
                "service":
                    service[valid_zip],

                "zip":
                    zip_series[
                        valid_zip
                    ].astype(str),
            }
        )


        combinations = (
            service_zip_df
            .value_counts()
        )


        for (
            service_name,
            zip_code
        ), count in combinations.items():

            service_zip_total[
                (
                    str(service_name),
                    str(zip_code),
                )
            ] += int(count)


    # --------------------------------------------------------
    # TEMPORAL COUNTS
    # --------------------------------------------------------

    created = pd.to_datetime(
        df["created_at"],
        errors="coerce",
    )


    valid_created = (
        created.notna()
    )


    if valid_created.any():

        created_valid = (
            created[
                valid_created
            ]
        )


        update_counter(
            daily_counts,
            created_valid.dt.strftime(
                "%Y-%m-%d"
            ),
        )

        update_counter(
            day_of_week_counts,
            created_valid.dt.day_name(),
        )

        update_counter(
            hour_counts,
            created_valid.dt.hour,
        )

        update_counter(
            month_counts,
            created_valid.dt.strftime(
                "%Y-%m"
            ),
        )


# ============================================================
# OVERALL DISTRIBUTIONS
# ============================================================

all_resolution_hours = concatenate_arrays(
    resolution_arrays
)

all_backlog_age_days = concatenate_arrays(
    backlog_age_arrays
)


# ============================================================
# SERVICE PERFORMANCE TABLE
# ============================================================

service_rows = []


for service_name, request_count in (
    service_total.items()
):

    backlog_count = int(
        service_backlog[
            service_name
        ]
    )

    closed_count = int(
        service_closed[
            service_name
        ]
    )

    resolution_values = (
        concatenate_arrays(
            resolution_by_service.get(
                service_name,
                [],
            )
        )
    )

    backlog_ages = (
        concatenate_arrays(
            backlog_age_by_service.get(
                service_name,
                [],
            )
        )
    )


    service_rows.append(
        {
            "service_problem":
                service_name,

            "request_count":
                request_count,

            "closed_count":
                closed_count,

            "backlog_count":
                backlog_count,

            "backlog_rate_pct":
                safe_pct(
                    backlog_count,
                    request_count,
                ),

            "valid_resolution_count":
                len(
                    resolution_values
                ),

            "median_resolution_hours":
                percentile(
                    resolution_values,
                    50,
                ),

            "p75_resolution_hours":
                percentile(
                    resolution_values,
                    75,
                ),

            "p90_resolution_hours":
                percentile(
                    resolution_values,
                    90,
                ),

            "median_backlog_age_days":
                percentile(
                    backlog_ages,
                    50,
                ),

            "p90_backlog_age_days":
                percentile(
                    backlog_ages,
                    90,
                ),
        }
    )


service_df = pd.DataFrame(
    service_rows
)


service_df[
    "median_resolution_days"
] = (
    service_df[
        "median_resolution_hours"
    ]
    /
    24
)


service_df[
    "p90_resolution_days"
] = (
    service_df[
        "p90_resolution_hours"
    ]
    /
    24
)


service_df = service_df.sort_values(
    "request_count",
    ascending=False,
)


service_df.to_csv(
    OUTPUT_DIR
    / "service_operations_summary.csv",
    index=False,
)


# ============================================================
# AGENCY TABLE
# ============================================================

agency_rows = []


for agency_name, request_count in (
    agency_total.items()
):

    resolution_values = (
        concatenate_arrays(
            resolution_by_agency.get(
                agency_name,
                [],
            )
        )
    )

    backlog_count = int(
        agency_backlog[
            agency_name
        ]
    )


    agency_rows.append(
        {
            "agency":
                agency_name,

            "request_count":
                request_count,

            "closed_count":
                int(
                    agency_closed[
                        agency_name
                    ]
                ),

            "backlog_count":
                backlog_count,

            "backlog_rate_pct":
                safe_pct(
                    backlog_count,
                    request_count,
                ),

            "valid_resolution_count":
                len(
                    resolution_values
                ),

            "median_resolution_hours":
                percentile(
                    resolution_values,
                    50,
                ),

            "p90_resolution_hours":
                percentile(
                    resolution_values,
                    90,
                ),
        }
    )


agency_df = (
    pd.DataFrame(
        agency_rows
    )
    .sort_values(
        "request_count",
        ascending=False,
    )
)


agency_df[
    "median_resolution_days"
] = (
    agency_df[
        "median_resolution_hours"
    ]
    /
    24
)


agency_df[
    "p90_resolution_days"
] = (
    agency_df[
        "p90_resolution_hours"
    ]
    /
    24
)


agency_df.to_csv(
    OUTPUT_DIR
    / "agency_operations_summary.csv",
    index=False,
)


# ============================================================
# BOROUGH TABLE
# ============================================================

borough_rows = []


for borough_name, request_count in (
    borough_total.items()
):

    resolution_values = (
        concatenate_arrays(
            resolution_by_borough.get(
                borough_name,
                [],
            )
        )
    )


    backlog_count = int(
        borough_backlog[
            borough_name
        ]
    )


    borough_rows.append(
        {
            "borough":
                borough_name,

            "request_count":
                request_count,

            "backlog_count":
                backlog_count,

            "backlog_rate_pct":
                safe_pct(
                    backlog_count,
                    request_count,
                ),

            "median_resolution_hours":
                percentile(
                    resolution_values,
                    50,
                ),

            "p90_resolution_hours":
                percentile(
                    resolution_values,
                    90,
                ),
        }
    )


borough_df = (
    pd.DataFrame(
        borough_rows
    )
    .sort_values(
        "request_count",
        ascending=False,
    )
)


borough_df.to_csv(
    OUTPUT_DIR
    / "borough_operations_summary.csv",
    index=False,
)


# ============================================================
# ZIP HOTSPOTS
# ============================================================

zip_df = pd.DataFrame(
    [
        {
            "incident_zip":
                zip_code,

            "request_count":
                count,
        }

        for zip_code, count
        in zip_total.items()
    ]
).sort_values(
    "request_count",
    ascending=False,
)


zip_df.to_csv(
    OUTPUT_DIR
    / "zip_request_volume.csv",
    index=False,
)


service_zip_df = pd.DataFrame(
    [
        {
            "service_problem":
                service_name,

            "incident_zip":
                zip_code,

            "request_count":
                count,
        }

        for (
            service_name,
            zip_code
        ), count

        in service_zip_total.items()
    ]
).sort_values(
    "request_count",
    ascending=False,
)


service_zip_df.to_csv(
    OUTPUT_DIR
    / "service_zip_hotspots.csv",
    index=False,
)


# ============================================================
# TEMPORAL TABLES
# ============================================================

daily_df = pd.DataFrame(
    [
        {
            "date": date,
            "request_count": count,
        }

        for date, count
        in daily_counts.items()
    ]
).sort_values(
    "date"
)


daily_df.to_csv(
    OUTPUT_DIR
    / "daily_request_demand.csv",
    index=False,
)


dow_order = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


dow_df = pd.DataFrame(
    [
        {
            "day_of_week":
                day,

            "request_count":
                day_of_week_counts[
                    day
                ],
        }

        for day in dow_order
    ]
)


dow_df.to_csv(
    OUTPUT_DIR
    / "day_of_week_demand.csv",
    index=False,
)


hour_df = pd.DataFrame(
    [
        {
            "hour":
                hour,

            "request_count":
                count,
        }

        for hour, count
        in sorted(
            hour_counts.items(),
            key=lambda x: int(x[0]),
        )
    ]
)


hour_df.to_csv(
    OUTPUT_DIR
    / "hourly_request_demand.csv",
    index=False,
)


month_df = pd.DataFrame(
    [
        {
            "month":
                month,

            "request_count":
                count,
        }

        for month, count
        in sorted(
            month_counts.items()
        )
    ]
)


month_df.to_csv(
    OUTPUT_DIR
    / "monthly_request_demand.csv",
    index=False,
)


# ============================================================
# KPI SUMMARY
# ============================================================

days_observed = len(
    daily_counts
)


top_services = (
    service_df.head(10)
)


top_5_share = safe_pct(
    int(
        service_df
        .head(5)[
            "request_count"
        ]
        .sum()
    ),
    total_requests,
)


top_10_share = safe_pct(
    int(
        service_df
        .head(10)[
            "request_count"
        ]
        .sum()
    ),
    total_requests,
)


kpis = {

    "total_requests":
        total_requests,

    "closed_requests":
        closed_requests,

    "current_backlog":
        backlog_requests,

    "backlog_rate_pct":
        safe_pct(
            backlog_requests,
            total_requests,
        ),

    "valid_resolution_requests":
        valid_resolution_requests,

    "observed_calendar_days":
        days_observed,

    "requests_per_day":
        (
            total_requests
            /
            days_observed
            if days_observed
            else None
        ),

    "median_resolution_hours":
        percentile(
            all_resolution_hours,
            50,
        ),

    "p75_resolution_hours":
        percentile(
            all_resolution_hours,
            75,
        ),

    "p90_resolution_hours":
        percentile(
            all_resolution_hours,
            90,
        ),

    "median_backlog_age_days":
        percentile(
            all_backlog_age_days,
            50,
        ),

    "p75_backlog_age_days":
        percentile(
            all_backlog_age_days,
            75,
        ),

    "p90_backlog_age_days":
        percentile(
            all_backlog_age_days,
            90,
        ),

    "top_5_service_share_pct":
        top_5_share,

    "top_10_service_share_pct":
        top_10_share,
}


with (
    OUTPUT_DIR
    / "initial_kpis.json"
).open(
    "w",
    encoding="utf-8",
) as f:

    json.dump(
        kpis,
        f,
        indent=2,
    )


# ============================================================
# PRINT — KPI SUMMARY
# ============================================================

print("\n" + "=" * 84)
print("1 — INITIAL OPERATIONAL KPIs")
print("=" * 84)

print(
    f"Total Requests:              "
    f"{total_requests:,}"
)

print(
    f"Closed Requests:             "
    f"{closed_requests:,}"
)

print(
    f"Current Backlog:             "
    f"{backlog_requests:,}"
)

print(
    f"Backlog Rate:                "
    f"{kpis['backlog_rate_pct']:.2f}%"
)

print(
    f"Observed Calendar Days:      "
    f"{days_observed:,}"
)

print(
    f"Requests / Day:              "
    f"{kpis['requests_per_day']:,.1f}"
)

print(
    f"\nMedian Resolution:           "
    f"{kpis['median_resolution_hours']:.2f} hours"
)

print(
    f"P75 Resolution:              "
    f"{kpis['p75_resolution_hours']:.2f} hours"
)

print(
    f"P90 Resolution:              "
    f"{kpis['p90_resolution_hours']:.2f} hours"
)

print(
    f"\nMedian Backlog Age:          "
    f"{kpis['median_backlog_age_days']:.2f} days"
)

print(
    f"P75 Backlog Age:             "
    f"{kpis['p75_backlog_age_days']:.2f} days"
)

print(
    f"P90 Backlog Age:             "
    f"{kpis['p90_backlog_age_days']:.2f} days"
)

print(
    f"\nTop 5 Service Share:         "
    f"{top_5_share:.2f}%"
)

print(
    f"Top 10 Service Share:        "
    f"{top_10_share:.2f}%"
)


# ============================================================
# PRINT — DEMAND
# ============================================================

print("\n" + "=" * 84)
print("2 — HIGHEST-DEMAND SERVICE PROBLEMS")
print("=" * 84)

print(
    service_df[
        [
            "service_problem",
            "request_count",
            "backlog_count",
            "backlog_rate_pct",
        ]
    ]
    .head(15)
    .to_string(
        index=False,
    )
)


# ============================================================
# PRINT — BACKLOG COUNT
# ============================================================

print("\n" + "=" * 84)
print("3 — LARGEST CURRENT BACKLOGS")
print("=" * 84)

print(
    service_df[
        [
            "service_problem",
            "request_count",
            "backlog_count",
            "backlog_rate_pct",
            "median_backlog_age_days",
            "p90_backlog_age_days",
        ]
    ]
    .sort_values(
        "backlog_count",
        ascending=False,
    )
    .head(15)
    .to_string(
        index=False,
    )
)


# ============================================================
# PRINT — BACKLOG RATE
# ============================================================

print("\n" + "=" * 84)
print("4 — HIGHEST BACKLOG RATE — MATERIAL SERVICES")
print("=" * 84)

material_services = (
    service_df[
        service_df[
            "request_count"
        ]
        >=
        MIN_SERVICE_REQUESTS_FOR_RATE
    ]
)


print(
    material_services[
        [
            "service_problem",
            "request_count",
            "backlog_count",
            "backlog_rate_pct",
            "median_backlog_age_days",
            "p90_backlog_age_days",
        ]
    ]
    .sort_values(
        "backlog_rate_pct",
        ascending=False,
    )
    .head(15)
    .to_string(
        index=False,
    )
)


# ============================================================
# PRINT — RESOLUTION PERFORMANCE
# ============================================================

print("\n" + "=" * 84)
print("5 — LONGEST RESOLUTION — MATERIAL SERVICES")
print("=" * 84)

duration_services = (
    service_df[
        service_df[
            "valid_resolution_count"
        ]
        >=
        MIN_VALID_RESOLUTIONS_FOR_DURATION
    ]
)


print(
    duration_services[
        [
            "service_problem",
            "request_count",
            "valid_resolution_count",
            "median_resolution_days",
            "p90_resolution_days",
        ]
    ]
    .sort_values(
        "median_resolution_days",
        ascending=False,
    )
    .head(15)
    .to_string(
        index=False,
    )
)


print("\nHighest P90 resolution times:")

print(
    duration_services[
        [
            "service_problem",
            "request_count",
            "valid_resolution_count",
            "median_resolution_days",
            "p90_resolution_days",
        ]
    ]
    .sort_values(
        "p90_resolution_days",
        ascending=False,
    )
    .head(15)
    .to_string(
        index=False,
    )
)


# ============================================================
# PRINT — AGENCIES
# ============================================================

print("\n" + "=" * 84)
print("6 — AGENCY OPERATIONS PROFILE")
print("=" * 84)

print(
    agency_df[
        [
            "agency",
            "request_count",
            "backlog_count",
            "backlog_rate_pct",
            "median_resolution_days",
            "p90_resolution_days",
        ]
    ]
    .to_string(
        index=False,
    )
)


# ============================================================
# PRINT — GEOGRAPHY
# ============================================================

print("\n" + "=" * 84)
print("7 — HIGHEST REQUEST-VOLUME ZIP CODES")
print("=" * 84)

print(
    zip_df
    .head(15)
    .to_string(
        index=False,
    )
)


print(
    "\nHighest service × ZIP concentrations:"
)

print(
    service_zip_df
    .head(20)
    .to_string(
        index=False,
    )
)


# ============================================================
# PRINT — TEMPORAL
# ============================================================

print("\n" + "=" * 84)
print("8 — TEMPORAL DEMAND")
print("=" * 84)

print("\nDay of week:")

print(
    dow_df.to_string(
        index=False,
    )
)


print("\nHourly demand:")

print(
    hour_df.to_string(
        index=False,
    )
)


print("\nMonthly demand:")

print(
    month_df.to_string(
        index=False,
    )
)


print("\nHighest-demand individual days:")

print(
    daily_df
    .sort_values(
        "request_count",
        ascending=False,
    )
    .head(15)
    .to_string(
        index=False,
    )
)


# ============================================================
# COMPLETE
# ============================================================

print("\n" + "=" * 84)
print("INITIAL OPERATIONS ANALYSIS COMPLETE")
print("=" * 84)

print(
    f"Outputs → {OUTPUT_DIR}"
)