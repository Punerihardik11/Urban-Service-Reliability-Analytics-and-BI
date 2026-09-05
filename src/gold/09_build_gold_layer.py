from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import json

import numpy as np
import pandas as pd
import pyarrow.parquet as pq


# =============================================================================
# CONFIG
# =============================================================================

ROOT = Path(__file__).resolve().parents[2]

SILVER_DIR = ROOT / "data" / "silver" / "service_requests_2026_ytd"

GOLD_DIR = (
    ROOT
    / "data"
    / "gold"
    / "nyc_311_2026_ytd"
)

GOLD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

EXPECTED_TOTAL = 2_644_153
EXPECTED_CLOSED = 2_457_717
EXPECTED_BACKLOG = 186_436
EXPECTED_VALID_RESOLUTION = 2_457_340

SCOPE_START_DATE = "2026-01-01"
SCOPE_END_EXCLUSIVE = "2026-08-30"
SCOPE_LAST_INCLUDED_DATE = "2026-08-29"

OBSERVED_DAYS = 241

SYSTEMATIC_60D_MIN_VALID = 1_000
SYSTEMATIC_60D_MIN_SHARE_PCT = 40.0


# =============================================================================
# HELPERS
# =============================================================================

def section(title: str) -> None:
    print()
    print("=" * 118)
    print(title)
    print("=" * 118)


def safe_label(
    series: pd.Series,
    unknown: str = "Unknown",
) -> pd.Series:

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


def append_array(
    store: dict,
    key,
    values,
) -> None:

    arr = np.asarray(
        values,
        dtype="float64",
    )

    if len(arr):
        store[key].append(arr)


def combine_arrays(
    arrays: list[np.ndarray],
) -> np.ndarray:

    if not arrays:
        return np.array(
            [],
            dtype="float64",
        )

    return np.concatenate(
        arrays
    )


def percentile(
    values: np.ndarray,
    q: float,
) -> float:

    if len(values) == 0:
        return np.nan

    return float(
        np.percentile(
            values,
            q,
        )
    )


def age_metrics(
    values: np.ndarray,
) -> dict:

    if len(values) == 0:

        return {
            "median_backlog_age_days":
                np.nan,

            "p75_backlog_age_days":
                np.nan,

            "p90_backlog_age_days":
                np.nan,

            "backlog_30d_plus":
                0,

            "backlog_60d_plus":
                0,

            "backlog_90d_plus":
                0,

            "backlog_180d_plus":
                0,

            "old_backlog_share_60d_plus_pct":
                np.nan,
        }


    count = len(values)

    c30 = int(
        (values >= 30)
        .sum()
    )

    c60 = int(
        (values >= 60)
        .sum()
    )

    c90 = int(
        (values >= 90)
        .sum()
    )

    c180 = int(
        (values >= 180)
        .sum()
    )


    return {

        "median_backlog_age_days":
            percentile(
                values,
                50,
            ),

        "p75_backlog_age_days":
            percentile(
                values,
                75,
            ),

        "p90_backlog_age_days":
            percentile(
                values,
                90,
            ),

        "backlog_30d_plus":
            c30,

        "backlog_60d_plus":
            c60,

        "backlog_90d_plus":
            c90,

        "backlog_180d_plus":
            c180,

        "old_backlog_share_60d_plus_pct":
            c60
            / count
            * 100,
    }


def resolution_metrics(
    values: np.ndarray,
) -> dict:

    if len(values) == 0:

        return {

            "valid_resolution_count":
                0,

            "median_resolution_hours":
                np.nan,

            "p75_resolution_hours":
                np.nan,

            "p90_resolution_hours":
                np.nan,

            "median_resolution_days":
                np.nan,

            "p90_resolution_days":
                np.nan,

            "resolution_59_5_60_5_count":
                0,

            "resolution_59_5_60_5_share_pct":
                np.nan,
        }


    days = (
        values
        / 24
    )


    in_60_window = (
        (days >= 59.5)
        &
        (days <= 60.5)
    )


    window_count = int(
        in_60_window.sum()
    )


    return {

        "valid_resolution_count":
            len(values),

        "median_resolution_hours":
            percentile(
                values,
                50,
            ),

        "p75_resolution_hours":
            percentile(
                values,
                75,
            ),

        "p90_resolution_hours":
            percentile(
                values,
                90,
            ),

        "median_resolution_days":
            percentile(
                days,
                50,
            ),

        "p90_resolution_days":
            percentile(
                days,
                90,
            ),

        "resolution_59_5_60_5_count":
            window_count,

        "resolution_59_5_60_5_share_pct":
            window_count
            / len(values)
            * 100,
    }


