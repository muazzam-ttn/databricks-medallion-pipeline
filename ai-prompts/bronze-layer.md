# AI Prompts — Bronze Layer

## Context

This file documents the AI-assisted work completed during:

```text
Checkpoint 3 — Bronze Layer
```

Primary AI tool:

```text
Cursor
```

The objective of this checkpoint was to ingest the generated CSV source files from a Databricks Unity Catalog Volume into Bronze Delta tables while preserving the source data as-is.

No Silver data-quality transformations, Gold aggregations, or dashboard logic were included in this checkpoint.

---

# Databricks Environment

The project is running on Databricks Free Edition with Unity Catalog.

The source files were manually uploaded to a Databricks Volume because the project is not using DBFS.

Existing objects:

```text
Catalog:
ecommerce_sales

Source schema:
ecommerce_sales.raw

Volume:
ecommerce_sales.raw.source_files
```

Source files:

```text
/Volumes/ecommerce_sales/raw/source_files/customers.csv

/Volumes/ecommerce_sales/raw/source_files/orders.csv

/Volumes/ecommerce_sales/raw/source_files/products.csv
```

Bronze target schema:

```text
ecommerce_sales.bronze
```

Target tables:

```text
ecommerce_sales.bronze.customers

ecommerce_sales.bronze.orders

ecommerce_sales.bronze.products
```

---

# Prompt — Bronze Layer Ingestion

## Prompt Sent

```text
Act as a senior Databricks data engineer implementing the Bronze layer for this project. Prioritize source preservation, traceability, and simple maintainable PySpark.

Before making changes, read the relevant project context:


data-model.md
design-notes.md
tool-specific/cursor-workflow/project-context.md
tool-specific/cursor-workflow/spec.md
tool-specific/cursor-workflow/cursor-rules-or-instructions.md
tool-specific/cursor-workflow/task-breakdown.md


Active checkpoint
Checkpoint 3 — Bronze Layer
Implement only Bronze ingestion.
Do not implement Silver, Gold, or dashboard logic.

Databricks Environment
The project is running on Databricks Free Edition.
The CSV files have already been uploaded to a Unity Catalog Volume.

Source locations:

/Volumes/ecommerce_sales/raw/source_files/customers.csv
/Volumes/ecommerce_sales/raw/source_files/orders.csv
/Volumes/ecommerce_sales/raw/source_files/products.csv

Existing objects:

Catalog: ecommerce_sales
Schema: raw
Volume: source_files

Use the following target schema for the Bronze layer:
ecommerce_sales.bronze

If the schema does not exist, include the minimal setup required to create it.
Files to create/update

src/bronze/01_ingest_customers.py
src/bronze/02_ingest_orders.py
src/bronze/03_ingest_products.py

database/schema.sql
database/setup-notes.md


Do not modify the generated source CSVs.

Bronze requirements

For each source:

1. Read the CSV from the Volume path using PySpark.
2. Use the source header.
3. Infer the CSV schema as required by the project.
4. Do not clean, deduplicate, filter, fill NULLs, or correct any source values.
5. Add only operational ingestion metadata:
_ingested_at

Optionally add _source_file only if it remains simple and useful.

6. Write the result as a Delta table:
- ecommerce_sales.bronze.customers
- ecommerce_sales.bronze.orders
- ecommerce_sales.bronze.products

7. Use rerun-safe behavior suitable for this exercise so repeated development runs do not duplicate source records.
8. Log/display source and Bronze row counts.

Important preservation requirement

Bronze must preserve the intentionally bad records.

Do not remove:
- NULL customer emails
- NULL order customer_id values
- NULL order product_id values
- invalid foreign keys
- duplicate customer IDs
- duplicate order IDs

The source-to-Bronze physical row counts must remain:

customers = 10,000
orders    = 100,000
products  = 500

Adding _ingested_at does not count as modifying the source business data.

- Do not perform Silver-quality evaluation yet; these checks are only to prove Bronze preservation.
- Keep the code straightforward and readable.
- Use small reusable helpers only where they reduce obvious duplication.

Do not introduce:

- Auto Loader
- streaming
- DLT / Lakeflow Declarative Pipelines
- Workflows
- complex configuration frameworks for this checkpoint.

After implementation

Summarize:

1. files changed,
2. table names created,
3. schema inferred for each dataset,
4. source vs Bronze row counts,
5. any assumptions or Databricks Free Edition limitations discovered.

Then STOP.

Do not proceed to Silver.
```


