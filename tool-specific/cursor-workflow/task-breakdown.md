# Cursor Task Breakdown

## 1. Purpose

This file defines the implementation sequence for the Databricks Medallion Pipeline AI Capability Exercise.

Cursor should use this breakdown together with:

```text
requirements-analysis.md
design-notes.md
data-model.md
data-quality-strategy.md
tool-specific/cursor-workflow/project-context.md
tool-specific/cursor-workflow/spec.md
tool-specific/cursor-workflow/cursor-rules-or-instructions.md
```

The goal is to:

- keep implementation incremental,
- prevent scope creep,
- make validation gates explicit,
- support meaningful prompt history,
- ensure each checkpoint is accepted before the next begins.

The expected working pattern is:

```text
Read context
→ implement one task
→ review
→ run
→ validate
→ fix if required
→ document
→ commit
→ proceed
```

Cursor must not automatically continue into the next checkpoint.

---

# 2. Checkpoint Overview

The project is divided into seven checkpoints.

```text
Checkpoint 1 — Planning & Cursor Context
Checkpoint 2 — Synthetic Data Generation
Checkpoint 3 — Bronze Layer
Checkpoint 4 — Silver Layer + Quality Metrics + Tests
Checkpoint 5 — Gold Layer
Checkpoint 6 — Dashboard
Checkpoint 7 — Final Validation + Documentation + Reflection
```

Each checkpoint has:

- objectives,
- tasks,
- allowed files,
- validation requirements,
- completion gate.

---

# 3. Checkpoint 1 — Planning & Cursor Context

## Objective

Create a complete planning package before implementation begins.

The planning package should allow Cursor to understand:

- the business problem,
- the technical requirements,
- the data model,
- the quality rules,
- architecture decisions,
- open decisions,
- implementation boundaries,
- project checkpoints.

## Tasks

### Task 1.1 — Requirements Analysis

Create/finalize:

```text
requirements-analysis.md
```

Must include:

- problem statement,
- functional requirements,
- non-functional requirements,
- assumptions,
- edge cases,
- clarifications needed,
- acceptance criteria.

---

### Task 1.2 — Design Notes

Create/finalize:

```text
design-notes.md
```

Must cover:

- Medallion architecture,
- layer responsibilities,
- data-generation approach,
- Bronze behavior,
- Silver validation design,
- Gold design,
- dashboard design,
- testing,
- debugging,
- configuration,
- deferred decisions.

---

### Task 1.3 — Data Quality Strategy

Create/finalize:

```text
data-quality-strategy.md
```

Must cover:

- completeness,
- uniqueness,
- type validation,
- referential integrity,
- business logic,
- quality metadata,
- expected seeded defects,
- quality metrics,
- testing strategy,
- Gold eligibility implications.

---

### Task 1.4 — Data Model

Create/finalize:

```text
data-model.md
```

Must define:

- source schemas,
- grains,
- keys,
- foreign-key relationships,
- Bronze tables,
- Silver tables,
- quality metrics table,
- Gold tables,
- dashboard data sources,
- open modeling decisions.

---

### Task 1.5 — Cursor Project Context

Create:

```text
tool-specific/cursor-workflow/project-context.md
```

Purpose:

Provide persistent context that Cursor can read before implementation tasks.

---

### Task 1.6 — Cursor Specification

Create:

```text
tool-specific/cursor-workflow/spec.md
```

Purpose:

Define the implementation-facing contract and overall definition of done.

---

### Task 1.7 — Cursor Rules

Create:

```text
tool-specific/cursor-workflow/cursor-rules-or-instructions.md
```

Purpose:

Define the rules Cursor must follow while editing the repository.

---

### Task 1.8 — Task Breakdown

Create:

```text
tool-specific/cursor-workflow/task-breakdown.md
```

This file.

---

### Task 1.9 — Candidate Information

Create/finalize:

```text
candidate-info.md
```

Include:

- candidate name,
- role,
- primary stack,
- primary AI tool,
- selected project option,
- Databricks environment,
- start date,
- submission date when known.

---

### Task 1.10 — Repository Scaffold

Ensure required directories and placeholder files exist.

No pipeline implementation should be generated during this task.

---

## Checkpoint 1 Validation Gate

