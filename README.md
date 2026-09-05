# Urban Service Reliability Analytics & BI

This repository contains the end-to-end workflow for urban service reliability analytics, from API ingestion and validation through transformation, analysis, and Power BI reporting.

## Project Structure

- `data/` stores raw, validated, and curated datasets
- `src/` contains Python pipeline components
- `sql/` contains database and transformation SQL scripts
- `docs/` contains project documentation
- `outputs/` stores profiling, validation, and analysis outputs
- `notebooks/` contains exploratory analysis notebooks
- `powerbi/` contains Power BI project notes and related assets
- `tests/` contains automated validation tests

## Getting Started

1. Create a virtual environment
2. Install dependencies from `requirements.txt`
3. Configure environment variables using `.env.example`
4. Review configuration in `config/config.yaml`
5. Run the ingestion and validation pipeline from the `src/` modules

## Notes

This project is intentionally scaffolded for a structured analytics workflow.