def write_table(
    df: pd.DataFrame,
    name: str,
) -> None:

    parquet_path = (
        GOLD_DIR
        / f"{name}.parquet"
    )

    csv_path = (
        GOLD_DIR
        / f"{name}.csv"
    )


    df.to_parquet(
        parquet_path,
        index=False,
        engine="pyarrow",
    )


    df.to_csv(
        csv_path,
        index=False,
    )


    print(
        f"{name:<34} "
        f"{len(df):>10,} rows"
    )


# =============================================================================
# DISCOVER SILVER
# =============================================================================

section(
    "URBAN SERVICE RELIABILITY - BUILD GOLD LAYER"
)


parts = sorted(
    SILVER_DIR.glob(
        "part_*.parquet"
    )
)


if not parts:

    raise FileNotFoundError(
        f"No Silver parquet parts found in:\n"
        f"{SILVER_DIR}"
    )


columns = (
    pq.ParquetFile(
        parts[0]
    )
    .schema_arrow
    .names
)


required_columns = [

    "agency",
    "service_problem",
    "status",
    "created_at",
    "incident_zip",
    "borough",
    "request_age_days",
    "resolution_duration_valid",
    "resolution_hours",
]


missing = [

    col
    for col
    in required_columns
    if col not in columns
]


if missing:

    raise KeyError(
        "Required Silver columns missing:\n"
        f"{missing}"
    )


print(
    f"Silver parts:            "
    f"{len(parts)}"
)

print(
    "Required Silver schema: PASS"
)


# =============================================================================
# ACCUMULATORS
# =============================================================================

total_rows = 0
closed_rows = 0
backlog_rows = 0
valid_resolution_rows = 0
invalid_created_rows = 0


agency_service_requests = Counter()
agency_service_backlog = Counter()

zip_requests = Counter()
zip_backlog = Counter()

agency_service_zip_requests = Counter()
agency_service_zip_backlog = Counter()


agency_service_backlog_ages = defaultdict(list)
zip_backlog_ages = defaultdict(list)
agency_service_zip_backlog_ages = defaultdict(list)


agency_service_resolution = defaultdict(list)
all_resolution_arrays = []

all_backlog_age_arrays = defaultdict(list)


service_daily_parts = []
service_zip_daily_parts = []


# =============================================================================
# SCAN SILVER
# =============================================================================

