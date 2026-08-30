# Databricks Medallion Pipeline

## Overview

This project implements a batch e-commerce analytics pipeline on Databricks
Free Edition. It uses deterministic synthetic CSV data so the expected
data-quality conditions are known before ingestion.

The pipeline preserves source defects in Bronze, annotates every row with
quality results in Silver, builds business-ready Gold aggregations from
qualifying data, and provides SQL queries and setup guidance for a Databricks
dashboard.

All customer-like data is synthetic. No production customer data is used.

## Architecture

```text
Synthetic CSV files
        ↓
Bronze Delta tables
source-preserving ingestion
        ↓
Silver Delta tables
quality flags and failure reasons
        ↓
Gold Delta tables
business aggregations
        ↓
Databricks SQL dashboard
```

Layer responsibilities:

- Bronze reads the uploaded CSV files, preserves every physical row, and adds
  only `_ingested_at`.
- Silver preserves Bronze row counts while adding completeness, uniqueness,
  type, referential-integrity, and business-logic results.
- Gold uses qualifying Silver records and Completed orders for revenue
  calculations.
- Dashboard queries read Gold tables only.

## Technology Stack

- Python
- pandas and Faker for synthetic data generation
- PySpark for Bronze and Silver processing
- Databricks Free Edition
- Unity Catalog Volumes
- Delta Lake
- Databricks SQL

## Databricks Environment

The implemented environment uses:

```text
Catalog:        ecommerce_sales
Source schema:  raw
Volume:         source_files
Bronze schema:  bronze
Silver schema:  silver
Gold schema:    gold
```

The source Volume is:

```text
ecommerce_sales.raw.source_files
```

Uploaded source paths:

```text
/Volumes/ecommerce_sales/raw/source_files/customers.csv
/Volumes/ecommerce_sales/raw/source_files/orders.csv
/Volumes/ecommerce_sales/raw/source_files/products.csv
```

The catalog, `raw` schema, Volume, and uploaded files must exist before Bronze
ingestion. `database/schema.sql` creates the Bronze schema. The Silver and Gold
runners create their target schemas if required.

Databricks supplies the active `spark` session; the pipeline scripts do not
create a separate `SparkSession`.

## Repository Structure

```text
data/
  customers.csv
  orders.csv
  products.csv

src/
  data_generation/
    generate_sample_data.py
    DATA_GENERATION_NOTES.md

  bronze/
    01_ingest_customers.py
    02_ingest_orders.py
    03_ingest_products.py

  silver/
    01_quality_completeness.py
    02_quality_uniqueness.py
    03_quality_type_validation.py
    04_quality_referential_integrity.py
    05_quality_business_logic.py
    create_silver_tables.py

  gold/
    01_sales_by_product.sql
    02_revenue_by_customer.sql
    03_daily_weekly_trends.sql
    04_customer_segmentation.sql
    create_gold_tables.py

  dashboard/
    dashboard_queries.sql
    DASHBOARD_GUIDE.md

database/
  schema.sql
  setup-notes.md

ai-prompts/
tool-specific/cursor-workflow/
debugging-notes.md
tool-workflow.md
```

## Synthetic Data Generation

Run from the repository root:

```text
python src/data_generation/generate_sample_data.py
```

Prerequisites are Python, pandas, and Faker.

The generator uses fixed seeds:

```text
Python random: 20260820
Faker:         20260821
```

It creates:

- 10,000 customer rows
- 100,000 order rows
- 500 product rows

The generator builds valid baselines first, injects only the required defects,
and validates the final data before writing the CSV files. Monetary values are
generated from integer cents using `Decimal`.

See `src/data_generation/DATA_GENERATION_NOTES.md` for the complete generation
contract.

## Seeded Quality Issues

Customers contain:

- 50 NULL emails
- 10 rows modified to reuse existing `customer_id` values
- 20 physical rows participating in the resulting duplicate-key groups

Orders contain:

- 100 NULL `customer_id` values
- 200 NULL `product_id` values
- 50 non-null invalid customer references
- 30 non-null invalid product references
- 20 rows modified to reuse existing `order_id` values
- 40 physical rows participating in the resulting duplicate-key groups

Products have no intentionally seeded defects and contain 500 unique product
IDs.

Defect groups are non-overlapping where practical. No additional malformed
types or business-rule failures were added to force an approximate issue count.

## Bronze Execution

Run `database/schema.sql`, then execute these files on Databricks compute:

```text
src/bronze/01_ingest_customers.py
src/bronze/02_ingest_orders.py
src/bronze/03_ingest_products.py
```

They create:

```text
ecommerce_sales.bronze.customers
ecommerce_sales.bronze.orders
ecommerce_sales.bronze.products
```

Each script:

- reads its CSV with headers and Spark schema inference,
- validates the expected columns and source row count,
- adds `_ingested_at`,
- writes a Delta table using overwrite mode,
- compares source and Bronze row counts,
- prints the inferred and persisted schemas.

Bronze does not clean, filter, deduplicate, fill NULLs, or repair foreign keys.
See `database/setup-notes.md` for environment details.

## Silver Quality Approach

Run:

```text
src/silver/create_silver_tables.py
```

The runner imports and composes the five validation modules and creates:

```text
ecommerce_sales.silver.customers
ecommerce_sales.silver.orders
ecommerce_sales.silver.products
```

Every Silver row contains:

```text
completeness_pass
uniqueness_pass
type_validation_pass
referential_integrity_pass
business_logic_pass
quality_check_result
quality_failure_reasons
```