Before Checkpoint 2 begins:

- [ ] Requirements are documented.
- [ ] Architecture is documented.
- [ ] Data model is documented.
- [ ] Data quality strategy is documented.
- [ ] Cursor project context exists.
- [ ] Cursor spec exists.
- [ ] Cursor rules exist.
- [ ] Cursor task breakdown exists.
- [ ] Candidate information exists.
- [ ] Repository structure matches the agreed scaffold.
- [ ] Open decisions are explicitly visible.
- [ ] No pipeline implementation has started accidentally.

---

# 4. Checkpoint 2 — Synthetic Data Generation

## Objective

Generate reproducible synthetic source data containing the exact intentional quality conditions required by the exercise.

## Allowed Primary Files

```text
src/data_generation/generate_sample_data.py
src/data_generation/DATA_GENERATION_NOTES.md

data/customers.csv
data/orders.csv
data/products.csv

ai-prompts/data-generation.md
database/seed-data-notes.md
```

Avoid modifying Bronze, Silver, Gold, or dashboard implementation during this checkpoint.

---

## Task 2.1 — Review Source Data Contracts

Before generating code, read:

```text
requirements-analysis.md
data-model.md
data-quality-strategy.md
```

Confirm:

- customer schema,
- order schema,
- product schema,
- logical row counts,
- intentional defect counts.

---

## Task 2.2 — Decide Duplicate Physical-Row Strategy

Resolve the open decision:

Will duplicate defects:

### Option A

append additional physical rows,

or

### Option B

reuse existing IDs while keeping fixed physical row counts?

Document the selected approach before final generation.

The generator, notes, tests, and Bronze row-count expectations must use the same interpretation.

---

## Task 2.3 — Implement Reproducible Random Generation

Use deterministic seeds for:

- Python random,
- Faker,
- NumPy if used.

The same run should produce stable data for validation and debugging.

---

## Task 2.4 — Generate Products Baseline

Generate approximately:

```text
500 products
```

Validate:

- product IDs unique,
- no unexpected NULLs,
- non-negative numeric values,
- realistic categories and names.

---

## Task 2.5 — Generate Customers Baseline

Generate approximately:

```text
10,000 logical customers
```

Validate before corruption:

- valid IDs,
- valid segment values,
- realistic synthetic names/emails,
- valid dates,
- non-negative lifetime value.

---

## Task 2.6 — Inject Customer Defects

Inject:

```text
50 NULL email rows
10 duplicate customer_id records
```

Keep intentional defect selection controlled and reproducible.

---

## Task 2.7 — Generate Orders Baseline

Generate approximately:

```text
100,000 logical orders
```

Initially generate valid references to:

```text
customers.customer_id
products.product_id
```

Validate:

- valid order IDs,
- valid foreign keys,
- quantity > 0,
- valid status,
- reasonable dates,
- valid amounts.

---

## Task 2.8 — Inject Order Defects

Inject:

```text
100 NULL customer_id rows
200 NULL product_id rows
50 invalid customer_id references
30 invalid product_id references
20 duplicate order_id records
```

Where practical, keep issue groups non-overlapping.

---

## Task 2.9 — Validate Generated Defect Counts

Before writing CSV output, assert the required conditions exist.

Do not rely only on visual inspection.

---

## Task 2.10 — Write CSV Files

Write:

```text
data/customers.csv
data/orders.csv
data/products.csv
```

---

## Task 2.11 — Inspect Output

Check:

- physical row counts,
- headers,
- sample records,
- NULL values,
- duplicate-key groups,
- orphan references,
- data types/formats.

---

## Task 2.12 — Document Generation

Update:

```text
src/data_generation/DATA_GENERATION_NOTES.md
```

Document:

- generation approach,
- Faker usage,
- seed values,
- dependency order,
- duplicate strategy,
- intentional defects,
- issue validation.

---

## Task 2.13 — Record Prompt History

Update:

```text
ai-prompts/data-generation.md
```

Capture meaningful iterations.

---

## Checkpoint 2 Validation Gate

Before Bronze begins:

