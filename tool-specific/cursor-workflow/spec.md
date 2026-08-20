# Project Specification

## 1. Purpose

This specification defines the expected implementation for the Databricks Medallion Pipeline AI Capability Exercise.

It is an implementation-facing summary of the approved planning documents:

```text
requirements-analysis.md
design-notes.md
data-model.md
data-quality-strategy.md
tool-specific/cursor-workflow/project-context.md
```

These files remain the source of truth for detailed requirements and design decisions.

This specification should be used by Cursor to understand:

- what must be built,
- how the major layers should behave,
- what outputs are required,
- what must be validated,
- what must not be over-engineered.

---

# 2. System Objective

Build a Databricks Medallion Architecture pipeline for synthetic e-commerce sales data.

The end-to-end flow is:

```text
Synthetic CSV Data
        ↓
Bronze
        ↓
Silver
        ↓
Gold
        ↓
Databricks SQL Dashboard
```

The project must also demonstrate disciplined AI-assisted engineering across:

```text
requirements
design
implementation
testing
validation
debugging
documentation
reflection
```

---

# 3. Core Technology Stack

Use:

```text
Python
PySpark
SQL
Databricks
Delta Lake
pandas
Faker
```

Preferred division of responsibilities:

```text
pandas + Faker
→ synthetic data generation

PySpark
→ Bronze and Silver processing

SQL
→ Gold aggregations and dashboard queries
```

Use another approach only when justified by the approved design.

---

# 4. Repository Structure

The project should follow this structure:

```text
databricks-medallion-pipeline/
├── README.md
├── candidate-info.md
├── tool-workflow.md
├── requirements-analysis.md
├── design-notes.md
├── data-model.md
├── data-quality-strategy.md
│
├── src/
│   ├── data_generation/
│   │   ├── generate_sample_data.py
│   │   └── DATA_GENERATION_NOTES.md
│   │
│   ├── bronze/
│   │   ├── 01_ingest_customers.py
│   │   ├── 02_ingest_orders.py
│   │   ├── 03_ingest_products.py
│   │   └── ingest_all.py
│   │
│   ├── silver/
│   │   ├── 01_quality_completeness.py
│   │   ├── 02_quality_uniqueness.py
│   │   ├── 03_quality_type_validation.py
│   │   ├── 04_quality_referential_integrity.py
│   │   ├── 05_quality_business_logic.py
│   │   └── create_silver_tables.py
│   │
│   ├── gold/
│   │   ├── 01_sales_by_product.sql
│   │   ├── 02_revenue_by_customer.sql
│   │   ├── 03_daily_weekly_trends.sql
│   │   ├── 04_customer_segmentation.sql
│   │   └── create_gold_tables.py
│   │
│   └── dashboard/
│       ├── dashboard_queries.sql
│       └── DASHBOARD_GUIDE.md
│
├── data/
│   ├── customers.csv
│   ├── orders.csv
│   └── products.csv
│
├── database/
│   ├── schema.sql
│   ├── seed-data-notes.md
│   └── setup-notes.md
│
├── debugging-notes.md
├── reflection.md
├── final-ai-usage-summary.md
│
├── ai-prompts/
│   ├── data-generation.md
│   ├── bronze-layer.md
│   ├── silver-layer.md
│   ├── gold-layer.md
│   ├── dashboard.md
│   ├── debugging.md
│   └── documentation.md
│
└── tool-specific/
    └── cursor-workflow/
        ├── project-context.md
        ├── spec.md
        ├── cursor-rules-or-instructions.md
        └── task-breakdown.md
```

Do not significantly restructure the repository unless explicitly requested.

---

# 5. Source Data Specification

## 5.1 Customers

Target logical size:

```text
10,000 customers
```

Fields:

```text
customer_id          INT
customer_name        STRING
email                STRING
country              STRING
signup_date          DATE
customer_segment     STRING
lifetime_value       DECIMAL
```

Allowed segment values:

```text
Premium
Standard
Basic
```

Intentional issues:

```text
50 NULL email rows
10 duplicate customer_id records
```

---

## 5.2 Orders

Target logical size:

```text
100,000 orders
```

Fields:

```text
order_id             INT
customer_id          INT
order_date           DATE
product_id           INT
quantity             INT
unit_price           DECIMAL
total_amount         DECIMAL
order_status         STRING
payment_date         DATE nullable
```

Allowed status values:

```text
Pending
Completed
Cancelled
```

Intentional issues:

```text
100 NULL customer_id rows
200 NULL product_id rows
50 customer_id values not present in customers
30 product_id values not present in products
20 duplicate order_id records
```

---

