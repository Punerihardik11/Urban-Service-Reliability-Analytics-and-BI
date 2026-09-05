-- Placeholder SQL for creating operational data tables.
-- Add schema definitions for bronze, silver, and gold tables as needed.

CREATE TABLE IF NOT EXISTS service_requests (
    id VARCHAR(255),
    created_date TIMESTAMP,
    status VARCHAR(255),
    service_name VARCHAR(255),
    priority VARCHAR(255)
);