section(
    "1 - SCANNING SILVER"
)


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
        columns=required_columns,
        engine="pyarrow",
    )


    total_rows += len(df)


    agency = safe_label(
        df["agency"]
    )


    service = safe_label(
        df["service_problem"]
    )


    status = safe_label(
        df["status"]
    )


    incident_zip = safe_label(
        df["incident_zip"]
    )


    borough = safe_label(
        df["borough"]
    )


    created = pd.to_datetime(
        df["created_at"],
        errors="coerce",
    )


    invalid_created_rows += int(
        created.isna().sum()
    )


    request_age = pd.to_numeric(
        df["request_age_days"],
        errors="coerce",
    )


    resolution_hours = pd.to_numeric(
        df["resolution_hours"],
        errors="coerce",
    )


    is_closed = (
        status
        .str
        .casefold()
        .eq("closed")
    )


    is_backlog = ~is_closed


    valid_resolution = (
        df[
            "resolution_duration_valid"
        ]
        .fillna(False)
        .astype(bool)
    )


    closed_rows += int(
        is_closed.sum()
    )


    backlog_rows += int(
        is_backlog.sum()
    )


    valid_resolution_rows += int(
        valid_resolution.sum()
    )


    # =========================================================================
    # REQUEST COUNTS
    # =========================================================================

    as_frame = pd.DataFrame(
        {
            "agency":
                agency.values,

            "service_problem":
                service.values,
        }
    )


    agency_service_requests.update(
        as_frame
        .value_counts()
        .to_dict()
    )


    zip_requests.update(
        incident_zip
        .value_counts()
        .to_dict()
    )


    asz_frame = pd.DataFrame(
        {
            "agency":
                agency.values,

            "service_problem":
                service.values,

            "incident_zip":
                incident_zip.values,
        }
    )


    agency_service_zip_requests.update(
        asz_frame
        .value_counts()
        .to_dict()
    )


    # =========================================================================
    # BACKLOG
    # =========================================================================

    if is_backlog.any():

        backlog_agency = (
            agency
            .loc[is_backlog]
        )

        backlog_service = (
            service
            .loc[is_backlog]
        )

        backlog_zip = (
            incident_zip
            .loc[is_backlog]
        )

        backlog_age = (
            request_age
            .loc[is_backlog]
        )


        if (
            backlog_age.isna().any()
            or
            backlog_age.lt(0).any()
        ):

            raise RuntimeError(
                "Invalid backlog age encountered "
                "in Silver."
            )


        backlog_as = pd.DataFrame(
            {
                "agency":
                    backlog_agency.values,

                "service_problem":
                    backlog_service.values,
            }
        )


        agency_service_backlog.update(
            backlog_as
            .value_counts()
            .to_dict()
        )


        zip_backlog.update(
            backlog_zip
            .value_counts()
            .to_dict()
        )


        backlog_asz = pd.DataFrame(
            {
                "agency":
                    backlog_agency.values,

                "service_problem":
                    backlog_service.values,

                "incident_zip":
                    backlog_zip.values,
            }
        )


        agency_service_zip_backlog.update(
            backlog_asz
            .value_counts()
            .to_dict()
        )


        append_array(
            all_backlog_age_arrays,
            "__city__",
            backlog_age.values,
        )


        temp_backlog = pd.DataFrame(
            {
                "agency":
                    backlog_agency.values,

                "service_problem":
                    backlog_service.values,

                "incident_zip":
                    backlog_zip.values,

                "backlog_age_days":
                    backlog_age.values,
            }
        )


        for (
            agency_name,
            service_name,
        ), group in temp_backlog.groupby(
            [
                "agency",
                "service_problem",
            ],
            sort=False,
        ):

            append_array(
                agency_service_backlog_ages,
                (
                    agency_name,
                    service_name,
                ),
                group[
                    "backlog_age_days"
                ].values,
            )


        for zip_name, group in temp_backlog.groupby(
            "incident_zip",
            sort=False,
        ):

            append_array(
                zip_backlog_ages,
                zip_name,
                group[
                    "backlog_age_days"
                ].values,
            )


        for (
            agency_name,
            service_name,
            zip_name,
        ), group in temp_backlog.groupby(
            [
                "agency",
                "service_problem",
                "incident_zip",
            ],
            sort=False,
        ):

            append_array(
                agency_service_zip_backlog_ages,
                (
                    agency_name,
                    service_name,
                    zip_name,
                ),
                group[
                    "backlog_age_days"
                ].values,
            )


    # =========================================================================
    # VALID RESOLUTION
    # =========================================================================

    if valid_resolution.any():

        valid_hours = (
            resolution_hours
            .loc[valid_resolution]
        )


        if valid_hours.isna().any():

            raise RuntimeError(
                "Silver valid-resolution flag "
                "contains null resolution_hours."
            )


        all_resolution_arrays.append(
            valid_hours.to_numpy(
                dtype="float64"
            )
        )


        temp_resolution = pd.DataFrame(
            {
                "agency":
                    agency
                    .loc[valid_resolution]
                    .values,

                "service_problem":
                    service
                    .loc[valid_resolution]
                    .values,

                "resolution_hours":
                    valid_hours.values,
            }
        )


        for (
            agency_name,
            service_name,
        ), group in temp_resolution.groupby(
            [
                "agency",
                "service_problem",
            ],
            sort=False,
        ):

            append_array(
                agency_service_resolution,
                (
                    agency_name,
                    service_name,
                ),
                group[
                    "resolution_hours"
                ].values,
            )


    # =========================================================================
    # DAILY AGGREGATIONS
    # =========================================================================

    if created.isna().any():

        raise RuntimeError(
            "Created timestamp contains null/invalid values."
        )


    created_date = (
        created
        .dt
        .normalize()
    )


    daily_temp = pd.DataFrame(
        {
            "created_date":
                created_date.values,

            "agency":
                agency.values,

            "service_problem":
                service.values,

            "is_backlog":
                is_backlog
                .astype("int8")
                .values,
        }
    )


    daily_part = (
        daily_temp
        .groupby(
            [
                "created_date",
                "agency",
                "service_problem",
            ],
            as_index=False,
        )
        .agg(
            request_count=(
                "is_backlog",
                "size",
            ),

            current_backlog_count=(
                "is_backlog",
                "sum",
            ),
        )
    )


    service_daily_parts.append(
        daily_part
    )


    # =========================================================================
    # DAILY AGENCY x SERVICE x ZIP FOR RECURRENCE
    # =========================================================================

    recurrence_temp = pd.DataFrame(
        {
            "created_date":
                created_date.values,

            "agency":
                agency.values,

            "service_problem":
                service.values,

            "incident_zip":
                incident_zip.values,

            "request_count":
                1,
        }
    )


    recurrence_part = (
        recurrence_temp
        .groupby(
            [
                "created_date",
                "agency",
                "service_problem",
                "incident_zip",
            ],
            as_index=False,
        )
        .agg(
            request_count=(
                "request_count",
                "sum",
            )
        )
    )


    service_zip_daily_parts.append(
        recurrence_part
    )