- [ ] All three CSVs exist.
- [ ] Required columns exist.
- [ ] Row-count interpretation is documented.
- [ ] 50 NULL customer emails confirmed.
- [ ] Customer duplicate condition confirmed.
- [ ] 100 NULL order customer IDs confirmed.
- [ ] 200 NULL order product IDs confirmed.
- [ ] 50 customer orphans confirmed.
- [ ] 30 product orphans confirmed.
- [ ] Order duplicate condition confirmed.
- [ ] No real PII exists.
- [ ] Generation notes are complete.
- [ ] Prompt history is recorded.

Stop after validation.

---

# 5. Checkpoint 3 — Bronze Layer

## Objective

Ingest the three source CSV files into Databricks as raw Delta tables while preserving source records and intentional quality issues.

## Primary Files

```text
src/bronze/01_ingest_customers.py
src/bronze/02_ingest_orders.py
src/bronze/03_ingest_products.py
src/bronze/ingest_all.py

database/schema.sql
database/setup-notes.md

ai-prompts/bronze-layer.md
```

---

## Task 3.1 — Confirm Databricks Environment

Before implementation, establish:

- source file location,
- available catalog/schema support,
- target table namespace,
- SQL Warehouse availability if relevant,
- storage path behavior.

Do not assume unsupported platform features.

---

## Task 3.2 — Create Database/Schema Setup

Update:

```text
database/schema.sql
```

Create the required logical namespaces for:

```text
Bronze
Silver
Gold
```

or the simplest compatible alternative.

---

## Task 3.3 — Centralize Environment Values

Define a lightweight approach for:

- source base path,
- catalog if applicable,
- Bronze schema,
- Silver schema,
- Gold schema.

Do not build a complex configuration framework.

---

## Task 3.4 — Implement Customer Ingestion

Create:

```text
src/bronze/01_ingest_customers.py
```

Responsibilities:

- validate input exists,
- read CSV,
- preserve business values,
- add `_ingested_at`,
- persist Delta,
- report row count.

No cleaning.

---

## Task 3.5 — Validate Customer Bronze

Verify:

```text
source row count = Bronze row count
```

Confirm:

- NULL emails preserved,
- duplicate customer IDs preserved.

---

## Task 3.6 — Implement Order Ingestion

Create:

```text
src/bronze/02_ingest_orders.py
```

No quality corrections.

---

## Task 3.7 — Validate Order Bronze

Confirm:

- source count matches,
- NULL foreign keys preserved,
- orphan foreign keys preserved,
- duplicate order IDs preserved.

---

## Task 3.8 — Implement Product Ingestion

Create:

```text
src/bronze/03_ingest_products.py
```

Validate row count and inferred schema.

---

## Task 3.9 — Implement Bronze Runner

Create:

```text
src/bronze/ingest_all.py
```

Run all Bronze ingestion tasks in a predictable sequence.

---

## Task 3.10 — Test Rerun Behavior

Run ingestion more than once.

Ensure data is not accidentally duplicated.

---

## Task 3.11 — Test Structural Failure

Test at least one failure condition such as:

```text
missing source path
```

Ensure the pipeline fails clearly.

---

## Task 3.12 — Record Prompt History

Update:

```text
ai-prompts/bronze-layer.md
```

---

## Checkpoint 3 Validation Gate

Before Silver begins:

- [ ] Three Bronze tables exist.
- [ ] Bronze uses Delta.
- [ ] Source rows are preserved.
- [ ] Intentional quality defects remain.
- [ ] Ingestion timestamps exist.
- [ ] Row counts reconcile.
- [ ] Rerunning does not duplicate data.
- [ ] Structural errors fail clearly.
- [ ] Bronze prompt history is recorded.

Stop after validation.

---

# 6. Checkpoint 4 — Silver Layer, Quality Metrics and Tests

## Objective

Build Silver datasets that retain Bronze rows while adding quality validation results and measurable quality metrics.

## Primary Files

```text
src/silver/01_quality_completeness.py
src/silver/02_quality_uniqueness.py
src/silver/03_quality_type_validation.py
src/silver/04_quality_referential_integrity.py
src/silver/05_quality_business_logic.py
src/silver/create_silver_tables.py

ai-prompts/silver-layer.md
```

Testing files may be added if a dedicated test structure is selected.

---

# 7. Silver Task Group A — Completeness

## Task 4.1 — Implement Completeness

