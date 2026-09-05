from __future__ import annotations

from pathlib import Path

import pandas as pd


# =============================================================================
# CONFIG
# =============================================================================

ROOT = Path(__file__).resolve().parents[2]

DAY2_DIR = ROOT / "outputs" / "analysis" / "day2"

EXPECTED_TOTAL = 2_644_153
EXPECTED_BACKLOG = 186_436
EXPECTED_VALID_RESOLUTION = 2_457_340
EXPECTED_EDC_HELICOPTER = 6_974


# =============================================================================
# HELPERS
# =============================================================================

def section(title: str) -> None:
    print()
    print("=" * 112)
    print(title)
    print("=" * 112)


def require_file(filename: str) -> Path:
    path = DAY2_DIR / filename

    if not path.exists():
        raise FileNotFoundError(
            f"Required Day 2 output missing:\n{path}"
        )

    return path


def get_row(
    df: pd.DataFrame,
    column: str,
    value: str,
) -> pd.Series:

    rows = df.loc[
        df[column]
        .astype("string")
        .eq(value)
    ]

    if len(rows) != 1:
        raise RuntimeError(
            f"Expected exactly one row where "
            f"{column} = {value!r}; found {len(rows)}."
        )

    return rows.iloc[0]


# =============================================================================
# LOAD VALIDATED DAY 2 OUTPUTS
# =============================================================================

section(
    "URBAN SERVICE RELIABILITY - DAY 2 SYNTHESIS"
)


required_files = [

    "backlog_by_service.csv",

    "agency_service_profile.csv",

    "geography_borough_profile.csv",

    "geography_zip_profile.csv",

    "geography_service_zip_profile.csv",

    "geography_zip_quality_summary.csv",

    "temporal_monthly_profile.csv",

    "temporal_daily_profile.csv",

    "temporal_top_day_service_contributors.csv",

    "recurring_service_zip_profile.csv",

    "edc_noise_helicopter_status_profile.csv",

    "edc_noise_helicopter_closure_evidence.csv",

    "closure_pattern_service_profile.csv",

    "closure_pattern_target_services.csv",
]


paths = {
    filename:
        require_file(filename)

    for filename
    in required_files
}


print("Required Day 2 outputs:  PASS")


backlog_service = pd.read_csv(
    paths["backlog_by_service.csv"]
)

agency_service = pd.read_csv(
    paths["agency_service_profile.csv"]
)

borough = pd.read_csv(
    paths["geography_borough_profile.csv"]
)

zip_profile = pd.read_csv(
    paths["geography_zip_profile.csv"],
    dtype={
        "incident_zip": "string",
    },
)

service_zip = pd.read_csv(
    paths["geography_service_zip_profile.csv"],
    dtype={
        "incident_zip": "string",
    },
)

zip_quality = pd.read_csv(
    paths["geography_zip_quality_summary.csv"]
)

monthly = pd.read_csv(
    paths["temporal_monthly_profile.csv"]
)

daily = pd.read_csv(
    paths["temporal_daily_profile.csv"]
)

top_day_services = pd.read_csv(
    paths["temporal_top_day_service_contributors.csv"]
)

recurring = pd.read_csv(
    paths["recurring_service_zip_profile.csv"],
    dtype={
        "incident_zip": "string",
    },
)

edc_status = pd.read_csv(
    paths["edc_noise_helicopter_status_profile.csv"]
)

edc_closure = pd.read_csv(
    paths["edc_noise_helicopter_closure_evidence.csv"]
)

closure_profile = pd.read_csv(
    paths["closure_pattern_service_profile.csv"]
)

closure_targets = pd.read_csv(
    paths["closure_pattern_target_services.csv"]
)


# =============================================================================
# CROSS-OUTPUT RECONCILIATION
# =============================================================================

section(
    "1 - CROSS-OUTPUT RECONCILIATION"
)