## 5.3 Products

Target size:

```text
500 products
```

Fields:

```text
product_id           INT
product_name         STRING
category             STRING
price                DECIMAL
cost                 DECIMAL
stock_quantity       INT
reorder_level        INT
```

No mandatory seeded quality defects are required.

---

# 6. Synthetic Data Generation Specification

Implementation file:

```text
src/data_generation/generate_sample_data.py
```

The generator must:

1. Produce realistic but fully synthetic data.
2. Use reproducible random seeds.
3. Generate valid baseline data first.
4. Inject intentional data-quality issues afterward.
5. Avoid accidental overlap of intentional defects where practical.
6. Validate expected defect conditions before writing output.
7. Produce the three required CSV files.

Output:

```text
data/customers.csv
data/orders.csv
data/products.csv
```

Use only synthetic names and emails.

Never introduce real customer data.

---

# 7. Data Generation Documentation

Create:

```text
src/data_generation/DATA_GENERATION_NOTES.md
```

Document:

- libraries used,
- random seed strategy,
- generation order,
- realistic value-generation approach,
- intentional defects,
- how each defect was injected,
- duplicate semantics,
- expected row counts,
- validation performed after generation.

---

# 8. Bronze Layer Specification

Bronze represents raw ingestion.

Expected tables:

```text
bronze.customers
bronze.orders
bronze.products
```

or an equivalent naming convention if the Databricks environment requires it.

Bronze must:

- read the CSV files,
- preserve all physical input rows,
- preserve source business values,
- preserve intentional quality issues,
- infer or use a source-compatible schema,
- persist as Delta,
- add ingestion metadata,
- report row counts.

Recommended metadata:

```text
_ingested_at
```

Optional:

```text
_source_file
```

Bronze must not:

```text
drop duplicates
fill NULL values
fix bad references
apply quality filtering
apply business cleaning
```

---

# 9. Bronze Validation Requirements

After ingestion verify:

```text
source customer rows = Bronze customer rows

source order rows = Bronze order rows

source product rows = Bronze product rows
```

Also verify that known defects still exist.

Examples:

```text
NULL customer emails remain

NULL order foreign keys remain

duplicate IDs remain

orphan foreign keys remain
```

---

# 10. Silver Layer Specification

Expected tables:

```text
silver.customers
silver.orders
silver.products
```

Silver must:

- retain all Bronze rows,
- evaluate applicable quality rules,
- attach row-level validation results,
- expose failure reasons,
- generate measurable quality metrics.

Silver must not silently delete bad rows.

---

# 11. Required Silver Quality Categories

Implement:

```text
1. Completeness
2. Uniqueness
3. Type Validation
4. Referential Integrity
5. Business Logic
```

The mandatory core quality dimensions are:

```text
Completeness
Uniqueness
Referential Integrity
```

Type validation and business logic are additional project depth.

---

# 12. Silver Quality Metadata

Recommended quality metadata:

```text
completeness_pass
uniqueness_pass
type_validation_pass
referential_integrity_pass
business_logic_pass
quality_check_result
quality_failure_reasons
```

Applicable fields may vary by dataset.

Example:

```text
quality_check_result = "FAIL"

quality_failure_reasons =
[
    "NULL_CUSTOMER_ID",
    "INVALID_QUANTITY"
]
```

Do not hide failure details inside only a generic PASS/FAIL indicator.

---

# 13. Completeness Specification

## Customers

Validate:

```text
email IS NOT NULL
```

Expected seeded failures:

```text
50
```

## Orders

Validate:

```text
customer_id IS NOT NULL
product_id IS NOT NULL
```

Expected seeded failures:

```text
100 NULL customer_id
200 NULL product_id
```

Do not consider NULL `payment_date` a completeness failure because it is legitimately nullable.

---

# 14. Uniqueness Specification

Validate:

```text
customers.customer_id
orders.order_id
products.product_id
```

Do not remove duplicates.

Flag records participating in duplicate groups.

Document and test the difference between:

```text
duplicate rows intentionally added
```

and:

```text
all physical rows participating in duplicate groups
```

---

# 15. Referential Integrity Specification

Apply to Orders.

Validate:

```text
orders.customer_id
```

against:

```text
customers.customer_id
```

Expected orphan references:

```text
50
```

Validate:

```text
orders.product_id
```

against:

```text
products.product_id
```

Expected orphan references:

```text
30
```

Only non-null foreign keys should be evaluated as orphan references.

Use distinct parent keys during existence validation.

Do not allow duplicate parent rows to multiply child rows.

---

# 16. Type Validation Specification

Validate relevant logical data types.