# =============================================================================
# BASE RECONCILIATION
# =============================================================================

section(
    "2 - BASE RECONCILIATION"
)


base_checks = {

    "Total Silver rows":
        total_rows
        == EXPECTED_TOTAL,

    "Closed rows":
        closed_rows
        == EXPECTED_CLOSED,

    "Backlog rows":
        backlog_rows
        == EXPECTED_BACKLOG,

    "Valid resolution rows":
        valid_resolution_rows
        == EXPECTED_VALID_RESOLUTION,

    "Invalid Created rows":
        invalid_created_rows
        == 0,

    "Agency x Service requests":
        sum(
            agency_service_requests.values()
        )
        == EXPECTED_TOTAL,

    "Agency x Service backlog":
        sum(
            agency_service_backlog.values()
        )
        == EXPECTED_BACKLOG,

    "ZIP requests":
        sum(
            zip_requests.values()
        )
        == EXPECTED_TOTAL,

    "ZIP backlog":
        sum(
            zip_backlog.values()
        )
        == EXPECTED_BACKLOG,

    "Agency x Service x ZIP requests":
        sum(
            agency_service_zip_requests.values()
        )
        == EXPECTED_TOTAL,

    "Agency x Service x ZIP backlog":
        sum(
            agency_service_zip_backlog.values()
        )
        == EXPECTED_BACKLOG,
}


for label, passed in base_checks.items():

    print(
        f"{label:<42} "
        f"{'PASS' if passed else 'FAIL'}"
    )


if not all(
    base_checks.values()
):

    raise RuntimeError(
        "Gold build stopped during "
        "base reconciliation."
    )


# =============================================================================
# GOLD CITY SNAPSHOT
# =============================================================================

section(
    "3 - BUILDING GOLD TABLES"
)


city_backlog_age = combine_arrays(
    all_backlog_age_arrays[
        "__city__"
    ]
)


city_resolution = combine_arrays(
    all_resolution_arrays
)


city_age_metrics = age_metrics(
    city_backlog_age
)


city_resolution_metrics = resolution_metrics(
    city_resolution
)


gold_city_snapshot = pd.DataFrame(
    [
        {
            "scope_id":
                "nyc_311_2026_ytd_through_2026_08_29",

            "scope_start_date":
                SCOPE_START_DATE,

            "scope_end_exclusive":
                SCOPE_END_EXCLUSIVE,

            "scope_last_included_date":
                SCOPE_LAST_INCLUDED_DATE,

            "observed_calendar_days":
                OBSERVED_DAYS,

            "total_requests":
                total_rows,

            "closed_requests":
                closed_rows,

            "current_backlog":
                backlog_rows,

            "backlog_rate_pct":
                backlog_rows
                / total_rows
                * 100,

            "requests_per_observed_day":
                total_rows
                / OBSERVED_DAYS,

            **city_age_metrics,

            **city_resolution_metrics,
        }
    ]
)


# =============================================================================
# GOLD SERVICE SNAPSHOT
# =============================================================================

service_rows = []


for (
    agency_name,
    service_name,
), request_count in agency_service_requests.items():

    key = (
        agency_name,
        service_name,
    )


    backlog_count = (
        agency_service_backlog
        .get(
            key,
            0,
        )
    )


    backlog_values = combine_arrays(
        agency_service_backlog_ages[
            key
        ]
    )


    resolution_values = combine_arrays(
        agency_service_resolution[
            key
        ]
    )


    row = {

        "agency":
            agency_name,

        "service_problem":
            service_name,

        "request_count":
            request_count,

        "backlog_count":
            backlog_count,

        "backlog_rate_pct":
            backlog_count
            / request_count
            * 100,

        "share_of_city_requests_pct":
            request_count
            / EXPECTED_TOTAL
            * 100,

        "share_of_city_backlog_pct":
            backlog_count
            / EXPECTED_BACKLOG
            * 100,

        **age_metrics(
            backlog_values
        ),

        **resolution_metrics(
            resolution_values
        ),
    }


    service_rows.append(
        row
    )


gold_service_snapshot = pd.DataFrame(
    service_rows
)


# =============================================================================
# GOLD LIFECYCLE FLAGS
# =============================================================================

gold_lifecycle_flags = (
    gold_service_snapshot[
        [
            "agency",
            "service_problem",
            "request_count",
            "backlog_count",
            "backlog_rate_pct",
            "valid_resolution_count",
            "resolution_59_5_60_5_share_pct",
        ]
    ]
    .copy()
)


