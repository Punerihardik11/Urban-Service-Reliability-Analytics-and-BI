# 05 Data Dictionary

This document defines key fields and their business meanings for project datasets.

# Data Dictionary

## Core Source Fields

| Field | Business Meaning | Type | Raw Null % | Example | Key? | Analytical Use | Caveat |
|---|---|---:|---:|---|---|---|---|
| unique_key | NYC 311 Service Request identifier | Integer | 0.00% | 70235850 | Primary | Request grain | Validated unique in snapshot |
| created_at | Request creation timestamp | Datetime | 0.00% | 2026-08-30 02:31:07 | No | Demand/time analysis | Local NYC operational time |
| closed_at | Source closure timestamp | Datetime | 6.28% | 2026-08-30 02:31:07 | No | Conditional duration calculation | Does not independently define current closure |
| agency | Responding agency code | String | 0.00% | DOT | No | Agency analysis | Cross-agency comparison requires service context |
| agency_name | Full responding agency name | String | 0.00% | Department of Transportation | No | Reporting | — |
| service_problem | Source Complaint Type / Problem | String | 0.00% | Street Condition | No | Primary service category | Taxonomy may be agency-specific |
| problem_detail | Source Descriptor / Problem Detail | String | ~0.00% | Pothole | No | Service drill-down | 31 missing rows |
| additional_detail | Additional service detail | String | 50.00% | — | No | Optional drill-down | Not uniformly available |
| status | Current observed request status | String | 0.00% | Closed | No | Backlog/current state | Primary field for current lifecycle classification |
| borough | Borough associated with request | String | 0.00% | QUEENS | No | Geographic analysis | Includes Unspecified |
| incident_zip | Raw source ZIP | String | 0.92% | 11415 | No | Geographic analysis | Two malformed values found |
| community_board | NYC Community Board | String | 0.00% | Varies | No | Neighborhood analysis | Administrative geography |
| council_district | Council district | String | 2.93% | Varies | No | Geographic analysis | Missing for some requests |
| latitude | Incident latitude | Numeric | 2.49% | 40.x | No | Mapping/hotspots | Coordinate analysis requires longitude |
| longitude | Incident longitude | Numeric | 2.49% | -73.x | No | Mapping/hotspots | Coordinate analysis requires latitude |
| due_date | Agency target/update date | Datetime | 99.63% | — | No | DSNY-specific investigation only | Unsuitable for city-wide SLA |
| resolution_description | Latest agency action/free-text explanation | String | 2.30% | Agency response text | No | Qualitative investigation | Contains encoding artifacts |
| resolution_action_updated_date | Latest resolution-action update timestamp | Datetime | 2.01% | Varies | No | Lifecycle context | Not equivalent to closure |
| open_data_channel_type | Request submission channel | String | 0.00% | ONLINE | No | Channel analysis | UNKNOWN is a real source category |

## Derived Analytical Fields

| Field | Meaning |
|---|---|
| is_closed | Current Status equals Closed |
| is_backlog | Current Status represents an unresolved request |
| resolution_duration_valid | Request satisfies lifecycle and timestamp requirements for duration analysis |
| resolution_hours | Valid elapsed hours between creation and closure |
| resolution_days | Valid elapsed days between creation and closure |
| request_age_days | Age of currently unresolved request at analytical snapshot |
| incident_zip_clean | Validated five-digit ZIP derivative |
| has_valid_coordinates | Complete usable latitude/longitude pair |
| lifecycle_mismatch_flag | Status and Closed Date combination requires caution |
| negative_duration_flag | Closed Date precedes Created Date |
| future_closed_date_flag | Closed Date occurs after extraction snapshot |
| zero_duration_flag | Valid resolution duration equals zero |
| extreme_duration_flag | Valid resolution duration exceeds 180 days |
| resolution_duration_band | Operational duration grouping |
| backlog_age_band | Age grouping for unresolved requests |