Examples:

```text
integer IDs
dates
quantities
decimal monetary values
stock quantities
```

The exact implementation should be based on observed Databricks CSV parsing behavior.

Do not build a generic schema-validation framework.

If no malformed type rows are intentionally generated, ensure valid data passes and the validation mechanism behaves correctly.

---

# 17. Business Logic Specification

Keep business logic checks modest.

Candidate customer checks:

```text
customer_segment valid
lifetime_value >= 0
signup_date <= current_date()
```

Candidate order checks:

```text
quantity > 0
unit_price >= 0
total_amount >= 0
order_status valid
```

Potential:

```text
total_amount ≈ quantity * unit_price
```

if implemented with decimal-safe logic.

Candidate product checks:

```text
price >= 0
cost >= 0
stock_quantity >= 0
reorder_level >= 0
```

Do not invent unsupported business rules.

---

# 18. Silver Row Preservation Contract

Expected:

```text
bronze.customers count
=
silver.customers count
```

```text
bronze.orders count
=
silver.orders count
```

```text
bronze.products count
=
silver.products count
```

Quality validation annotates rows rather than removes them.

---

# 19. Quality Metrics Specification

Recommended table:

```text
silver.quality_metrics
```

Suggested grain:

> One row per dataset + quality rule + evaluation run.

Suggested columns:

```text
dataset_name
check_category
check_name
records_evaluated
records_passed
records_failed
pass_percentage
evaluated_at
```

Rule-level metrics are preferred over only broad category-level metrics.

Examples:

```text
customers.email_not_null

customers.customer_id_unique

orders.customer_id_not_null

orders.product_id_not_null

orders.order_id_unique

orders.customer_reference_valid

orders.product_reference_valid
```

---

# 20. Quality Metric Validation

Metrics must be reconciled against expected seeded defects.

At minimum demonstrate detection of:

```text
50 NULL customer emails

100 NULL order customer IDs

200 NULL order product IDs

50 invalid customer references

30 invalid product references

customer duplicate condition

order duplicate condition
```

If detected counts differ from the raw injection count, explain the reason.

Do not silently change expected results until the discrepancy is understood.

---

# 21. Gold Layer Specification

Mandatory Gold tables:

```text
gold.sales_by_product
gold.revenue_by_customer
gold.customer_segmentation
```

Gold should consume analytics-eligible Silver data based on a documented quality policy.

Initial policy:

```text
quality_check_result = 'PASS'
```

This remains a project decision and may be refined before Gold implementation.

---

# 22. Gold — Sales by Product

Implementation:

```text
src/gold/01_sales_by_product.sql
```

Output grain:

> One row per product.

Required fields:

```text
product_id
product_name
category
total_orders
total_revenue
avg_order_value
```

Expected calculations:

```text
total_orders =
COUNT(DISTINCT order_id)

total_revenue =
SUM(total_amount)

avg_order_value =
AVG(total_amount)
```

Revenue status eligibility must be resolved before implementation.

---

# 23. Gold — Revenue by Customer

Implementation:

```text
src/gold/02_revenue_by_customer.sql
```

Output grain:

> One row per customer.

Required fields:

```text
customer_id
customer_name
customer_segment
total_orders
total_revenue
avg_order_value
lifetime_value_actual
```

Proposed interpretation:

```text
lifetime_value_actual =
SUM(qualifying historical order revenue)
```

Do not finalize this definition until the open business decision is explicitly resolved.

---

# 24. Gold — Customer Segmentation

Implementation:

```text
src/gold/04_customer_segmentation.sql
```

Required output:

```text
segment_type
customer_count
avg_revenue
total_revenue
```

Required segment labels:

```text
High-Value
Repeat
One-Time
Inactive
```

Each customer should belong to one intended segment.

Inactive customers must be preserved using customer-first logic such as a LEFT JOIN to order/revenue aggregates.

The High-Value threshold remains an explicit open decision.

---

# 25. Optional Gold Scope

Repository placeholder:

```text
src/gold/03_daily_weekly_trends.sql
```

Treat this as optional/stretch.

Do not implement it until:

```text
core pipeline works
tests pass
documentation is current
```

unless explicitly requested.

---

# 26. Gold Runner

Implementation:

```text
src/gold/create_gold_tables.py
```

Responsibility:

- execute/create the mandatory Gold outputs,
- fail clearly if required Silver inputs are unavailable,
- keep logic simple and understandable.

Do not introduce unnecessary orchestration frameworks.

---

# 27. Dashboard Specification

Create:

```text
src/dashboard/dashboard_queries.sql
src/dashboard/DASHBOARD_GUIDE.md
```