Cursor was asked to act as a senior Databricks data engineer and implement only the Bronze layer.

Before implementation, Cursor was instructed to read the existing project context:

```text
data-model.md
design-notes.md

tool-specific/cursor-workflow/project-context.md
tool-specific/cursor-workflow/spec.md
tool-specific/cursor-workflow/cursor-rules-or-instructions.md
tool-specific/cursor-workflow/task-breakdown.md
```

The task was scoped to:

```text
src/bronze/01_ingest_customers.py
src/bronze/02_ingest_orders.py
src/bronze/03_ingest_products.py

database/schema.sql
database/setup-notes.md
```

The main implementation requirements were:

* Read CSV files directly from the Databricks Volume using PySpark.
* Use CSV headers.
* Use Spark schema inference.
* Preserve the input data without cleaning.
* Add only operational ingestion metadata using `_ingested_at`.
* Persist each dataset as a Delta table.
* Use overwrite behavior so development reruns do not duplicate data.
* Display/log source and Bronze row counts.
* Keep the code straightforward and Databricks-focused.

Cursor was explicitly instructed not to:

```text
clean data
deduplicate records
fill NULL values
correct invalid foreign keys
perform Silver validation
build Gold logic
build dashboard logic
use Auto Loader
use streaming
use DLT / Lakeflow Declarative Pipelines
use Databricks Workflows
introduce a complex configuration framework
```

---

# AI Response Summary

Cursor generated separate ingestion scripts for:

```text
customers
orders
products
```

and created supporting database/setup documentation.

The implementation pattern used for each Bronze source was:

```text
Read CSV from Volume
        ↓
Validate source structure
        ↓
Print inferred schema
        ↓
Add _ingested_at
        ↓
Write Delta table using overwrite
        ↓
Read persisted table
        ↓
Compare source and Bronze row counts
```

The Bronze tables were designed as:

```text
ecommerce_sales.bronze.customers
ecommerce_sales.bronze.orders
ecommerce_sales.bronze.products
```

The setup documentation also included:

```sql
CREATE SCHEMA IF NOT EXISTS ecommerce_sales.bronze;
```

so the target Bronze schema can be created idempotently.

---

# What I Accepted

## 1. Unity Catalog Volume as the Bronze Source

The ingestion scripts read directly from:

```text
/Volumes/ecommerce_sales/raw/source_files/
```

### Why accepted

The generated CSV files had already been uploaded to a Unity Catalog Volume in Databricks Free Edition.

Using the Volume path keeps the source location explicit and aligns the pipeline with the actual Databricks environment.

---

## 2. Dedicated Bronze Schema

The Bronze tables are stored under:

```text
ecommerce_sales.bronze
```

while:

```text
ecommerce_sales.raw
```

remains the landing area containing the source Volume.

### Why accepted

This creates a clean separation between:

```text
raw source files
```

and:

```text
Bronze managed Delta tables
```

without adding unnecessary architecture.

---

## 3. Spark CSV Schema Inference

The scripts use:

```python
.option("header", True)
.option("inferSchema", True)
```

when loading CSV data.

### Why accepted

Schema inference is explicitly part of the Bronze requirement for this exercise.

The inferred schema is also printed so the actual Databricks runtime behavior can be inspected rather than assuming logical types from documentation.

---

## 4. Source Preservation

Cursor did not add:

```text
deduplication
NULL replacement
foreign-key correction
business filtering
quality filtering
```

### Why accepted

Bronze represents what arrived from the source.

The deliberately seeded quality problems must remain available for Silver validation.

---

## 5. `_ingested_at` Metadata

Each Bronze dataset receives:

```text
_ingested_at
```

using the current Databricks timestamp.

### Why accepted

This provides simple operational lineage without modifying the business fields.

Additional metadata was deliberately kept minimal.

