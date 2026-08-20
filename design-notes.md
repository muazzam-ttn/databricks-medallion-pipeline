# Design Notes

## 1. Architecture Overview

The project follows a standard Databricks Medallion Architecture:

```text
Synthetic CSV Files
      |
      v
+-------------+
|   Bronze    |
| Raw ingest  |
+-------------+
      |
      v
+-------------+
|   Silver    |
| Validation  |
| + quality   |
|   flags     |
+-------------+
      |
      v
+-------------+
|    Gold     |
| Business    |
| aggregates  |
+-------------+
      |
      v
+-------------+
| Databricks  |
| SQL         |
| Dashboard   |
+-------------+
```

The pipeline consists of four logical stages:

1. **Data Generation**
   - Generate synthetic customer, order, and product CSV files.
   - Introduce known data-quality problems intentionally.
   - Record how and why each problem was created.

2. **Bronze**
   - Ingest source CSV files.
   - Preserve the source data without business cleaning.
   - Add only operational ingestion metadata where required.

3. **Silver**
   - Apply data-quality validations.
   - Retain all records.
   - Add row-level quality information.
   - Produce quality metrics.

4. **Gold**
   - Use analytics-eligible Silver data.
   - Build business aggregations for products and customers.
   - Produce datasets used directly by the dashboard.

The design intentionally favors transparency and traceability over complexity because the main objective is to demonstrate a disciplined AI-assisted engineering workflow.

---

# 2. Design Principles

The following principles guide the implementation.

## 2.1 Preserve Source Data

Bronze represents the raw source.

No duplicate removal, NULL handling, filtering, or business correction should occur during Bronze ingestion.

This is important because the intentionally generated quality problems must remain traceable into Silver.

---

## 2.2 Validate Before Transforming

Data-quality validation belongs in Silver rather than Bronze.

This provides a clear separation between:

- what arrived,
- what is valid,
- what should be used for analytics.

---

## 2.3 Flag Rather Than Delete

Records failing quality checks will remain in the Silver layer.

Each record should expose enough information to determine whether it passed validation and, if not, which validations failed.

This supports:

- debugging,
- reconciliation,
- quality reporting,
- verification that the intentional test cases were detected.

---

## 2.4 Gold Should Represent Trusted Analytics Data

Gold tables should not blindly aggregate every Silver row.

Rows used for Gold must meet an explicitly documented set of quality requirements.

The initial design is:

```text
Bronze record
   ↓
Silver validations
   ↓
analytics_eligible?
   ├── yes → Gold
   └── no  → retained in Silver for investigation
```

The exact eligibility criteria are documented in the data-quality strategy.

---

## 2.5 Keep Business Logic Explicit

Rules such as:

- which order statuses count as revenue,
- how customers are segmented,
- what `lifetime_value_actual` means,

must be explicit and documented rather than hidden inside SQL.

---

## 2.6 Keep the Exercise Reproducible

The data-generation process should use a fixed random seed.

This makes:

- generated input stable,
- expected quality counts testable,
- debugging easier,
- reviewer validation repeatable.

---

# 3. Logical Data Model

The project contains three source entities.

## 3.1 Customers

Logical grain:

> One customer record per `customer_id`, except for intentionally introduced duplicate-key quality issues.

Fields:

| Column | Logical Type | Purpose |
|---|---|---|
| customer_id | INT | Customer identifier |
| customer_name | STRING | Synthetic customer name |
| email | STRING | Synthetic email address |
| country | STRING | Customer country |
| signup_date | DATE | Customer registration date |
| customer_segment | STRING | Premium / Standard / Basic |
| lifetime_value | DECIMAL | Synthetic source-system customer value |

Primary-key expectation:

```text
customer_id
```

---

## 3.2 Products

Logical grain:

> One product per `product_id`.

Fields:

| Column | Logical Type | Purpose |
|---|---|---|
| product_id | INT | Product identifier |
| product_name | STRING | Product name |
| category | STRING | Product category |
| price | DECIMAL | Selling/catalog price |
| cost | DECIMAL | Product cost |
| stock_quantity | INT | Current stock |
| reorder_level | INT | Reorder threshold |

Primary-key expectation:

```text
product_id
```

---