Important behavior:

- Duplicate detection uses a window count and flags every physical row in a
  duplicate-key group.
- Referential validation checks Orders against distinct parent IDs, preventing
  duplicate customer IDs from multiplying rows.
- NULL foreign keys fail completeness but are not classified as orphan
  references.
- Type validation checks the inferred Spark schema against approved logical
  type families.
- Business checks use only the documented customer, order, and product rules.
- Failed rows remain in Silver with specific failure reasons.
- The runner compares Bronze and Silver physical row counts and prints overall
  and dimension-level pass/fail summaries.

The numeric validation-module filenames are loaded with
`importlib.import_module()`. This approach was validated in Databricks.

## Gold Outputs

Run:

```text
src/gold/create_gold_tables.py
```

Keep the runner and its four sibling SQL files in the same Databricks folder.
The runner uses the notebook working directory to locate them.

It creates:

### `ecommerce_sales.gold.sales_by_product`

One row per valid product, including qualifying Completed-order count, total
revenue, and average order value.

### `ecommerce_sales.gold.revenue_by_customer`

One row per valid customer. Customers without qualifying orders are retained
with zero order and revenue values.

`lifetime_value_actual` is the sum of qualifying Completed-order
`total_amount`.

### `ecommerce_sales.gold.daily_weekly_trends`

Daily and Monday-based weekly aggregates with:

```text
period_type
period_start
total_orders
total_revenue
avg_order_value
```

### `ecommerce_sales.gold.customer_segmentation`

Customer-level revenue is ranked into a deterministic top quintile. Segment
precedence is:

```text
High-Value → Repeat → One-Time → Inactive
```

Definitions:

- High-Value: top 20% by `lifetime_value_actual`, with at least one qualifying
  order
- Repeat: more than one qualifying order and not High-Value
- One-Time: exactly one qualifying order and not High-Value
- Inactive: zero qualifying orders

All Gold revenue calculations use Silver rows with
`quality_check_result = 'PASS'` and `order_status = 'Completed'`.

The Gold runner checks business-key grain, Silver-to-Gold populations, trend
reconciliation, required segment labels, and segmentation population totals.

## Dashboard

Dashboard SQL is stored in:

```text
src/dashboard/dashboard_queries.sql
```

Required visualizations:

- Top 10 products by revenue — bar chart
- Customer revenue distribution — histogram
- Customer segmentation — pie chart

An additional weekly revenue line chart is provided but is not required for the
three-tile dashboard.

The queries use Gold tables only. Detailed Databricks SQL setup, field mappings,
filters, and business interpretations are documented in
`src/dashboard/DASHBOARD_GUIDE.md`.

## Run Order

1. Install pandas and Faker in the local generation environment.
2. Run `src/data_generation/generate_sample_data.py`.
3. Upload the three generated CSV files to
   `ecommerce_sales.raw.source_files`.
4. Run `database/schema.sql`.
5. Run the three Bronze ingestion scripts.
6. Run `src/silver/create_silver_tables.py`.
7. Run `src/gold/create_gold_tables.py` with the Gold SQL files in the same
   Databricks folder.
8. Run the statements in `src/dashboard/dashboard_queries.sql` individually
   and configure the visualizations using `DASHBOARD_GUIDE.md`.

## Validation Approach

Validation is built into each stage:

- Data generation asserts physical counts, required columns, exact NULL and
  orphan counts, duplicate semantics, parent references, and business-valid
  baseline values.
- Bronze checks source contracts and source-to-table row preservation.
- Silver checks Bronze-to-Silver row preservation, records specific failure
  reasons, and prints quality summaries.
- Gold validates output grains and reconciles customer, product, segmentation,
  and trend populations.
- Dashboard queries were checked to ensure they read only Gold tables.

The project records actual debugging decisions in `debugging-notes.md`.
Runtime outcomes should be accepted only after inspecting them in the target
Databricks workspace.

## Assumptions

- The input represents one deterministic synthetic batch rather than a
  production incremental feed.
- Unity Catalog and the `ecommerce_sales` catalog are available.
- The source files have been uploaded to the configured Volume paths.
- Development reruns intentionally overwrite Bronze, Silver, and Gold outputs.
- Spark CSV inference is used in Bronze as required by the project.
- `payment_date` is legitimately nullable.
- Completed, quality-passing Silver orders are the revenue population.
- Databricks provides `spark` and uses the notebook folder as the current
  working directory for the Gold runner.

## Known Limitations

- The solution is batch-only and processes one snapshot.
- Source and target locations are project-specific constants rather than an
  environment configuration package.
- Bronze relies on inferred CSV schemas.
- The Silver modules use numeric filenames and dynamic imports.
- There is no workflow orchestration, automated deployment, or CI pipeline.
- Dashboard creation remains a manual Databricks SQL configuration step.
- The repository does not contain exported Delta tables or dashboard objects.
- The Gold runner's `Path.cwd()` behavior must be validated in the target
  notebook folder when the project is rerun.

## AI-Assisted Workflow

Cursor was used for requirements analysis, design, focused implementation,
validation planning, debugging, and documentation. Work was divided into
checkpoints with explicit file scopes and stop conditions rather than generated
as one large change.

Persistent context is stored in:

```text
tool-specific/cursor-workflow/
```

Prompt histories are stored in:

```text
ai-prompts/
```

The full first-person workflow, accepted and rejected suggestions, validation
approach, responsible-AI boundaries, and production considerations are
documented in `tool-workflow.md`.