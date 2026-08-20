# Cursor Project Context

## 1. Project Overview

This repository implements an AI-assisted Databricks Medallion Architecture pipeline for a synthetic e-commerce sales use case.

The pipeline processes three source datasets:

- customers
- orders
- products

The required flow is:

```text
Synthetic CSVs
    ↓
Bronze
    ↓
Silver
    ↓
Gold
    ↓
Databricks SQL Dashboard
```

The project is part of an AI capability exercise focused not only on whether the pipeline works, but also on how AI is used across:

- requirement analysis,
- design,
- implementation,
- validation,
- testing,
- debugging,
- documentation,
- reflection.

The implementation must therefore remain understandable, testable, and easy to explain.

---

# 2. Authoritative Project Documents

Before making any non-trivial implementation change, read and follow these files:

```text
requirements-analysis.md
design-notes.md
data-model.md
data-quality-strategy.md
```

These documents define the current approved requirements and design.

If this file conflicts with one of those documents, use the more specific approved design document and surface the conflict rather than silently choosing an interpretation.

Do not invent new business requirements.

---

# 3. Core Business Problem

An e-commerce company ingests daily sales data into Databricks from CSV files representing:

- customers,
- orders,
- products.

The solution must provide:

### Bronze

Raw ingestion with no business cleaning.

### Silver

Data-quality validation with bad rows retained and flagged.

### Gold

Business-ready aggregations.

### Dashboard

At least three Databricks SQL visualizations for stakeholders.

---

# 4. Source Datasets

## Customers

Approximate logical size:

```text
10,000 customers
```

Fields:

```text
customer_id
customer_name
email
country
signup_date
customer_segment
lifetime_value
```

Required customer segments:

```text
Premium
Standard
Basic
```

Intentional quality issues:

```text
50 NULL email rows
10 duplicate customer_id records
```

---

## Orders

Approximate logical size:

```text
100,000 orders
```

Fields:

```text
order_id
customer_id
order_date
product_id
quantity
unit_price
total_amount
order_status
payment_date
```

Required statuses:

```text
Pending
Completed
Cancelled
```

Intentional quality issues:

```text
100 NULL customer_id rows
200 NULL product_id rows
50 invalid customer_id references
30 invalid product_id references
20 duplicate order_id records
```

---

## Products

Approximate size:

```text
500 products
```

Fields:

```text
product_id
product_name
category
price
cost
stock_quantity
reorder_level
```

No mandatory intentional product defects are required.

---

# 5. Technology Stack

Primary technologies:

```text
Python
PySpark
SQL
Databricks
Delta Lake
pandas
Faker
```

Use:

```text
pandas + Faker
```

for synthetic data generation unless there is a strong reason otherwise.

Use:

```text
PySpark
```

for Databricks pipeline processing.

Use:

```text
SQL
```

for Gold aggregations and dashboard queries where specified.

Do not add libraries without a clear requirement.

---

# 6. Bronze Rules

Bronze represents what arrived from the source.

Bronze must:

- read the CSV input,
- preserve every physical source row,
- preserve intentional quality issues,
- infer or apply source-compatible schema,
- persist as Delta,
- record ingestion timestamp,
- log/record row count.

Bronze must NOT:

- drop duplicates,
- replace NULL values,
- fix foreign keys,
- filter invalid rows,
- apply business rules,
- perform data-quality cleaning.

Allowed operational metadata includes:

```text
_ingested_at
```

and optionally:

```text
_source_file
```

---

# 7. Silver Rules

Silver is the validation layer.

Silver must retain bad records rather than delete them.

The required validation categories are:

```text
Completeness
Uniqueness
Referential Integrity
```

The project also includes:

```text
Type Validation
Business Logic Validation
```

as additional validation depth.

Recommended row-level metadata:

```text
completeness_pass
uniqueness_pass
type_validation_pass
referential_integrity_pass
business_logic_pass
quality_check_result
quality_failure_reasons
```

The final quality result should be understandable from the row itself.

Do not return only a generic FAIL value if the failure reason can be captured simply.

---

# 8. Completeness Rules

At minimum:

## Customers

```text
email IS NOT NULL
```

## Orders

```text
customer_id IS NOT NULL
product_id IS NOT NULL
```