## 3.3 Orders

Logical grain:

> One order record per `order_id`, except for intentionally introduced duplicate-key quality issues.

Fields:

| Column | Logical Type | Purpose |
|---|---|---|
| order_id | INT | Order identifier |
| customer_id | INT | Reference to customer |
| order_date | DATE | Order date |
| product_id | INT | Reference to product |
| quantity | INT | Quantity purchased |
| unit_price | DECIMAL | Price per item |
| total_amount | DECIMAL | Order total |
| order_status | STRING | Pending / Completed / Cancelled |
| payment_date | DATE | Payment date, nullable |

Foreign-key expectations:

```text
orders.customer_id → customers.customer_id
orders.product_id  → products.product_id
```

---

# 4. Physical Layer Design

The exact catalog/schema names depend on the Databricks environment.

Recommended logical naming:

```text
bronze.customers
bronze.orders
bronze.products

silver.customers
silver.orders
silver.products
silver.quality_metrics

gold.sales_by_product
gold.revenue_by_customer
gold.customer_segmentation
```

If the selected Databricks environment does not support separate schemas conveniently, a naming-prefix approach may be used instead:

```text
bronze_customers
silver_customers
gold_sales_by_product
```

The final convention should be chosen based on the actual workspace capabilities rather than hard-coded prematurely.

---

# 5. Data Generation Design

## 5.1 Technology

Preferred implementation:

```text
Python + pandas + Faker
```

Reasoning:

The generation workload is modest:

- ~10,000 customers
- ~100,000 orders
- ~500 products

pandas and Faker are sufficient and make intentional quality manipulation straightforward and readable.

PySpark is unnecessary for generating datasets at this scale.

The generated files will then be processed using PySpark in Databricks.

---

## 5.2 Generation Order

Data should be generated in dependency order:

```text
Products
   ↓
Customers
   ↓
Orders
```

Customers and products must exist before valid order foreign keys are generated.

The exact order between customers and products is otherwise irrelevant.

---

## 5.3 Reproducibility

Use deterministic random seeds for:

- Python `random`
- NumPy, if used
- Faker

This allows repeated generation to produce predictable test inputs.

---

## 5.4 Intentional Issue Injection

Generate a valid baseline dataset first.

Then deliberately modify selected records to create the required problems.

Conceptually:

```text
Generate valid dataset
        ↓
Validate baseline assumptions
        ↓
Select deterministic/random indexes
        ↓
Inject documented bad conditions
        ↓
Validate issue counts
        ↓
Write CSV
```

This is preferable to creating invalid records throughout the generation process because it makes exact issue counts easier to control and test.

---

## 5.5 Avoiding Issue Overlap

Where practical, the intentionally corrupted row groups should be non-overlapping.

For example, an order selected for:

```text
NULL customer_id
```

should preferably not also be selected for:

```text
NULL product_id
```

unless deliberately intended.

This makes expected quality metrics easier to explain.

However, the Silver implementation must still support rows failing multiple quality checks.

---

# 6. Bronze Layer Design

## 6.1 Objective

Bronze captures exactly what arrived from the source CSV files.

Bronze is not responsible for evaluating business correctness.

---

## 6.2 Input

Source files:

```text
data/customers.csv
data/orders.csv
data/products.csv
```

During Databricks execution these files will be referenced through a configurable Databricks-accessible path.

Possible locations depend on the selected environment:

- DBFS
- Unity Catalog Volume
- workspace-accessible storage
- other supported Databricks file location

The actual path must not be deeply hard-coded across multiple scripts.

---

## 6.3 Schema Handling

The exercise requests schema inference.

Therefore Bronze will read CSV using schema inference unless the selected implementation requires minor adjustments for safe malformed-value detection.

Expected options:

```python
header=True
inferSchema=True
```

The inferred schema must be inspected and recorded during validation.

A separate logical expected schema should still be documented so the pipeline can detect unexpected inferred results.

---

## 6.4 Bronze Transformations

Allowed:

- ingestion timestamp,
- source-file information if useful,
- ingestion/run metadata.

Not allowed:

- duplicate removal,
- NULL replacement,
- referential validation,
- invalid row filtering,
- business corrections.

---

## 6.5 Operational Metadata