Create:

```text
src/silver/01_quality_completeness.py
```

At minimum validate:

### Customers

```text
email
```

### Orders

```text
customer_id
product_id
```

Do not fail NULL `payment_date`.

---

## Task 4.2 — Validate Completeness Counts

Expected:

```text
50 NULL customer emails
100 NULL order customer_id
200 NULL order product_id
```

Inspect representative failure rows.

---

# 8. Silver Task Group B — Uniqueness

## Task 4.3 — Implement Uniqueness

Create:

```text
src/silver/02_quality_uniqueness.py
```

Validate:

```text
customers.customer_id
orders.order_id
products.product_id
```

Do not remove duplicates.

---

## Task 4.4 — Validate Duplicate Semantics

Compare:

```text
duplicate rows injected
```

against:

```text
rows participating in duplicate groups
```

Document the reason if counts differ.

---

# 9. Silver Task Group C — Type Validation

## Task 4.5 — Inspect Bronze Schemas First

Inspect how Databricks inferred:

- dates,
- integers,
- decimals.

Do not implement type validation blindly.

---

## Task 4.6 — Implement Type Validation

Create:

```text
src/silver/03_quality_type_validation.py
```

Keep logic proportionate to the exercise.

Do not build a generic schema-validation library.

---

# 10. Silver Task Group D — Referential Integrity

## Task 4.7 — Implement Referential Integrity

Create:

```text
src/silver/04_quality_referential_integrity.py
```

Validate non-null:

```text
orders.customer_id
orders.product_id
```

against parent entities.

---

## Task 4.8 — Protect Order Cardinality

Use distinct parent keys or equivalent existence validation.

Verify the customer duplicates do not multiply Orders.

---

## Task 4.9 — Validate Orphan Counts

Expected:

```text
50 invalid customer references
30 invalid product references
```

Do not count NULL foreign keys as orphans.

---

# 11. Silver Task Group E — Business Logic

## Task 4.10 — Implement Business Checks

Create:

```text
src/silver/05_quality_business_logic.py
```

Use only approved rules.

Potential rules:

### Customers

```text
valid customer_segment
lifetime_value >= 0
signup_date <= current_date()
```

### Orders

```text
quantity > 0
unit_price >= 0
total_amount >= 0
valid order_status
```

### Products

```text
price >= 0
cost >= 0
stock_quantity >= 0
reorder_level >= 0
```

---

## Task 4.11 — Validate No Legitimate Rows Are Incorrectly Rejected

Inspect results before accepting the rule set.

---

# 12. Silver Task Group F — Final Silver Tables

## Task 4.12 — Combine Quality Results

Create:

```text
src/silver/create_silver_tables.py
```

Recommended metadata:

```text
completeness_pass
uniqueness_pass
type_validation_pass
referential_integrity_pass
business_logic_pass
quality_check_result
quality_failure_reasons
```

---

## Task 4.13 — Persist Silver Tables

Create:

```text
silver.customers
silver.orders
silver.products
```

---

## Task 4.14 — Verify Row Preservation

Expected:

```text
Bronze count = Silver count
```

for each dataset.

Any mismatch must be investigated.

---

## Task 4.15 — Inspect Multi-Failure Rows

Ensure multiple failure reasons can coexist correctly.

---

# 13. Silver Task Group G — Quality Metrics

## Task 4.16 — Create Quality Metrics

Recommended table:

```text
silver.quality_metrics
```

Required measures:

```text
records_evaluated
records_passed
records_failed
pass_percentage
```

---

## Task 4.17 — Prefer Rule-Level Metrics

At minimum report useful metrics such as:

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

## Task 4.18 — Reconcile Metrics

Compare actual metrics against known seeded issues.

If results differ, investigate before accepting.

---

# 14. Silver Task Group H — Tests

## Task 4.19 — Implement Data Quality Tests

Verify that the deliberately introduced problems are detected.

Required scenarios:

```text
NULL customer email
duplicate customer ID
NULL order customer ID
NULL order product ID
invalid customer reference
invalid product reference
duplicate order ID
```

---

## Task 4.20 — Implement Row Preservation Test

Verify:

```text
Bronze counts = Silver counts
```

---

