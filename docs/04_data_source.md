# Data Source

## Source

NYC Open Data

Dataset:
311 Service Requests from 2020 to Present

Dataset ID:
erm2-nwe9

Provider:
NYC 311

## API

https://data.cityofnewyork.us/resource/erm2-nwe9.json

## Accessibility Verification

The API and metadata endpoints were successfully queried during project
initialization.

Observed HTTP status:

200 OK

The live metadata exposed 48 published columns.

## Expected Grain

One source row represents one 311 Service Request.

The source documentation indicates that Unique Key identifies a service
request.

Unique-key uniqueness will be validated after Bronze acquisition.

## Analytical Scope

Geography:
NYC-wide

Created-date window:

2026-01-01 00:00:00 inclusive
through
2026-08-30 00:00:00 exclusive

Human-readable scope:

January 1, 2026 through August 29, 2026.

## Scope Rationale

Source profiling showed normal recent daily request volumes of approximately
9,000–12,000 requests.

August 30 contained only 1,121 requests, with the latest request timestamp
at 02:31:07.

August 30 was therefore classified as an incomplete publication day and
excluded from the analytical window.

## Important Source Observations

### Due Date

Due Date was populated for only approximately 0.37% of observed 2026 YTD
records.

All populated Due Date records belonged to DSNY.

Therefore Due Date will not be used as a city-wide SLA or target-date
compliance field.

### Lifecycle

The relationship between Status and Closed Date is not perfectly one-to-one.

Observed anomalies included:

- Closed requests without Closed Date
- Non-Closed requests with Closed Date

Detailed lifecycle business rules will therefore be established only after
record-level validation.

### Geography

Geographic coverage is strong:

- Borough: 100%
- ZIP: ~99%
- Latitude / Longitude: ~97.5%
- Community Board: 100%
- Council District: ~97%

This supports NYC-wide geographic analysis.