checks = {

    "Agency x Service request total":
        int(
            agency_service[
                "request_count"
            ].sum()
        )
        == EXPECTED_TOTAL,

    "Agency x Service backlog total":
        int(
            agency_service[
                "backlog_count"
            ].sum()
        )
        == EXPECTED_BACKLOG,

    "ZIP request total":
        int(
            zip_profile[
                "request_count"
            ].sum()
        )
        == EXPECTED_TOTAL,

    "ZIP backlog total":
        int(
            zip_profile[
                "backlog_count"
            ].sum()
        )
        == EXPECTED_BACKLOG,

    "Service x ZIP request total":
        int(
            service_zip[
                "request_count"
            ].sum()
        )
        == EXPECTED_TOTAL,

    "Service x ZIP backlog total":
        int(
            service_zip[
                "backlog_count"
            ].sum()
        )
        == EXPECTED_BACKLOG,

    "Monthly request total":
        int(
            monthly[
                "request_count"
            ].sum()
        )
        == EXPECTED_TOTAL,

    "Monthly backlog total":
        int(
            monthly[
                "backlog_count"
            ].sum()
        )
        == EXPECTED_BACKLOG,

    "Daily request total":
        int(
            daily[
                "request_count"
            ].sum()
        )
        == EXPECTED_TOTAL,

    "Recurring Service x ZIP request total":
        int(
            recurring[
                "request_count"
            ].sum()
        )
        == EXPECTED_TOTAL,

    "Recurring Service x ZIP backlog total":
        int(
            recurring[
                "backlog_count"
            ].sum()
        )
        == EXPECTED_BACKLOG,

    "Valid resolution total":
        int(
            closure_profile[
                "valid_resolution_count"
            ].sum()
        )
        == EXPECTED_VALID_RESOLUTION,

    "EDC Helicopter status total":
        int(
            edc_status[
                "row_count"
            ].sum()
        )
        == EXPECTED_EDC_HELICOPTER,
}


for label, passed in checks.items():

    print(
        f"{label:<44} "
        f"{'PASS' if passed else 'FAIL'}"
    )


if not all(
    checks.values()
):

    raise RuntimeError(
        "\nDAY 2 SYNTHESIS STOPPED.\n"
        "One or more validated analysis outputs "
        "do not reconcile."
    )


# =============================================================================
# DERIVE LOCKED FINDINGS
# =============================================================================

section(
    "2 - DERIVING LOCKED DAY 2 FINDINGS"
)


# -------------------------------------------------------------------------
# CITY-WIDE PERSISTENT BACKLOG
# -------------------------------------------------------------------------

city_backlog = int(
    backlog_service[
        "backlog_count"
    ].sum()
)


city_30d = int(
    backlog_service[
        "backlog_30d_plus"
    ].sum()
)


city_60d = int(
    backlog_service[
        "backlog_60d_plus"
    ].sum()
)


city_90d = int(
    backlog_service[
        "backlog_90d_plus"
    ].sum()
)


city_180d = int(
    backlog_service[
        "backlog_180d_plus"
    ].sum()
)


share_30d = (
    city_30d
    / city_backlog
    * 100
)


share_60d = (
    city_60d
    / city_backlog
    * 100
)


share_90d = (
    city_90d
    / city_backlog
    * 100
)


share_180d = (
    city_180d
    / city_backlog
    * 100
)


# -------------------------------------------------------------------------
# HPD CONTRAST
# -------------------------------------------------------------------------

hpd_unsanitary = agency_service.loc[
    (
        agency_service["agency"]
        == "HPD"
    )
    &
    (
        agency_service[
            "service_problem"
        ]
        == "UNSANITARY CONDITION"
    )
].iloc[0]


hpd_heat = agency_service.loc[
    (
        agency_service["agency"]
        == "HPD"
    )
    &
    (
        agency_service[
            "service_problem"
        ]
        == "HEAT/HOT WATER"
    )
].iloc[0]


# -------------------------------------------------------------------------
# TLC CONCENTRATION
# -------------------------------------------------------------------------

tlc = agency_service.loc[
    agency_service[
        "agency"
    ]
    == "TLC"
]


tlc_backlog = int(
    tlc[
        "backlog_count"
    ].sum()
)


tlc_fhv = tlc.loc[
    tlc[
        "service_problem"
    ]
    == "For Hire Vehicle Complaint"
].iloc[0]


tlc_taxi = tlc.loc[
    tlc[
        "service_problem"
    ]
    == "Taxi Complaint"
].iloc[0]


tlc_two_workflow_share = (
    (
        tlc_fhv[
            "backlog_count"
        ]
        +
        tlc_taxi[
            "backlog_count"
        ]
    )
    / tlc_backlog
    * 100
)


# -------------------------------------------------------------------------
# GEOGRAPHIC CONTRAST
# -------------------------------------------------------------------------

zip_10023 = get_row(
    zip_profile,
    "incident_zip",
    "10023",
)