## Task 4.21 — Test Referential Join Stability

Verify one Bronze order corresponds to one Silver order.

No join-induced multiplication.

---

## Task 4.22 — Test Overall Quality Result

Rows failing any applicable configured check should receive appropriate failure metadata.

---

## Task 4.23 — Record Silver Prompt History

Update:

```text
ai-prompts/silver-layer.md
```

---

## Checkpoint 4 Validation Gate

Before Gold begins:

- [ ] Completeness works.
- [ ] Uniqueness works.
- [ ] Type validation works.
- [ ] Referential integrity works.
- [ ] Business logic works.
- [ ] Bad rows are retained.
- [ ] Failure reasons are visible.
- [ ] Silver counts reconcile with Bronze.
- [ ] RI joins do not multiply rows.
- [ ] Quality metrics exist.
- [ ] Seeded defects reconcile with metrics.
- [ ] Data quality tests pass.
- [ ] Prompt history is recorded.

Stop after validation.

---

# 15. Checkpoint 5 — Gold Layer

## Objective

Create business-ready analytical tables from trusted Silver data.

## Primary Files

```text
src/gold/01_sales_by_product.sql
src/gold/02_revenue_by_customer.sql
src/gold/03_daily_weekly_trends.sql
src/gold/04_customer_segmentation.sql
src/gold/create_gold_tables.py

ai-prompts/gold-layer.md
```

---

# 16. Gold Pre-Implementation Decisions

## Task 5.1 — Resolve Revenue Eligibility

Decide which order statuses count as revenue.

Do not implement Gold revenue until this decision is documented.

---

## Task 5.2 — Resolve `lifetime_value_actual`

Define exact calculation.

Document the relationship between:

```text
customers.lifetime_value
```

and:

```text
lifetime_value_actual
```

---

## Task 5.3 — Resolve High-Value Threshold

Inspect revenue distribution.

Choose and document a deterministic threshold.

Avoid arbitrary rules if a data-driven rule is more defensible.

---

## Task 5.4 — Resolve Gold Analytics Eligibility

Review whether the current default:

```text
quality_check_result = 'PASS'
```

should apply to every Gold use case.

Document the final decision.

---

# 17. Gold Sales by Product

## Task 5.5 — Implement Sales by Product

Create:

```text
src/gold/01_sales_by_product.sql
```

Required fields:

```text
product_id
product_name
category
total_orders
total_revenue
avg_order_value
```

---

## Task 5.6 — Validate Product Aggregations

Manually inspect selected product totals against Silver orders.

Verify table grain:

```text
one row per product_id
```

---

# 18. Gold Revenue by Customer

## Task 5.7 — Implement Revenue by Customer

Create:

```text
src/gold/02_revenue_by_customer.sql
```

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

---

## Task 5.8 — Preserve Customers Needed for Segmentation

Ensure the modeling approach can represent customers with no qualifying orders.

---

## Task 5.9 — Validate Sample Customers

Manually recalculate selected customers.

Verify:

```text
one row per customer_id
```

---

# 19. Gold Customer Segmentation

## Task 5.10 — Implement Customer Segmentation

Create:

```text
src/gold/04_customer_segmentation.sql
```

Required labels:

```text
High-Value
Repeat
One-Time
Inactive
```

---

## Task 5.11 — Validate Segment Exclusivity

Each eligible customer should belong to one intended segment.

---

## Task 5.12 — Validate Inactive Customers

Ensure customers with no qualifying orders can appear in:

```text
Inactive
```

---

## Task 5.13 — Validate Segment Population

Check:

```text
SUM(customer_count)
```

against the expected segmentation population.

---

# 20. Gold Runner

## Task 5.14 — Implement Gold Runner

Create:

```text
src/gold/create_gold_tables.py
```

Keep orchestration simple.

---

## Task 5.15 — Validate Full Gold Refresh

Run Gold from validated Silver tables.

Confirm all mandatory outputs populate correctly.

---

## Task 5.16 — Record Gold Prompt History

Update:

```text
ai-prompts/gold-layer.md
```

---

## Checkpoint 5 Validation Gate

Before dashboard work:

- [ ] Revenue business rule documented.
- [ ] `lifetime_value_actual` documented.
- [ ] High-Value threshold documented.
- [ ] Analytics eligibility documented.
- [ ] Sales by Product exists.
- [ ] Revenue by Customer exists.
- [ ] Daily/Weekly Sales Trends exists.
- [ ] Customer Segmentation exists.
- [ ] Gold grains are unique.
- [ ] Aggregations have been manually spot-checked.
- [ ] Inactive customers are represented correctly.
- [ ] Gold prompt history is recorded.

Stop after validation.

---

# 21. Checkpoint 6 — Dashboard

## Objective

Create three required stakeholder visualizations using business-ready Gold data.

## Primary Files

```text
src/dashboard/dashboard_queries.sql
src/dashboard/DASHBOARD_GUIDE.md

ai-prompts/dashboard.md
```

---

## Task 6.1 — Write Top Products Query

Create SQL for:

```text
Top 10 products by revenue
```

Visualization:

```text
Bar chart
```

Source:

```text
gold.sales_by_product
```

---

## Task 6.2 — Write Revenue Distribution Query

Create SQL suitable for:

```text
Customer revenue distribution
```

Visualization:

```text
Histogram
```

Source:

```text
gold.revenue_by_customer
```

---

## Task 6.3 — Write Customer Segmentation Query

Create SQL for:

```text
Customer segmentation
```

Visualization:

```text
Pie chart
```

Source:

```text
gold.customer_segmentation
```

---

## Task 6.4 — Validate Queries Independently

Run each SQL query before creating charts.

---

## Task 6.5 — Build Dashboard

Configure the three visualizations in Databricks SQL.

Add simple useful filters only if they improve the required dashboard.

---

## Task 6.6 — Validate Dashboard Values

Compare dashboard outputs against Gold tables.

---

## Task 6.7 — Document Dashboard Setup

Create:

```text
src/dashboard/DASHBOARD_GUIDE.md
```

Document:

- query source,
- visualization type,
- field mappings,
- filters,
- business interpretation.

---

## Task 6.8 — Record Prompt History

Update:

```text
ai-prompts/dashboard.md
```

---

## Checkpoint 6 Validation Gate

Before finalization:

- [ ] Top 10 bar chart exists.
- [ ] Customer revenue histogram exists.
- [ ] Customer segmentation pie chart exists.
- [ ] Queries run successfully.
- [ ] Values reconcile with Gold.
- [ ] Dashboard guide exists.
- [ ] Prompt history is recorded.

---

# 22. Checkpoint 7 — Final Validation and Documentation

## Objective

Prove the project works end-to-end and complete the lifecycle documentation required for submission.

---

# 23. End-to-End Validation

## Task 7.1 — Perform Clean Pipeline Run

Execute:

```text
Generate data
→ Bronze
→ Silver
→ Quality metrics
→ Gold
→ Dashboard queries
```

---

## Task 7.2 — Reconcile Counts Across Layers

Validate:

```text
Source → Bronze
Bronze → Silver
```

---

## Task 7.3 — Reconcile Quality Results

Compare final metrics against intentional seeded defects.

---

## Task 7.4 — Validate Gold Again

Perform final aggregation spot checks.

---

## Task 7.5 — Validate Rerun Behavior

Run relevant layers again and ensure results do not duplicate unexpectedly.

---

# 24. Debugging Documentation

## Task 7.6 — Finalize Debugging Notes

File:

```text
debugging-notes.md
```

Document actual meaningful problems encountered.

For each issue include:

```text
Problem
Observed behavior
Hypothesis
AI suggestion
Validation
Root cause
Fix
Retest result
Lesson learned
```

---

## Task 7.7 — Finalize Debugging Prompt History

Update:

```text
ai-prompts/debugging.md
```

Do not fabricate debugging interactions.

---

# 25. README

## Task 7.8 — Finalize README

Create/update:

```text
README.md
```

Include:

- project overview,
- architecture,
- prerequisites,
- repository structure,
- setup,
- data generation,
- Bronze execution,
- Silver execution,
- Gold execution,
- dashboard setup,
- testing,
- expected quality issues,
- assumptions,
- known limitations.

Validate instructions from a clean perspective.

---

# 26. AI Workflow Documentation

## Task 7.9 — Finalize `tool-workflow.md`