Recommended metadata column:

```text
_ingested_at
```

Optional metadata:

```text
_source_file
```

These fields are operational rather than business transformations.

---

## 6.6 Row Count Logging

Each ingestion should record:

```text
source
bronze_table
row_count
ingestion_timestamp
```

For this exercise, simple logging/output is sufficient.

A dedicated ingestion-audit framework is unnecessary.

---

## 6.7 Rerun Behavior

Development execution must be predictable.

For the exercise, Bronze tables should be recreated/overwritten from the current generated source files.

Reason:

The input represents one synthetic exercise batch rather than a production incremental feed.

This prevents accidental duplicate loading when scripts are rerun during development.

---

# 7. Silver Layer Design

## 7.1 Objective

Silver provides validated, typed, and quality-enriched representations of Bronze data.

Silver should answer:

> Which records are trustworthy, which records have problems, and why?

---

## 7.2 Validation Categories

Five logical quality categories will be implemented:

1. Completeness
2. Uniqueness
3. Type validation
4. Referential integrity
5. Business logic

The first three explicitly required core categories from the problem definition remain central:

- completeness,
- uniqueness,
- referential integrity.

Type and business validation provide additional engineering depth.

---

## 7.3 Quality Representation

Each Silver dataset should contain:

```text
quality_check_result
```

Recommended values:

```text
PASS
FAIL
```

A second column is recommended:

```text
quality_failure_reasons
```

Example:

```text
["NULL_CUSTOMER_ID", "INVALID_QUANTITY"]
```

This is clearer than storing only:

```text
FAIL
```

because reviewers and engineers can inspect the root cause directly.

---

## 7.4 Quality Check Columns

Implementation options include:

### Option A — Individual Boolean Columns

```text
completeness_pass
uniqueness_pass
type_validation_pass
referential_integrity_pass
business_logic_pass
quality_check_result
quality_failure_reasons
```

### Option B — Only Final Result + Reasons

```text
quality_check_result
quality_failure_reasons
```

### Selected Design

Use **individual check results plus final result**.

Reason:

This makes:

- metrics easier to generate,
- debugging easier,
- tests more explicit,
- reviewer inspection simpler.

Example:

```text
completeness_pass            = true
uniqueness_pass              = true
type_validation_pass         = true
referential_integrity_pass   = false
business_logic_pass          = true
quality_check_result         = "FAIL"
quality_failure_reasons      = ["INVALID_CUSTOMER_REFERENCE"]
```

---

# 8. Uniqueness Design

Duplicate detection must not silently remove data.

Example approach:

```text
COUNT(*) OVER (PARTITION BY customer_id)
```

Then:

```text
count > 1 → uniqueness failure
```

The same pattern applies to:

```text
order_id
```

Both copies of a duplicate identifier will be marked as participating in a uniqueness violation.

This distinction must be considered when comparing seeded duplicate-row counts with Silver failed-row counts.

---

# 9. Referential Integrity Design

Order foreign keys will be checked against distinct parent identifier sets.

For customers:

```text
SELECT DISTINCT customer_id
FROM bronze/silver customers
WHERE customer_id IS NOT NULL
```

For products:

```text
SELECT DISTINCT product_id
FROM bronze/silver products
WHERE product_id IS NOT NULL
```

Then check order references against these sets.

Using distinct parent IDs prevents duplicate customer rows from multiplying order records during joins.

---

# 10. Type Validation Design

CSV input creates a design challenge because schema inference may convert malformed values to NULL or potentially infer a wider STRING type.

Type validation therefore needs to distinguish:

```text
actual missing value
```

from:

```text
value present in CSV but unparsable as expected type
```

During implementation, we will validate how Databricks CSV inference behaves against the generated dataset before deciding whether additional raw-string parsing is required.

Because the exercise does not require intentionally seeded malformed types, type validation should remain lightweight.

The objective is to show validation thinking rather than build a generic schema-validation framework.

---

# 11. Business Logic Validation Design

Selected candidate rules:

## Customers

```text
customer_segment IN ('Premium', 'Standard', 'Basic')

lifetime_value >= 0

signup_date <= current_date()
```

## Products

```text
price >= 0
cost >= 0
stock_quantity >= 0
reorder_level >= 0
```