zip_11226 = get_row(
    zip_profile,
    "incident_zip",
    "11226",
)


# -------------------------------------------------------------------------
# TEMPORAL
# -------------------------------------------------------------------------

feb = get_row(
    monthly,
    "month",
    "2026-02",
)


feb24 = top_day_services.loc[
    top_day_services[
        "date"
    ]
    == "2026-02-24"
]


feb24_snow = feb24.loc[
    feb24[
        "service_problem"
    ]
    == "Snow or Ice"
].iloc[0]


# -------------------------------------------------------------------------
# RECURRING LOCAL DEMAND
# -------------------------------------------------------------------------

illegal_parking_11101 = recurring.loc[
    (
        recurring[
            "service_problem"
        ]
        == "Illegal Parking"
    )
    &
    (
        recurring[
            "incident_zip"
        ]
        == "11101"
    )
].iloc[0]


# -------------------------------------------------------------------------
# EDC
# -------------------------------------------------------------------------

edc_in_progress = get_row(
    edc_status,
    "status",
    "In Progress",
)


closed_evidence = get_row(
    edc_closure,
    "metric",
    "Status = Closed",
)


# -------------------------------------------------------------------------
# 60-DAY PATTERN
# -------------------------------------------------------------------------

food = closure_targets.loc[
    closure_targets[
        "service_problem"
    ]
    == "Food Establishment"
].iloc[0]


smoking = closure_targets.loc[
    closure_targets[
        "service_problem"
    ]
    == "Smoking or Vaping"
].iloc[0]


mobile_food = closure_profile.loc[
    closure_profile[
        "service_problem"
    ]
    == "Mobile Food Vendor"
].iloc[0]


# =============================================================================
# FINDINGS TABLE
# =============================================================================