gold_lifecycle_flags[
    "is_structural_lifecycle_exception"
] = (
    (
        gold_lifecycle_flags[
            "agency"
        ]
        == "EDC"
    )
    &
    (
        gold_lifecycle_flags[
            "service_problem"
        ]
        == "Noise - Helicopter"
    )
)


gold_lifecycle_flags[
    "has_systematic_60d_closure_pattern"
] = (
    (
        gold_lifecycle_flags[
            "valid_resolution_count"
        ]
        >= SYSTEMATIC_60D_MIN_VALID
    )
    &
    (
        gold_lifecycle_flags[
            "resolution_59_5_60_5_share_pct"
        ]
        >= SYSTEMATIC_60D_MIN_SHARE_PCT
    )
)


gold_lifecycle_flags[
    "lifecycle_interpretation"
] = np.select(

    [
        gold_lifecycle_flags[
            "is_structural_lifecycle_exception"
        ],

        gold_lifecycle_flags[
            "has_systematic_60d_closure_pattern"
        ],
    ],

    [
        (
            "Structural lifecycle exception: "
            "retain under Status-based backlog rule; "
            "do not compare naively with conventional "
            "closure workflows."
        ),

        (
            "Systematic ~60-day recorded closure "
            "pattern detected; resolution duration "
            "should not be interpreted automatically "
            "as field-service completion time."
        ),
    ],

    default=(
        "No special lifecycle flag established "
        "during Day 2."
    ),
)


gold_service_snapshot = (
    gold_service_snapshot
    .merge(
        gold_lifecycle_flags[
            [
                "agency",
                "service_problem",
                "is_structural_lifecycle_exception",
                "has_systematic_60d_closure_pattern",
            ]
        ],
        on=[
            "agency",
            "service_problem",
        ],
        how="left",
    )
)


gold_service_snapshot = (
    gold_service_snapshot
    .sort_values(
        [
            "backlog_count",
            "request_count",
        ],
        ascending=False,
    )
    .reset_index(
        drop=True
    )
)


# =============================================================================
# GOLD SERVICE DAILY
# =============================================================================

gold_service_daily = (
    pd.concat(
        service_daily_parts,
        ignore_index=True,
    )
    .groupby(
        [
            "created_date",
            "agency",
            "service_problem",
        ],
        as_index=False,
    )
    .agg(
        request_count=(
            "request_count",
            "sum",
        ),

        current_backlog_count=(
            "current_backlog_count",
            "sum",
        ),
    )
)


gold_service_daily[
    "current_open_share_pct"
] = (
    gold_service_daily[
        "current_backlog_count"
    ]
    / gold_service_daily[
        "request_count"
    ]
    * 100
)


gold_service_daily[
    "day_of_week"
] = (
    gold_service_daily[
        "created_date"
    ]
    .dt
    .day_name()
)


gold_service_daily[
    "month"
] = (
    gold_service_daily[
        "created_date"
    ]
    .dt
    .to_period("M")
    .astype(str)
)


gold_service_daily = (
    gold_service_daily
    .sort_values(
        [
            "created_date",
            "agency",
            "service_problem",
        ]
    )
    .reset_index(
        drop=True
    )
)


# =============================================================================
# GOLD ZIP SNAPSHOT
# =============================================================================

zip_rows = []


for zip_name, request_count in zip_requests.items():

    backlog_count = (
        zip_backlog
        .get(
            zip_name,
            0,
        )
    )


    backlog_values = combine_arrays(
        zip_backlog_ages[
            zip_name
        ]
    )


    zip_rows.append(
        {

            "incident_zip":
                zip_name,

            "zip_is_valid_5_digit":
                bool(
                    pd.Series(
                        [zip_name]
                    )
                    .astype("string")
                    .str
                    .fullmatch(
                        r"\d{5}",
                        na=False,
                    )
                    .iloc[0]
                ),

            "request_count":
                request_count,

            "backlog_count":
                backlog_count,

            "backlog_rate_pct":
                backlog_count
                / request_count
                * 100,

            "share_of_city_requests_pct":
                request_count
                / EXPECTED_TOTAL
                * 100,

            "share_of_city_backlog_pct":
                backlog_count
                / EXPECTED_BACKLOG
                * 100,

            **age_metrics(
                backlog_values
            ),
        }
    )


gold_zip_snapshot = (
    pd.DataFrame(
        zip_rows
    )
    .sort_values(
        [
            "backlog_count",
            "request_count",
        ],
        ascending=False,
    )
    .reset_index(
        drop=True
    )
)


# =============================================================================
# GOLD SERVICE x ZIP SNAPSHOT
# =============================================================================

service_zip_rows = []