Possible additional rule:

```text
price >= cost
```

This will only be enforced if generation logic explicitly guarantees that relationship.

It should not be invented as a universal business requirement.

## Orders

```text
quantity > 0

unit_price >= 0

total_amount >= 0

order_status IN ('Pending', 'Completed', 'Cancelled')
```

Recommended consistency rule:

```text
total_amount ≈ quantity * unit_price
```

using decimal-safe comparison.

Payment-date validation will remain conservative because the problem does not fully define payment semantics.

---

# 12. Analytics Eligibility Design

Not every quality failure necessarily has the same effect on every Gold table.

For simplicity and transparency, the initial rule will be:

```text
quality_check_result = 'PASS'
```

for records included in Gold fact-based calculations.

This creates a clear contract:

> Gold uses only Silver records that passed all configured validations.

Potential exception:

Customer records with NULL email do not technically prevent revenue aggregation.

However, selectively ignoring some validation failures would introduce additional eligibility complexity.

For this exercise, using full Silver quality pass as the default Gold eligibility rule is clearer and easier to explain.

This should be reviewed after actual data-quality metrics are available.

---

# 13. Gold Layer Design

Gold tables represent business-ready outputs.

The three mandatory aggregations are:

1. Sales by Product
2. Revenue by Customer
3. Customer Segmentation

---

# 14. Gold — Sales by Product

Target table:

```text
gold.sales_by_product
```

Grain:

> One row per product.

Columns:

```text
product_id
product_name
category
total_orders
total_revenue
avg_order_value
```

Expected calculation:

```text
total_orders =
COUNT(DISTINCT order_id)

total_revenue =
SUM(total_amount)

avg_order_value =
AVG(total_amount)
```

Only analytics-eligible orders should contribute to calculations.

### Open Decision

Revenue order status has not been explicitly specified.

Recommended default for later confirmation:

```text
Completed orders only
```

because revenue normally represents realized sales.

However, this must be documented as a project-defined business assumption rather than presented as a requirement from the guide.

---

# 15. Gold — Revenue by Customer

Target table:

```text
gold.revenue_by_customer
```

Grain:

> One row per valid customer.

Columns:

```text
customer_id
customer_name
customer_segment
total_orders
total_revenue
avg_order_value
lifetime_value_actual
```

Proposed calculation:

```text
total_orders =
COUNT(DISTINCT order_id)

total_revenue =
SUM(total_amount)

avg_order_value =
AVG(total_amount)

lifetime_value_actual =
SUM(total_amount)
```

under the same revenue-status rules.

`lifetime_value_actual` will therefore represent calculated revenue from available order history.

The original source:

```text
customers.lifetime_value
```

can be retained in Silver but is not treated as the calculated actual value.

---

# 16. Gold — Customer Segmentation

Target table:

```text
gold.customer_segmentation
```

Columns:

```text
segment_type
customer_count
avg_revenue
total_revenue
```

Required labels:

```text
High-Value
Repeat
One-Time
Inactive
```

The exercise does not define segmentation thresholds.

Recommended design:

Apply segmentation at the individual-customer level before aggregating counts.

Example conceptual logic:

```text
Inactive:
    total_orders = 0

One-Time:
    total_orders = 1

Repeat:
    total_orders > 1
    AND not High-Value

High-Value:
    revenue meets selected high-value threshold
```

The High-Value threshold must be deliberately chosen and documented.

A data-driven threshold such as a percentile may be preferable to an arbitrary hard-coded monetary amount.

The final threshold will be selected after inspecting generated revenue distribution.

---

# 17. Customers With No Orders

The segmentation design must preserve customers with no valid orders.

Therefore customer segmentation must start from the customer population and LEFT JOIN revenue/order aggregations.

Conceptually:

```text
customers
LEFT JOIN customer_revenue
```

rather than:

```text
orders
INNER JOIN customers
```

Without this, the `Inactive` segment would disappear.

---

# 18. Optional Daily/Weekly Trends

`03_daily_weekly_trends.sql` will remain in the repository structure.

It is optional.

It should not be implemented until:

- mandatory pipeline works,
- testing is complete,
- required documentation is complete.

---