---

## 6. Delta Table Output

The scripts persist Bronze data using:

```text
Delta
```

and:

```text
saveAsTable(...)
```

### Why accepted

Delta is the intended storage format for the Databricks Medallion pipeline and provides managed business-layer tables that can be consumed cleanly by Silver.

---

## 7. Overwrite-Based Rerun Behavior

The generated implementation uses:

```python
.mode("overwrite")
.option("overwriteSchema", "true")
```

### Why accepted

This exercise currently processes one synthetic source snapshot.

Using overwrite means repeated development runs replace the current Bronze snapshot rather than appending another copy and corrupting expected row counts.

A production ingestion solution could require incremental behavior, but that is outside the current project scope.

---

## 8. Structural Source Validation

The scripts check:

* expected column names,
* expected source row count.

For example, customer ingestion expects:

```text
10,000 rows
```

with the documented customer columns.

### Why accepted

These are pipeline/input-contract checks rather than Silver data-quality checks.

A structurally incorrect input file should fail the ingestion clearly instead of silently generating an unexpected Bronze table.

---

## 9. Source-to-Bronze Count Reconciliation

After writing the Delta table, the script compares:

```text
source_count
```

with:

```text
bronze_count
```

and fails if they differ.

### Why accepted

The key Bronze contract is source preservation.

Row-count reconciliation is a simple and meaningful way to verify that ingestion has not accidentally dropped or multiplied rows.

---

# What I Changed

## Change 1 — Removed Explicit SparkSession Retrieval

### Initial AI implementation

Cursor initially added logic similar to:

```python
SparkSession.getActiveSession()
```

inside each Bronze ingestion file.

### Change requested

I separately asked Cursor to remove this logic and use the Databricks-provided:

```python
spark
```

session directly.

### Why I changed it

These ingestion scripts are designed specifically to run in Databricks.

Databricks already provides an active Spark session through the global:

```python
spark
```

variable.

Adding explicit session discovery through:

```python
SparkSession.getActiveSession()
```

was unnecessary for this environment and added boilerplate without improving functionality.

The revised implementation therefore uses:

```python
spark.read...
spark.sql(...)
spark.table(...)
```

directly.

### Result

The scripts are now simpler and better aligned with their Databricks-only execution context.

The setup documentation was also updated to make this environment assumption explicit.

---

## Change 2 — Simplified the Prompt Validation Scope

The final Bronze prompt was intentionally shorter than the initial version considered during planning.

Detailed Silver-style quality validation was removed from the prompt.

### Why I changed it

The Bronze checkpoint should primarily prove:

```text
source can be read
+
source structure is expected
+
rows are preserved
+
Bronze Delta table is created
```

It should not become an early Silver validation layer.

The final implementation still performs lightweight structural safeguards such as expected columns and expected row counts, but it does not evaluate business/data-quality rules.

---

## Change 3 — No `ingest_all.py` in the Current Bronze Scope

The Bronze prompt focused on the three individual ingestion scripts and supporting setup files.

### Why

Running the three small scripts independently is sufficient for the current checkpoint.

A combined runner is not necessary to prove Bronze ingestion and can be introduced only if it provides useful value later.

This keeps the checkpoint focused.

---

# What I Rejected / Avoided

## 1. Creating a Spark Session Manually

Rejected:

```python
SparkSession.builder...
```

and unnecessary active-session lookup logic.

### Reason

The Databricks runtime already supplies `spark`.

---

## 2. Bronze Data Cleaning

Rejected any logic that would:

```text
drop duplicates
fill NULLs
fix foreign keys
filter bad rows
change source business values
```

### Reason

These responsibilities belong to Silver.

---

## 3. Silver Data-Quality Validation in Bronze

Rejected completeness, uniqueness, referential-integrity, type-validation, and business-logic evaluation from this layer.

### Reason

Running these rules during Bronze ingestion would blur the layer responsibilities established in the project design.

---

## 4. Auto Loader / Streaming

Not used.

### Reason

The project uses three small static CSV files and does not require incremental or streaming ingestion.

Adding Auto Loader or streaming would increase scope without improving the exercise.

---

