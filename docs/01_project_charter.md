# Project Charter

## Project

Urban Service Reliability Analytics and BI

## Analytical Implementation

NYC 311 Service Operations Intelligence

## Domain

Government / Public Sector / Service Operations

## Primary Stakeholder

City Operations / Service Delivery Manager

## Business Objective

Build an operational analytics system that identifies where city-service
demand is accumulating, where unresolved requests persist, which service
categories experience unusual resolution delays, and where operational
attention may be required.

The project is not intended to answer only:

"How many 311 requests were submitted?"

Instead, it should help answer:

"Where is service demand accumulating, which services and locations experience
persistent resolution problems, why are requests taking longer to resolve,
and where should city operations investigate first?"

## Primary Data Source

NYC Open Data

Dataset:
311 Service Requests from 2020 to Present

Dataset ID:
erm2-nwe9

## Expected Grain

One row represents one 311 Service Request.

This must still be validated empirically using Unique Key.

## Geographic Scope

NYC-wide.

## Time Scope

Not yet locked.

Candidate periods will be evaluated using API row counts before acquisition.

## Project Duration

3–4 days.

## Architectural Direction

NYC Open Data API
→ Bronze
→ Python validation/transformation
→ Silver
→ MySQL
→ SQL Gold/business layer
→ Power BI

## Analytical Principles

- Business-first analysis
- Validation before visualization
- Preserve unknown/null values unless semantics justify transformation
- Do not manufacture SLAs
- Prefer median and percentiles for skewed duration distributions
- Keep invalid records visible in audit outputs
- Separate observed facts, derived metrics, estimates and assumptions