# 19. Dashboard Design

The dashboard will be built from Gold tables.

## Tile 1 — Top 10 Products by Revenue

Source:

```text
gold.sales_by_product
```

Visualization:

```text
Bar chart
```

Logic:

```text
ORDER BY total_revenue DESC
LIMIT 10
```

Purpose:

Identify the products generating the highest revenue.

---

## Tile 2 — Customer Revenue Distribution

Source:

```text
gold.revenue_by_customer
```

Visualization:

```text
Histogram
```

Measure:

```text
total_revenue
```

Purpose:

Show how customer revenue is distributed and whether revenue is concentrated among a smaller customer population.

---

## Tile 3 — Customer Segmentation

Source:

```text
gold.customer_segmentation
```

Visualization:

```text
Pie chart
```

Dimensions:

```text
segment_type
customer_count
```

Purpose:

Show the distribution of customers across behavioral/value segments.

---

# 20. Quality Metrics Design

A Silver quality metrics dataset is recommended.

Target:

```text
silver.quality_metrics
```

Example structure:

| dataset | check_name | records_evaluated | records_passed | records_failed | pass_percentage | evaluated_at |
|---|---|---:|---:|---:|---:|---|
| customers | completeness | ... | ... | ... | ... | ... |
| customers | uniqueness | ... | ... | ... | ... | ... |
| orders | completeness | ... | ... | ... | ... | ... |

This provides a clear reusable output rather than relying only on console messages.

---

# 21. Testing Design

Testing will be developed alongside the relevant pipeline stages.

The most important tier is:

> Data quality detection validation.

Tests should demonstrate that known generated problems are actually detected.

Examples:

```text
expected NULL email rows detected

expected NULL customer_id rows detected

expected NULL product_id rows detected

expected invalid customer references detected

expected invalid product references detected

duplicate key conditions detected
```

Testing should also include a small integration path:

```text
CSV
 → Bronze
 → Silver
 → Gold
```

with row-count and aggregation sanity checks.

---

# 22. Debugging Approach

Debugging will follow a repeatable process:

1. Reproduce the issue.
2. Capture the error or incorrect result.
3. Identify the smallest failing component.
4. Inspect input/schema/data assumptions.
5. Ask AI for possible causes when useful.
6. Validate AI hypotheses manually.
7. Apply the smallest appropriate fix.
8. Rerun relevant tests.
9. Record the issue and fix in `debugging-notes.md`.

AI suggestions will not be accepted solely because they appear plausible.

---

# 23. Error Handling Design

The exercise requires input validation and error handling.

Each ingestion path should validate:

- source exists,
- expected columns exist,
- dataset can be read,
- target table can be written.

Errors should fail clearly.

Example principle:

```text
fail fast on structural pipeline errors
flag data-quality errors inside the dataset
```

A missing input file is a pipeline error.

A NULL email is a data-quality condition.

These should not be handled the same way.

---

# 24. Configuration Approach

Avoid unnecessary configuration frameworks.

A small configuration section/object should hold values such as:

```text
source_path
catalog
bronze_schema
silver_schema
gold_schema
```

The goal is to prevent hard-coded values from appearing throughout every script.

---

# 25. AI-Assisted Development Approach

Cursor/AI should receive:

- project context,
- approved requirements,
- approved design,
- current task scope.

Each prompt should focus on one unit of work.

Example progression:

```text
Requirements
      ↓
Design
      ↓
Data generation
      ↓
Test
      ↓
Bronze
      ↓
Test
      ↓
Silver
      ↓
Test
      ↓
Gold
      ↓
Validate
      ↓
Dashboard
```

The AI should not be asked to generate the complete repository implementation in one prompt.

This supports meaningful iteration and makes acceptance/rejection decisions visible.

---

# 26. Decisions Deferred Until Implementation

The following decisions remain intentionally unresolved:

1. Exact Databricks storage path.
2. Catalog/schema naming based on workspace capabilities.
3. Final revenue-status rule.
4. Exact High-Value customer threshold.
5. Exact type-validation implementation after inspecting CSV parsing behavior.
6. Whether an explicit `tests/` folder is useful after the first test tier is implemented.

These should be resolved with evidence rather than guessed during initial design.