## 5. Complex Configuration Framework

Not added.

### Reason

The source paths and table names are currently simple and known.

A configuration framework would add unnecessary abstraction for this exercise.

---

# Example Implementation — Customers

The final customer ingestion script follows this pattern:

```text
Source:
/Volumes/ecommerce_sales/raw/source_files/customers.csv

        ↓

PySpark CSV read
header=True
inferSchema=True

        ↓

Structural validation

        ↓

Add _ingested_at

        ↓

Delta overwrite

        ↓

ecommerce_sales.bronze.customers

        ↓

Source/Bronze count reconciliation
```

The script uses the Databricks-provided:

```python
spark
```

session directly.

It does not create or retrieve a separate `SparkSession`.

---

# Bronze Source Contract

The expected source counts are:

| Dataset   | Source rows | Bronze target                      |
| --------- | ----------: | ---------------------------------- |
| customers |      10,000 | `ecommerce_sales.bronze.customers` |
| orders    |     100,000 | `ecommerce_sales.bronze.orders`    |
| products  |         500 | `ecommerce_sales.bronze.products`  |

The Bronze layer must preserve those physical row counts.

---

# Schema Handling

No explicit casts are performed during this checkpoint.

The source files are loaded using Spark CSV schema inference.

The actual runtime:

```text
printSchema()
```

output is treated as authoritative.

This is especially relevant for fields such as:

```text
lifetime_value
unit_price
total_amount
price
cost
```

whose inferred numeric types may differ from the logical types documented in the project model.

Any required type normalization or validation belongs to a later Silver task rather than being silently added in Bronze.

---

# Source Preservation

The known source problems intentionally remain in Bronze.

These include:

```text
NULL customer email values

duplicate customer_id values

NULL order customer_id values

NULL order product_id values

invalid customer references

invalid product references

duplicate order_id values
```

Bronze is not expected to determine whether these records are valid.

Its responsibility is to preserve them for downstream evaluation.

---

# Rerun Strategy

The Bronze tables use overwrite behavior.

Conceptually:

```text
Current source snapshot
        ↓
overwrite
        ↓
Current Bronze snapshot
```

### Why

During development, rerunning the same source ingestion should not double the dataset.

For this exercise, overwrite provides the simplest idempotent behavior.

---

# Setup Documentation

`database/setup-notes.md` documents:

* Databricks Free Edition,
* Unity Catalog Volume paths,
* required Bronze schema,
* expected execution order,
* expected source/Bronze counts,
* Spark schema inference,
* overwrite behavior,
* Databricks-provided `spark` session.

This provides enough environment context for another engineer to understand how the Bronze scripts should be run.

---

# Evaluation of Cursor Output

## What was good

* Correctly used the Databricks Volume paths.
* Kept the Bronze layer focused on raw ingestion.
* Preserved source quality defects.
* Used schema inference as required.
* Added lightweight ingestion metadata.
* Used Delta tables.
* Added rerun-safe overwrite behavior.
* Added useful structural checks.
* Reconciled source and persisted row counts.
* Kept the implementation small and readable.

## What needed adjustment

The initial scripts included explicit Spark session retrieval using:

```python
SparkSession.getActiveSession()
```

This was unnecessary because Databricks already provides:

```python
spark
```

The code was subsequently simplified to use the Databricks session directly.

---

# Final Decision

**ACCEPTED WITH MODIFICATION**

The overall Bronze design and generated implementation were accepted.

One implementation detail was intentionally changed:

```text
Explicit SparkSession retrieval
        ↓
removed
        ↓
Databricks-provided spark session used directly
```

This simplified the scripts and aligned them more closely with the execution environment.

No further Bronze complexity was added.

---

# Checkpoint Status

Current checkpoint:

```text
Checkpoint 3 — Bronze Layer
```

Implementation files have been created.

Before moving to Silver, the Bronze tables should be executed in Databricks and the actual runtime outputs should be recorded, including:

```text
source row counts
Bronze row counts
inferred schemas
successful Delta table creation
```

Once those results are confirmed, Checkpoint 3 can be considered complete and work can proceed to:

```text
Checkpoint 4 — Silver Layer
```
