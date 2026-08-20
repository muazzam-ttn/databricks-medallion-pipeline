-- Checkpoint 3: minimal Unity Catalog setup for Bronze ingestion.
-- The ecommerce_sales catalog and raw.source_files Volume already exist.

CREATE SCHEMA IF NOT EXISTS ecommerce_sales.bronze
COMMENT 'Source-preserving Bronze Delta tables for e-commerce CSV ingestion';