At least three visualizations are required.

---

## Dashboard Tile 1

Business question:

> Which products generate the most revenue?

Source:

```text
gold.sales_by_product
```

Visualization:

```text
Bar chart
```

Expected:

```text
Top 10 products by total_revenue
```

---

## Dashboard Tile 2

Business question:

> How is revenue distributed across customers?

Source:

```text
gold.revenue_by_customer
```

Visualization:

```text
Histogram
```

Field:

```text
total_revenue
```

---

## Dashboard Tile 3

Business question:

> How is the customer base distributed across the calculated segments?

Source:

```text
gold.customer_segmentation
```

Visualization:

```text
Pie chart
```

Fields:

```text
segment_type
customer_count
```

---

# 28. Dashboard Guide Specification

`DASHBOARD_GUIDE.md` should document:

- dashboard creation steps,
- SQL query used,
- source Gold table,
- visualization type,
- field mappings,
- filters if used,
- business interpretation.

Do not turn this into a large BI design exercise.

---

# 29. Database Setup Specification

Required files:

```text
database/schema.sql
database/setup-notes.md
database/seed-data-notes.md
```

`schema.sql` should provide required schema/database creation logic.

`setup-notes.md` should explain:

- environment setup,
- input file location,
- path configuration,
- table namespace,
- how to run the pipeline.

`seed-data-notes.md` should summarize:

- generated datasets,
- row counts,
- intentional quality defects,
- source file locations.

---

# 30. Error Handling Specification

Structural errors should fail clearly.

Examples:

```text
source file missing

required columns missing

source unreadable

Delta write failure
```

Data-quality defects should not crash the pipeline.

Examples:

```text
NULL customer_id

duplicate order_id

invalid product reference
```

These should be captured as Silver validation failures.

---

# 31. Testing Specification

At least one meaningful test tier is mandatory.

Testing should be created alongside implementation rather than at the end.

Minimum required validation scenarios:

```text
customer email completeness

customer key uniqueness

order customer_id completeness

order product_id completeness

order key uniqueness

customer referential integrity

product referential integrity
```

Also validate:

```text
Bronze row preservation

Silver row preservation

referential joins do not multiply orders

Gold table grain uniqueness

basic Gold aggregation correctness
```

---

# 32. Integration Validation

A meaningful integration check should validate:

```text
CSV
→ Bronze
→ Silver
→ Gold
```

Expected checks include:

- source and Bronze row counts reconcile,
- Bronze and Silver row counts reconcile,
- known defects are detected,
- quality metrics match expectations,
- Gold tables populate,
- Gold table keys are unique,
- selected aggregate values can be manually reproduced.

---

# 33. Rerun Behavior

Development execution should be predictable.

For this exercise, prefer idempotent/recreatable behavior.

Re-running a layer should not accidentally duplicate records.

The exact overwrite/create strategy should remain simple and appropriate to the environment.

---

# 34. Documentation Requirements

Required lifecycle documentation includes:

```text
README.md
candidate-info.md
tool-workflow.md
requirements-analysis.md
design-notes.md
data-model.md
data-quality-strategy.md
debugging-notes.md
reflection.md
final-ai-usage-summary.md
```

Also maintain activity-specific prompt history under:

```text
ai-prompts/
```

---

# 35. Prompt History Requirements

For meaningful AI interactions record:

```text
Prompt sent
AI response summary
What was accepted
Why it was accepted
What was changed
Why it was changed
What was rejected
Why it was rejected
How the final result was validated
```

Prompt history should show iteration.

Do not reconstruct fake AI interactions after implementation.

---

# 36. Debugging Documentation

Use:

```text
debugging-notes.md
```

for actual meaningful issues encountered.

Recommended structure:

```text
Issue
Observed behavior
Hypothesis
AI suggestion
Validation performed
Root cause
Fix
Retest result
Lesson learned
```

Do not manufacture debugging problems for appearance.

---

# 37. Responsible AI Requirements

All customer-like data must be synthetic.

Never introduce:

```text
real customer PII
passwords
tokens
API keys
private keys
production credentials
confidential customer datasets
unnecessary sensitive business data
```

The documentation should explain that real production AI usage should follow data-minimization and access-control practices.

---

# 38. Scope Constraints

Do not add the following unless explicitly requested:

```text
streaming
CDC
Auto Loader
Lakeflow Declarative Pipelines
complex Workflows
generic quality frameworks
machine learning
recommendation systems
Terraform
advanced CI/CD
production-scale optimization
complex object-oriented frameworks
```

The intended project value is in:

```text
correctness
quality thinking
testing
AI-assisted reasoning
documentation
traceability
```

not architectural complexity.

---

# 39. Open Decisions

The following decisions are intentionally unresolved.

Cursor must not silently choose them during unrelated work.

## OD-01 — Databricks Namespace

Status:

```text
OPEN
```

Need final environment details before choosing:

```text
catalog/schema naming
storage path
```

---

## OD-02 — Revenue-Eligible Status

Status:

```text
OPEN
```

Need to define which order statuses contribute to Gold revenue.

---

## OD-03 — `lifetime_value_actual`

Status:

```text
OPEN
```

Proposed direction:

```text
sum of qualifying historical order revenue
```

but final definition must follow the revenue-status decision.

---

## OD-04 — High-Value Customer Threshold

Status:

```text
OPEN
```

Preferred approach:

Inspect generated customer-revenue distribution before selecting a threshold.

Do not invent a hard-coded amount prematurely.

---

## OD-05 — Analytics Eligibility Policy

Status:

```text
OPEN / INITIAL DEFAULT AVAILABLE
```

Initial rule:

```text
quality_check_result = 'PASS'
```

Before Gold implementation, review whether failures unrelated to analytical correctness should block the affected Gold calculation.

---

## OD-06 — Duplicate Physical Row Strategy

Status:

```text
TO BE FINALIZED DURING DATA GENERATION
```

Need to explicitly document whether duplicate defects:

- increase physical CSV row counts, or
- reuse IDs within fixed physical row counts.

The chosen implementation must remain consistent with tests and documentation.

---

# 40. Implementation Checkpoints

The system must be built incrementally.

## Checkpoint 1 — Planning

Deliver:

```text
requirements-analysis.md
design-notes.md
data-quality-strategy.md
data-model.md
project-context.md
spec.md
cursor-rules-or-instructions.md
task-breakdown.md
```

No pipeline implementation should be produced during this checkpoint.

---

## Checkpoint 2 — Data Generation

Deliver:

```text
generate_sample_data.py
customers.csv
orders.csv
products.csv
DATA_GENERATION_NOTES.md
data-generation prompt history
validation evidence
```

Do not begin Bronze until data-generation validation passes.

---

## Checkpoint 3 — Bronze

Deliver:

```text
three Bronze ingestion scripts
ingest_all.py
Bronze Delta tables
row-count validation
source preservation checks
Bronze prompt history
```

Do not begin Silver until Bronze is validated.

---

## Checkpoint 4 — Silver

Deliver:

```text
five quality categories
Silver tables
quality_check_result
quality_failure_reasons
quality metrics
quality tests
Silver prompt history
```

Do not begin Gold until seeded defects are correctly detected and metrics reconcile.

---

## Checkpoint 5 — Gold

Deliver:

```text
sales_by_product
revenue_by_customer
customer_segmentation
Gold runner
aggregation validation
Gold prompt history
```

Do not begin dashboard work until core Gold calculations are validated.

---

## Checkpoint 6 — Dashboard

Deliver:

```text
dashboard_queries.sql
3+ required visualizations
DASHBOARD_GUIDE.md
dashboard validation
dashboard prompt history
```

---

## Checkpoint 7 — Final Validation and Documentation

Deliver/finalize:

```text
end-to-end test
README
tool-workflow.md
debugging-notes.md
reflection.md
final-ai-usage-summary.md
prompt-history review
repository completeness review
```

---

# 41. Checkpoint Gate Rule

Before moving from one checkpoint to the next:

```text
implement
→ run
→ inspect
→ validate
→ correct
→ document
→ commit
→ proceed
```

Do not treat generated code as accepted merely because it compiles or appears reasonable.

---

# 42. Definition of Done

The project is complete when:

- [ ] Three synthetic CSV datasets exist.
- [ ] Required intentional quality issues exist and are documented.
- [ ] Bronze successfully ingests and preserves all source rows.
- [ ] Silver implements required quality validations.
- [ ] Invalid rows remain available and are flagged.
- [ ] Quality metrics report passed/failed results.
- [ ] Tests demonstrate that seeded quality issues are caught.
- [ ] Three mandatory Gold aggregations exist.
- [ ] Gold calculations have been validated.
- [ ] Dashboard contains at least three required visualizations.
- [ ] Database setup scripts and notes exist.
- [ ] README can guide a reviewer through the project.
- [ ] AI prompt history shows real iterative usage.
- [ ] Actual debugging/validation evidence is documented.
- [ ] Responsible AI considerations are documented.
- [ ] Reflection explains what worked, what did not, and what could improve.
- [ ] The final implementation remains understandable and appropriately scoped.