findings = [

    {
        "finding_id":
            "D2-F01",

        "theme":
            "Persistent backlog",

        "finding":
            (
                f"Current backlog contains substantial aged inventory: "
                f"{share_30d:.2f}% is 30+ days old, "
                f"{share_60d:.2f}% is 60+ days old, "
                f"{share_90d:.2f}% is 90+ days old, and "
                f"{share_180d:.2f}% is 180+ days old."
            ),

        "business_implication":
            (
                "Backlog prioritization must distinguish recent "
                "unresolved work from persistent aged inventory."
            ),
    },

    {
        "finding_id":
            "D2-F02",

        "theme":
            "Workflow heterogeneity",

        "finding":
            (
                f"Inside HPD, UNSANITARY CONDITION has "
                f"{int(hpd_unsanitary['backlog_count']):,} backlog rows "
                f"with median age "
                f"{hpd_unsanitary['median_backlog_age_days']:.2f} days, "
                f"while HEAT/HOT WATER has "
                f"{int(hpd_heat['backlog_count']):,} backlog rows "
                f"with median age "
                f"{hpd_heat['median_backlog_age_days']:.2f} days."
            ),

        "business_implication":
            (
                "Agency-level averages conceal materially different "
                "service workflows; Agency x Service is the primary "
                "operational comparison grain."
            ),
    },

    {
        "finding_id":
            "D2-F03",

        "theme":
            "Agency backlog concentration",

        "finding":
            (
                f"For Hire Vehicle Complaint and Taxi Complaint "
                f"together account for "
                f"{tlc_two_workflow_share:.2f}% of TLC backlog."
            ),

        "business_implication":
            (
                "High agency backlog may be driven by a small number "
                "of workflows rather than an agency-wide condition."
            ),
    },

    {
        "finding_id":
            "D2-F04",

        "theme":
            "Geographic concentration",

        "finding":
            (
                f"ZIP 10023 has backlog rate "
                f"{zip_10023['backlog_rate_pct']:.2f}% and median "
                f"backlog age {zip_10023['median_backlog_age_days']:.2f} "
                f"days, while high-volume ZIP 11226 has backlog rate "
                f"{zip_11226['backlog_rate_pct']:.2f}% and median age "
                f"{zip_11226['median_backlog_age_days']:.2f} days."
            ),

        "business_implication":
            (
                "High request volume and persistent backlog are "
                "different geographic phenomena. Service x Geography "
                "must be inspected before interpreting hotspots."
            ),
    },

    {
        "finding_id":
            "D2-F05",

        "theme":
            "Temporal decomposition",

        "finding":
            (
                f"February averaged "
                f"{feb['requests_per_observed_day']:.1f} requests per "
                f"observed day. On 2026-02-24, Snow or Ice generated "
                f"{int(feb24_snow['request_count']):,} requests, "
                f"{feb24_snow['share_of_day_demand_pct']:.2f}% "
                f"of all requests that day."
            ),

        "business_implication":
            (
                "Demand spikes should be explained through service "
                "composition rather than treated as uniform changes "
                "in city-wide demand."
            ),
    },

    {
        "finding_id":
            "D2-F06",

        "theme":
            "Recurring local demand",

        "finding":
            (
                f"Illegal Parking in ZIP 11101 was active on "
                f"{int(illegal_parking_11101['active_days'])} of "
                f"241 observed days, averaging "
                f"{illegal_parking_11101['requests_per_active_day']:.2f} "
                f"requests per active day."
            ),

        "business_implication":
            (
                "Local service demand must distinguish sustained "
                "recurrence from event-driven bursts."
            ),
    },

    {
        "finding_id":
            "D2-F07",

        "theme":
            "Lifecycle exception",

        "finding":
            (
                f"All {int(edc_in_progress['row_count']):,} "
                f"EDC / Noise - Helicopter rows are In Progress, "
                f"with {int(closed_evidence['row_count']):,} "
                f"rows marked Closed."
            ),

        "business_implication":
            (
                "EDC / Noise - Helicopter must remain in the data "
                "under the Status-based backlog rule but should be "
                "flagged as a structural lifecycle exception."
            ),
    },

    {
        "finding_id":
            "D2-F08",

        "theme":
            "Systematic closure timing",

        "finding":
            (
                f"Food Establishment has "
                f"{food['resolution_59_9_60_1d_share_pct']:.2f}% "
                f"of valid resolutions within 59.9-60.1 days. "
                f"Smoking or Vaping has "
                f"{smoking['resolution_59_9_60_1d_share_pct']:.2f}% "
                f"in the same narrow window."
            ),

        "business_implication":
            (
                "Recorded closure duration for selected workflows "
                "contains strong lifecycle/process effects and must "
                "not automatically be interpreted as field-service "
                "completion time."
            ),
    },

    {
        "finding_id":
            "D2-F09",

        "theme":
            "Extreme closure clustering",

        "finding":
            (
                f"Mobile Food Vendor has "
                f"{mobile_food['resolution_59_5_60_5d_share_pct']:.2f}% "
                f"of valid resolutions inside the 59.5-60.5 day window."
            ),

        "business_implication":
            (
                "The ~60-day concentration is workflow-specific, "
                "not a generic property of NYC 311 resolution times."
            ),
    },

    {
        "finding_id":
            "D2-F10",

        "theme":
            "Interpretation guardrails",

        "finding":
            (
                "No universal SLA was established; high backlog does "
                "not automatically mean poor agency performance; "
                "raw ZIP counts are not population-adjusted burden; "
                "and partial-year data cannot establish full annual "
                "seasonality."
            ),

        "business_implication":
            (
                "These limitations must remain visible in the Gold "
                "layer documentation and BI interpretation."
            ),
    },
]


findings_df = pd.DataFrame(
    findings
)


findings_path = (
    DAY2_DIR
    / "day2_locked_findings.csv"
)


findings_df.to_csv(
    findings_path,
    index=False,
)


# =============================================================================
# GOLD BUSINESS MODEL BLUEPRINT
# =============================================================================