Describe actual AI usage across:

```text
context setting
requirements
design
coding
validation
testing
debugging
data quality
documentation
reflection
```

Also document responsible AI practices and information that should not be shared unnecessarily in real production scenarios.

---

# 27. Prompt History Review

## Task 7.10 — Review All Prompt Files

Required:

```text
ai-prompts/data-generation.md
ai-prompts/bronze-layer.md
ai-prompts/silver-layer.md
ai-prompts/gold-layer.md
ai-prompts/dashboard.md
ai-prompts/debugging.md
ai-prompts/documentation.md
```

For meaningful prompts ensure they show:

```text
prompt
response summary
accepted
changed
rejected
reason
validation
```

---

# 28. Reflection

## Task 7.11 — Create Reflection

File:

```text
reflection.md
```

Cover:

- what was built,
- how AI was used,
- where AI helped,
- where AI was wrong/incomplete,
- how output was validated,
- what could improve,
- reusable workflow.

Use real examples from the project.

---

# 29. Final AI Usage Summary

## Task 7.12 — Create Final Summary

File:

```text
final-ai-usage-summary.md
```

Summarize:

- primary AI tool,
- major AI-assisted activities,
- important decisions,
- validation approach,
- examples of corrections/rejections,
- responsible AI practices,
- lessons learned.

---

# 30. Documentation Consistency Review

## Task 7.13 — Cross-Check Documents

Verify consistent terminology for:

```text
table names
quality rule names
Gold business rules
segment labels
revenue definition
lifetime_value_actual
```

Resolve contradictions.

---

# 31. Repository Completeness Review

## Task 7.14 — Compare Against Required Structure

Check every required repository artifact.

Do not rely on memory.

---

# 32. Code Review

## Task 7.15 — Perform Final Cursor-Assisted Code Review

Ask Cursor to identify:

- correctness risks,
- unclear logic,
- unnecessary duplication,
- hard-coded values,
- weak error handling,
- missing validation,
- scope creep.

Do not automatically accept all recommended refactors.

Evaluate each suggestion.

---

# 33. Final Submission Gate

The project is ready when:

- [ ] Working end-to-end pipeline exists.
- [ ] Synthetic source data exists.
- [ ] Required quality issues are present.
- [ ] Bronze ingestion works.
- [ ] Silver validations work.
- [ ] Quality metrics work.
- [ ] Quality tests demonstrate seeded problems are detected.
- [ ] Four Gold outputs work, including Daily/Weekly Sales Trends.
- [ ] Three dashboard visualizations exist.
- [ ] Setup/database files exist.
- [ ] README works.
- [ ] Prompt history is complete.
- [ ] Requirement/design/quality documentation is complete.
- [ ] Debugging notes contain real evidence.
- [ ] Reflection is complete.
- [ ] Final AI usage summary is complete.
- [ ] Responsible AI considerations are documented.
- [ ] Repository has been reviewed for consistency.
- [ ] Final end-to-end run has been completed successfully.

---

# 34. Implemented Gold Extension

The daily/weekly sales trends output is implemented in:

```text
src/gold/03_daily_weekly_trends.sql
```

It creates:

```text
ecommerce_sales.gold.daily_weekly_trends
```

The output contains daily and Monday-based weekly aggregations of qualifying
completed Silver orders and is validated as part of the Gold runner.

---

# 35. Cursor Execution Rule

For every implementation prompt, Cursor should be given:

```text
1. Active checkpoint
2. Exact task
3. Relevant source-of-truth files
4. Files allowed to change
5. Expected output
6. Validation requirements
7. Explicit stop condition
```

Example pattern:

```text
Active checkpoint: Checkpoint 2 — Data Generation

Read:
- requirements-analysis.md
- data-model.md
- data-quality-strategy.md
- project-context.md
- spec.md
- cursor-rules-or-instructions.md

Task:
Implement only the synthetic data generator.

Allowed files:
- src/data_generation/generate_sample_data.py
- src/data_generation/DATA_GENERATION_NOTES.md

Do not:
- create Bronze/Silver/Gold code
- make unrelated changes

After implementation:
- explain important decisions
- provide validation steps
- identify assumptions
- stop
```

This pattern should be reused throughout the project.