for (
    agency_name,
    service_name,
    zip_name,
), request_count in agency_service_zip_requests.items():

    key = (
        agency_name,
        service_name,
        zip_name,
    )


    backlog_count = (
        agency_service_zip_backlog
        .get(
            key,
            0,
        )
    )


    backlog_values = combine_arrays(
        agency_service_zip_backlog_ages[
            key
        ]
    )


    service_zip_rows.append(
        {

            "agency":
                agency_name,

            "service_problem":
                service_name,

            "incident_zip":
                zip_name,

            "zip_is_valid_5_digit":
                bool(
                    pd.Series(
                        [zip_name]
                    )
                    .astype("string")
                    .str
                    .fullmatch(
                        r"\d{5}",
                        na=False,
                    )
                    .iloc[0]
                ),

            "request_count":
                request_count,

            "backlog_count":
                backlog_count,

            "backlog_rate_pct":
                backlog_count
                / request_count
                * 100,

            "share_of_city_requests_pct":
                request_count
                / EXPECTED_TOTAL
                * 100,

            "share_of_city_backlog_pct":
                backlog_count
                / EXPECTED_BACKLOG
                * 100,

            **age_metrics(
                backlog_values
            ),
        }
    )


gold_service_zip_snapshot = (
    pd.DataFrame(
        service_zip_rows
    )
    .sort_values(
        [
            "backlog_count",
            "request_count",
        ],
        ascending=False,
    )
    .reset_index(
        drop=True
    )
)


# =============================================================================
# GOLD SERVICE x ZIP RECURRENCE
# =============================================================================

service_zip_daily = (
    pd.concat(
        service_zip_daily_parts,
        ignore_index=True,
    )
    .groupby(
        [
            "created_date",
            "agency",
            "service_problem",
            "incident_zip",
        ],
        as_index=False,
    )
    .agg(
        request_count=(
            "request_count",
            "sum",
        )
    )
)


service_zip_daily[
    "week_start"
] = (
    service_zip_daily[
        "created_date"
    ]
    -
    pd.to_timedelta(
        service_zip_daily[
            "created_date"
        ]
        .dt
        .dayofweek,
        unit="D",
    )
)


service_zip_daily[
    "month"
] = (
    service_zip_daily[
        "created_date"
    ]
    .dt
    .to_period("M")
    .astype(str)
)


recurrence_rows = []


for (
    agency_name,
    service_name,
    zip_name,
), group in service_zip_daily.groupby(
    [
        "agency",
        "service_problem",
        "incident_zip",
    ],
    sort=False,
):

    counts = (
        group[
            "request_count"
        ]
        .to_numpy(
            dtype="float64"
        )
    )


    request_count = int(
        counts.sum()
    )


    active_days = len(
        counts
    )


    max_daily = int(
        counts.max()
    )


    top_5_days = int(
        np.sort(
            counts
        )[
            -min(
                5,
                len(counts),
            ):
        ]
        .sum()
    )


    key = (
        agency_name,
        service_name,
        zip_name,
    )


    backlog_count = (
        agency_service_zip_backlog
        .get(
            key,
            0,
        )
    )


    recurrence_rows.append(
        {

            "agency":
                agency_name,

            "service_problem":
                service_name,

            "incident_zip":
                zip_name,

            "zip_is_valid_5_digit":
                bool(
                    pd.Series(
                        [zip_name]
                    )
                    .astype("string")
                    .str
                    .fullmatch(
                        r"\d{5}",
                        na=False,
                    )
                    .iloc[0]
                ),

            "request_count":
                request_count,

            "active_days":
                active_days,

            "active_day_rate_pct":
                active_days
                / OBSERVED_DAYS
                * 100,

            "active_weeks":
                int(
                    group[
                        "week_start"
                    ]
                    .nunique()
                ),

            "active_months":
                int(
                    group[
                        "month"
                    ]
                    .nunique()
                ),

            "first_request_date":
                group[
                    "created_date"
                ]
                .min(),

            "last_request_date":
                group[
                    "created_date"
                ]
                .max(),

            "requests_per_active_day":
                request_count
                / active_days,

            "median_requests_per_active_day":
                float(
                    np.percentile(
                        counts,
                        50,
                    )
                ),

            "p90_requests_per_active_day":
                float(
                    np.percentile(
                        counts,
                        90,
                    )
                ),

            "max_daily_requests":
                max_daily,

            "top_day_share_pct":
                max_daily
                / request_count
                * 100,

            "top_5_days_share_pct":
                top_5_days
                / request_count
                * 100,

            "backlog_count":
                backlog_count,

            "backlog_rate_pct":
                backlog_count
                / request_count
                * 100,
        }
    )


gold_service_zip_recurrence = (
    pd.DataFrame(
        recurrence_rows
    )
)