`payment_date` is legitimately nullable and must not fail completeness solely because it is NULL.

---

# 9. Uniqueness Rules

Validate intended primary keys:

```text
customers.customer_id
orders.order_id
products.product_id
```

Do not remove duplicate rows.

Flag rows participating in duplicate-key groups.

Be careful when reporting duplicate counts:

```text
duplicates introduced
```

and:

```text
rows participating in duplicate groups
```

may not be the same number.

---

# 10. Referential Integrity Rules

Validate Orders against parent entities.

```text
orders.customer_id → customers.customer_id
orders.product_id  → products.product_id
```

Only non-null foreign keys should be tested for orphan references.

A NULL foreign key is primarily a completeness failure.

Use distinct parent identifiers for existence checks.

This is important because the customers source intentionally contains duplicate customer IDs.

Do not write referential joins that multiply order rows.

---

# 11. Business Logic Rules

Keep business validation modest and explainable.

Candidate customer rules:

```text
customer_segment in Premium / Standard / Basic
lifetime_value >= 0
signup_date <= current_date()
```

Candidate order rules:

```text
quantity > 0
unit_price >= 0
total_amount >= 0
order_status in Pending / Completed / Cancelled
```

Candidate product rules:

```text
price >= 0
cost >= 0
stock_quantity >= 0
reorder_level >= 0
```

Do not introduce additional business rules unless supported by:

- project documentation,
- generated data contract,
- an explicit user decision.

---

# 12. Quality Metrics

The solution must produce measurable quality results.

Recommended output:

```text
silver.quality_metrics
```

Suggested fields:

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

Prefer rule-level metrics where practical.

Known seeded issues should be reconcilable against reported results.

---

# 13. Silver Preservation Contract

Silver annotates rather than filters.

Expected integration behavior:

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

unless a structural pipeline error prevents processing.

---

# 14. Gold Outputs

The mandatory Gold outputs are:

```text
gold.sales_by_product
gold.revenue_by_customer
gold.customer_segmentation
gold.daily_weekly_trends
```

---

## Sales by Product

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

## Revenue by Customer

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

## Customer Segmentation

Required fields:

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

---

## Daily/Weekly Sales Trends

Required fields:

```text
period_type
period_start
total_orders
total_revenue
avg_order_value
```

The implemented table uses qualifying completed Silver orders and provides one
row per daily or Monday-based weekly period.

---

# 15. Open Gold Decisions

Do not invent answers for the following open items.

These must be resolved before implementation of the affected Gold logic.

## Open Decision 1

Which order statuses contribute to revenue?

## Open Decision 2

Exact definition of:

```text
lifetime_value_actual
```

## Open Decision 3

Exact High-Value customer threshold.

## Open Decision 4

Whether all Silver failures block Gold eligibility or whether some non-analytical failures may still be usable.

If a requested task depends on one of these decisions and it remains unresolved, surface the dependency before implementing that logic.

---

# 16. Customer Segmentation Design Constraint

Inactive customers must not disappear.

Do not derive segmentation only from customers present in Orders.

The conceptual approach should preserve the customer population, for example:

```text
customers
LEFT JOIN customer revenue/order aggregates
```

so customers with zero qualifying orders can be classified as:

```text
Inactive
```

---

# 17. Dashboard Requirements

The dashboard must contain at least:

### Tile 1

Top 10 products by revenue.

```text
Bar chart
```

Source:

```text
gold.sales_by_product
```

### Tile 2

Customer revenue distribution.

```text
Histogram
```

Source:

```text
gold.revenue_by_customer
```

### Tile 3

Customer segmentation.

```text
Pie chart
```

Source:

```text
gold.customer_segmentation
```

Do not build a larger BI solution unless specifically requested.

---

# 18. Testing Requirements

Testing is part of implementation, not an afterthought.

At minimum verify that the intentional data-quality defects are detected.

Required validation scenarios include:

```text
50 NULL customer emails
100 NULL order customer IDs
200 NULL order product IDs
50 invalid customer references
30 invalid product references
customer duplicate-key condition
order duplicate-key condition
```

Also test:

```text
Bronze row preservation
Silver row preservation
Referential joins do not multiply orders
Gold business key uniqueness
```