gold_blueprint = [

    {
        "table_name":
            "gold_city_snapshot",

        "grain":
            "One row for the analytical snapshot",

        "primary_keys":
            "snapshot_date",

        "purpose":
            (
                "City-wide KPI snapshot: total requests, closed, "
                "backlog, backlog rate, age cohorts and "
                "resolution distribution."
            ),
    },

    {
        "table_name":
            "gold_service_snapshot",

        "grain":
            "One row per Agency x Service",

        "primary_keys":
            "agency, service_problem",

        "purpose":
            (
                "Operational workflow profile including demand, "
                "backlog volume, backlog rate, backlog age and "
                "lifecycle flags."
            ),
    },

    {
        "table_name":
            "gold_service_daily",

        "grain":
            "One row per Date x Agency x Service",

        "primary_keys":
            "created_date, agency, service_problem",

        "purpose":
            (
                "Temporal demand decomposition and service trend "
                "analysis."
            ),
    },

    {
        "table_name":
            "gold_zip_snapshot",

        "grain":
            "One row per Incident ZIP",

        "primary_keys":
            "incident_zip",

        "purpose":
            (
                "Geographic request and backlog concentration. "
                "Raw counts only; not population adjusted."
            ),
    },

    {
        "table_name":
            "gold_service_zip_snapshot",

        "grain":
            "One row per Agency x Service x Incident ZIP",

        "primary_keys":
            "agency, service_problem, incident_zip",

        "purpose":
            (
                "Workflow-level geographic hotspots, backlog "
                "concentration and local operational context."
            ),
    },

    {
        "table_name":
            "gold_service_zip_recurrence",

        "grain":
            "One row per Agency x Service x Incident ZIP",

        "primary_keys":
            "agency, service_problem, incident_zip",

        "purpose":
            (
                "Persistent versus burst-driven local demand using "
                "active days, active weeks, intensity and "
                "top-day concentration."
            ),
    },

    {
        "table_name":
            "gold_lifecycle_flags",

        "grain":
            "One row per Agency x Service",

        "primary_keys":
            "agency, service_problem",

        "purpose":
            (
                "Flags structural lifecycle exceptions and workflows "
                "with systematic closure-timing behavior."
            ),
    },
]


gold_df = pd.DataFrame(
    gold_blueprint
)


gold_path = (
    DAY2_DIR
    / "gold_model_blueprint.csv"
)


gold_df.to_csv(
    gold_path,
    index=False,
)


# =============================================================================
# HUMAN-READABLE DAY 2 HANDOVER
# =============================================================================

markdown_lines = [

    "# DAY 2 ANALYTICAL FINDINGS",

    "",

    "## Project",

    "Urban Service Reliability Analytics and BI",

    "",

    "Implementation: NYC 311 Service Operations Intelligence",

    "",

    "## Analytical Scope",

    "2026-01-01 inclusive through 2026-08-30 exclusive.",

    "",

    "August 30 remains excluded because it was identified as an "
    "incomplete publication day.",

    "",

    "## Locked Day 2 Findings",

]


for row in findings:

    markdown_lines.extend(
        [
            "",
            f"### {row['finding_id']} - {row['theme']}",
            "",
            row["finding"],
            "",
            f"Business implication: {row['business_implication']}",
        ]
    )


markdown_lines.extend(
    [
        "",
        "## Gold Layer Direction",
        "",
    ]
)


for table in gold_blueprint:

    markdown_lines.extend(
        [
            f"### {table['table_name']}",
            "",
            f"Grain: {table['grain']}",
            "",
            f"Primary key: {table['primary_keys']}",
            "",
            table["purpose"],
            "",
        ]
    )


markdown_lines.extend(
    [
        "## Locked Non-Claims",
        "",
        "- No universal SLA established.",
        "- High backlog does not automatically mean poor agency performance.",
        "- High resolution duration does not automatically mean service failure.",
        "- Raw ZIP request counts are not population-adjusted burden.",
        "- Partial-year data cannot establish full annual seasonality.",
        "- ~60-day closure clustering does not prove a 60-day SLA.",
        "- EDC / Noise - Helicopter is retained under the Status-based backlog rule.",
        "",
        "## Status",
        "",
        "DAY 2 ANALYTICAL INVESTIGATION COMPLETE.",
        "",
        "NEXT: BUILD GOLD BUSINESS TABLES AND LOAD THEM INTO MYSQL.",
    ]
)


handover_path = (
    DAY2_DIR
    / "DAY2_ANALYTICAL_FINDINGS.md"
)


handover_path.write_text(
    "\n".join(
        markdown_lines
    ),
    encoding="utf-8",
)


# =============================================================================
# PRINT
# =============================================================================

section(
    "3 - LOCKED FINDINGS"
)


print(
    findings_df[
        [
            "finding_id",
            "theme",
            "finding",
        ]
    ]
    .to_string(
        index=False
    )
)


section(
    "4 - GOLD MODEL BLUEPRINT"
)


print(
    gold_df
    .to_string(
        index=False
    )
)


section(
    "DAY 2 STEP 8 COMPLETE"
)


print("Outputs written:")

print(
    findings_path
)

print(
    gold_path
)

print(
    handover_path
)

print()

print(
    "DAY 2 SYNTHESIS PASSED"
)