recurrence_age_context = (
    gold_service_zip_snapshot[
        [
            "agency",
            "service_problem",
            "incident_zip",
            "median_backlog_age_days",
            "backlog_60d_plus",
            "old_backlog_share_60d_plus_pct",
        ]
    ]
)


gold_service_zip_recurrence = (
    gold_service_zip_recurrence
    .merge(
        recurrence_age_context,
        on=[
            "agency",
            "service_problem",
            "incident_zip",
        ],
        how="left",
    )
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
# GOLD RECONCILIATION
# =============================================================================

section(
    "4 - GOLD RECONCILIATION"
)


gold_checks = {

    "City total":
        int(
            gold_city_snapshot[
                "total_requests"
            ]
            .iloc[0]
        )
        == EXPECTED_TOTAL,

    "City backlog":
        int(
            gold_city_snapshot[
                "current_backlog"
            ]
            .iloc[0]
        )
        == EXPECTED_BACKLOG,

    "Service snapshot request sum":
        int(
            gold_service_snapshot[
                "request_count"
            ]
            .sum()
        )
        == EXPECTED_TOTAL,

    "Service snapshot backlog sum":
        int(
            gold_service_snapshot[
                "backlog_count"
            ]
            .sum()
        )
        == EXPECTED_BACKLOG,

    "Service daily request sum":
        int(
            gold_service_daily[
                "request_count"
            ]
            .sum()
        )
        == EXPECTED_TOTAL,

    "Service daily backlog sum":
        int(
            gold_service_daily[
                "current_backlog_count"
            ]
            .sum()
        )
        == EXPECTED_BACKLOG,

    "ZIP snapshot request sum":
        int(
            gold_zip_snapshot[
                "request_count"
            ]
            .sum()
        )
        == EXPECTED_TOTAL,

    "ZIP snapshot backlog sum":
        int(
            gold_zip_snapshot[
                "backlog_count"
            ]
            .sum()
        )
        == EXPECTED_BACKLOG,

    "Service ZIP request sum":
        int(
            gold_service_zip_snapshot[
                "request_count"
            ]
            .sum()
        )
        == EXPECTED_TOTAL,

    "Service ZIP backlog sum":
        int(
            gold_service_zip_snapshot[
                "backlog_count"
            ]
            .sum()
        )
        == EXPECTED_BACKLOG,

    "Recurrence request sum":
        int(
            gold_service_zip_recurrence[
                "request_count"
            ]
            .sum()
        )
        == EXPECTED_TOTAL,

    "Recurrence backlog sum":
        int(
            gold_service_zip_recurrence[
                "backlog_count"
            ]
            .sum()
        )
        == EXPECTED_BACKLOG,

    "Valid resolution sum":
        int(
            gold_service_snapshot[
                "valid_resolution_count"
            ]
            .sum()
        )
        == EXPECTED_VALID_RESOLUTION,

    "EDC structural exception":
        int(
            gold_lifecycle_flags[
                "is_structural_lifecycle_exception"
            ]
            .sum()
        )
        == 1,
}


for label, passed in gold_checks.items():

    print(
        f"{label:<42} "
        f"{'PASS' if passed else 'FAIL'}"
    )


if not all(
    gold_checks.values()
):

    raise RuntimeError(
        "\nGOLD BUILD FAILED RECONCILIATION."
    )


# =============================================================================
# DISPLAY LIFECYCLE FLAGS
# =============================================================================

section(
    "5 - LIFECYCLE FLAGS"
)


flagged = (
    gold_lifecycle_flags.loc[
        gold_lifecycle_flags[
            "is_structural_lifecycle_exception"
        ]
        |
        gold_lifecycle_flags[
            "has_systematic_60d_closure_pattern"
        ]
    ]
    .sort_values(
        [
            "is_structural_lifecycle_exception",
            "resolution_59_5_60_5_share_pct",
        ],
        ascending=False,
    )
)


print(
    flagged[
        [
            "agency",
            "service_problem",
            "request_count",
            "backlog_count",
            "valid_resolution_count",
            "resolution_59_5_60_5_share_pct",
            "is_structural_lifecycle_exception",
            "has_systematic_60d_closure_pattern",
        ]
    ]
    .to_string(
        index=False
    )
)


# =============================================================================
# WRITE GOLD TABLES
# =============================================================================

section(
    "6 - WRITING GOLD TABLES"
)


write_table(
    gold_city_snapshot,
    "gold_city_snapshot",
)


write_table(
    gold_service_snapshot,
    "gold_service_snapshot",
)


write_table(
    gold_service_daily,
    "gold_service_daily",
)


write_table(
    gold_zip_snapshot,
    "gold_zip_snapshot",
)


write_table(
    gold_service_zip_snapshot,
    "gold_service_zip_snapshot",
)


write_table(
    gold_service_zip_recurrence,
    "gold_service_zip_recurrence",
)


write_table(
    gold_lifecycle_flags,
    "gold_lifecycle_flags",
)


# =============================================================================
# MANIFEST
# =============================================================================

manifest = {

    "project":
        "Urban Service Reliability Analytics and BI",

    "implementation":
        "NYC 311 Service Operations Intelligence",

    "layer":
        "Gold",

    "scope":
        {

            "start_date_inclusive":
                SCOPE_START_DATE,

            "end_date_exclusive":
                SCOPE_END_EXCLUSIVE,

            "last_included_date":
                SCOPE_LAST_INCLUDED_DATE,

            "observed_calendar_days":
                OBSERVED_DAYS,
        },

    "locked_source_counts":
        {

            "total_requests":
                EXPECTED_TOTAL,

            "closed_requests":
                EXPECTED_CLOSED,

            "current_backlog":
                EXPECTED_BACKLOG,

            "valid_resolution_rows":
                EXPECTED_VALID_RESOLUTION,
        },

    "tables":
        {

            "gold_city_snapshot":
                len(
                    gold_city_snapshot
                ),

            "gold_service_snapshot":
                len(
                    gold_service_snapshot
                ),

            "gold_service_daily":
                len(
                    gold_service_daily
                ),

            "gold_zip_snapshot":
                len(
                    gold_zip_snapshot
                ),

            "gold_service_zip_snapshot":
                len(
                    gold_service_zip_snapshot
                ),

            "gold_service_zip_recurrence":
                len(
                    gold_service_zip_recurrence
                ),

            "gold_lifecycle_flags":
                len(
                    gold_lifecycle_flags
                ),
        },

    "business_rules":
        [

            (
                "Current request state is determined "
                "from Status."
            ),

            (
                "Backlog means Status is not Closed."
            ),

            (
                "Backlog age uses Silver "
                "request_age_days."
            ),

            (
                "Resolution duration uses Silver "
                "resolution_duration_valid and "
                "resolution_hours."
            ),

            (
                "Unknown geography is preserved."
            ),

            (
                "Raw ZIP counts are not "
                "population-adjusted burden."
            ),

            (
                "No universal SLA is assumed."
            ),
        ],
}


manifest_path = (
    GOLD_DIR
    / "gold_manifest.json"
)


manifest_path.write_text(
    json.dumps(
        manifest,
        indent=2,
    ),
    encoding="utf-8",
)


# =============================================================================
# README
# =============================================================================

readme = """# GOLD LAYER

Project: Urban Service Reliability Analytics and BI

Implementation: NYC 311 Service Operations Intelligence

## Scope

2026-01-01 inclusive through 2026-08-30 exclusive.

Last included request date: 2026-08-29.

## Tables

### gold_city_snapshot
One row containing the city-wide KPI snapshot.

### gold_service_snapshot
One row per Agency x Service workflow.

### gold_service_daily
One row per Created Date x Agency x Service.

`current_backlog_count` is the number of requests from that creation cohort
that remain non-Closed in the analytical dataset. It should not be read as a
same-day operational closure rate.

### gold_zip_snapshot
One row per Incident ZIP.

Raw ZIP counts are request concentration measures and are not
population-adjusted burden.

### gold_service_zip_snapshot
One row per Agency x Service x Incident ZIP.

### gold_service_zip_recurrence
One row per Agency x Service x Incident ZIP with recurrence and burst metrics.

### gold_lifecycle_flags
One row per Agency x Service with Day 2 lifecycle interpretation flags.

## Locked Rules

- Status determines current state.
- Backlog = Status is not Closed.
- Backlog age uses Silver request_age_days.
- Valid resolution duration uses Silver resolution_duration_valid.
- Resolution timing uses Silver resolution_hours.
- Unknown geography is preserved.
- No universal SLA is assumed.
- High backlog does not automatically imply poor agency performance.
- ~60-day closure clustering does not prove a 60-day SLA.
- EDC / Noise - Helicopter remains included but is flagged as a structural lifecycle exception.
"""


(
    GOLD_DIR
    / "README.md"
).write_text(
    readme,
    encoding="utf-8",
)


# =============================================================================
# COMPLETE
# =============================================================================

section(
    "GOLD LAYER BUILD COMPLETE"
)


print(
    f"Gold directory:\n"
    f"{GOLD_DIR}"
)

print()

print(
    f"Manifest:\n"
    f"{manifest_path}"
)

print()

print(
    "GOLD LAYER BUILD PASSED"
)