Where possible, compare expected versus actual counts.

---

# 19. Data Generation Rules

Generate a valid baseline first.

Then inject intentional defects.

Preferred flow:

```text
Generate valid records
    ↓
Validate baseline
    ↓
Select defect indexes
    ↓
Inject known problems
    ↓
Validate defect counts
    ↓
Write CSV
```

Use deterministic random seeds.

Avoid accidental issue overlap where practical.

Do not introduce real customer information.

All names, emails, and other customer-like data must be synthetic.

---

# 20. Error Handling

Differentiate structural failures from data-quality failures.

Example:

```text
Missing input file
→ pipeline failure
```

```text
NULL customer_id
→ data-quality failure
```

Structural failures should fail clearly.

Data-quality failures should be flagged inside Silver.

Avoid overly complex exception frameworks.

---

# 21. Configuration

Avoid scattering hard-coded environment values throughout the repository.

Environment-specific values should be centralized where practical.

Examples:

```text
source_path
catalog
bronze_schema
silver_schema
gold_schema
```

Keep configuration lightweight.

Do not introduce a large framework for a small exercise.

---

# 22. Implementation Style

Code should be:

- readable,
- maintainable,
- appropriately commented,
- split into focused functions where useful,
- easy for another data engineer to review.

Comments should explain:

```text
why
```

rather than narrating every obvious line.

Avoid unnecessary abstraction.

Do not optimize prematurely.

---

# 23. Scope Guardrails

Do not add any of the following unless explicitly requested:

```text
streaming
CDC
Auto Loader
Delta Live Tables / Lakeflow pipelines
complex orchestration
machine learning
recommendation systems
advanced CI/CD
Terraform
generic data-quality frameworks
production-scale performance tuning
complex class hierarchies
```

The core project is intentionally modest.

Documentation, testing, reasoning, and traceability are more important than additional technical features.

---

# 24. AI Working Style

When assisting with this repository:

1. Read the relevant approved planning files first.
2. Work on only the requested checkpoint/task.
3. Do not generate future layers unless explicitly requested.
4. State assumptions when needed.
5. Identify ambiguities rather than silently deciding.
6. Explain non-trivial implementation choices.
7. Suggest validation steps alongside code.
8. Keep code simple enough for the engineer to understand and defend.
9. Do not rewrite unrelated files.
10. Do not refactor stable code without a clear benefit.

---

# 25. Prompt History Expectations

For meaningful AI interactions, the project owner will record:

```text
prompt
AI response summary
accepted recommendations
changed recommendations
rejected recommendations
reasoning
validation performed
```

Therefore, when proposing a non-trivial decision, explain:

```text
what is being proposed
why it is being proposed
any relevant trade-off
```

Do not hide design decisions inside generated code.

---

# 26. Responsible AI Constraints

Never request or introduce:

- real customer PII,
- production credentials,
- API keys,
- passwords,
- access tokens,
- private keys,
- confidential customer datasets,
- secrets stored in code,
- unnecessary sensitive internal information.

For this exercise, all data is synthetic.

In real production work, use only the minimum necessary sanitized context when interacting with AI systems.

---

# 27. Current Development Checkpoints

The project follows these checkpoints:

```text
Checkpoint 1
Planning & Cursor Context

Checkpoint 2
Synthetic Data Generation

Checkpoint 3
Bronze

Checkpoint 4
Silver + Quality Metrics + Tests

Checkpoint 5
Gold

Checkpoint 6
Dashboard

Checkpoint 7
End-to-End Validation + Documentation + Reflection
```

Do not skip checkpoint validation gates.

---

# 28. Current Project Status

Current phase:

```text
Checkpoint 1 — Planning
```

Planning artifacts prepared or being prepared:

```text
requirements-analysis.md
design-notes.md
data-quality-strategy.md
data-model.md
project-context.md
```

Pipeline implementation has intentionally not started yet.

---

# 29. Definition of Good AI Assistance for This Project

Good assistance means:

```text
understand requirements
→ propose focused implementation
→ explain important choices
→ generate readable code
→ test it
→ inspect results
→ correct problems
→ document decisions
```

Poor assistance means:

```text
generate the whole repository
→ assume it works
→ skip validation
→ hide assumptions
```

Always follow the first approach.