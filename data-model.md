# Data Model

## 1. Purpose

This document defines the logical and physical data model for the e-commerce Medallion Architecture pipeline.

It serves as the schema contract for:

- synthetic data generation,
- Bronze ingestion,
- Silver validation,
- Gold aggregations,
- dashboard queries,
- testing,
- AI-assisted implementation.

The model is intentionally simple and aligned with the scope of the exercise.

The pipeline follows:

```text
CSV Source
   ↓
Bronze
   ↓
Silver
   ↓
Gold
   ↓
Databricks SQL Dashboard
```

---

# 2. Source Data Model

The project contains three source entities:

1. Customers
2. Orders
3. Products

All source data is synthetic.

No real customer PII is used.

---

# 3. Customers Source Model

## 3.1 Business Purpose

The customers dataset represents the customer master used by the e-commerce platform.

## 3.2 Grain

Expected grain:

> One logical customer per `customer_id`.

However, intentional duplicate `customer_id` records are introduced for data-quality testing.

## 3.3 Schema

| Column | Type | Nullable | Description |
|---|---|---:|---|
| customer_id | INT | No | Intended customer primary key |
| customer_name | STRING | No | Synthetic customer name |
| email | STRING | Yes | Synthetic customer email |
| country | STRING | No | Customer country |
| signup_date | DATE | No | Customer signup date |
| customer_segment | STRING | No | Premium / Standard / Basic |
| lifetime_value | DECIMAL | No | Synthetic source lifetime value |

## 3.4 Key

Intended primary key:

```text
customer_id
```

## 3.5 Domain Rules

Expected customer segment values:

```text
Premium
Standard
Basic
```

## 3.6 Intentional Quality Issues

The generated source includes:

```text
50 rows with NULL email
10 duplicate customer_id records
```

These issues must remain present in Bronze and be detected in Silver.

---

# 4. Products Source Model

## 4.1 Business Purpose

The products dataset represents the product catalog used by the e-commerce platform.

## 4.2 Grain

Expected grain:

> One product per `product_id`.

## 4.3 Schema

| Column | Type | Nullable | Description |
|---|---|---:|---|
| product_id | INT | No | Intended product primary key |
| product_name | STRING | No | Product name |
| category | STRING | No | Product category |
| price | DECIMAL | No | Product selling price |
| cost | DECIMAL | No | Product cost |
| stock_quantity | INT | No | Current stock level |
| reorder_level | INT | No | Reorder threshold |

## 4.4 Key

Intended primary key:

```text
product_id
```

## 4.5 Intentional Quality Issues

No mandatory seeded quality defects are required for products.

Products should therefore be generated valid by default.

---

# 5. Orders Source Model

## 5.1 Business Purpose

The orders dataset represents customer purchase activity.

## 5.2 Grain

Expected grain:

> One logical order record per `order_id`.

However, intentional duplicate `order_id` records are introduced for data-quality testing.

## 5.3 Schema

| Column | Type | Nullable | Description |
|---|---|---:|---|
| order_id | INT | No | Intended order primary key |
| customer_id | INT | Yes | Foreign key to customers |
| order_date | DATE | No | Order creation date |
| product_id | INT | Yes | Foreign key to products |
| quantity | INT | No | Number of units ordered |
| unit_price | DECIMAL | No | Price per unit |
| total_amount | DECIMAL | No | Order total amount |
| order_status | STRING | No | Pending / Completed / Cancelled |
| payment_date | DATE | Yes | Payment date |

## 5.4 Keys

Intended primary key:

```text
order_id
```

Foreign keys:

```text
orders.customer_id → customers.customer_id

orders.product_id → products.product_id
```

## 5.5 Domain Rules

Expected order status values:

```text
Pending
Completed
Cancelled
```

## 5.6 Intentional Quality Issues

The generated source includes:

```text
100 rows with NULL customer_id

200 rows with NULL product_id

50 rows with customer_id not present in customers

30 rows with product_id not present in products

20 duplicate order_id records
```

These issues must remain in Bronze and be detected in Silver.

---

# 6. Logical Entity Relationships

The logical relationship is:

```text
CUSTOMERS
customer_id PK
     |
     | 1
     |
     | *
ORDERS
customer_id FK
product_id  FK
     |
     | *
     |
     | 1
PRODUCTS
product_id PK
```

Conceptually:

```text
Customer
   |
   | places
   v
Order
   |
   | references
   v
Product
```

---

# 7. Bronze Data Model

## 7.1 Purpose

Bronze represents raw ingested source data.

The business columns should remain unchanged.

Bronze may add operational metadata required for traceability.

## 7.2 Design Principle

Bronze does not:

- remove duplicates,
- fill NULLs,
- validate foreign keys,
- correct values,
- apply business filters.

It preserves what arrived.

---

# 8. Bronze Customers

Recommended table:

```text
bronze.customers
```

## 8.1 Grain

Same as source:

> One physical row per customer CSV row.

This includes duplicate customer IDs.

## 8.2 Columns

Source columns:

```text
customer_id
customer_name
email
country
signup_date
customer_segment
lifetime_value
```

Operational metadata:

```text
_ingested_at
```

Optional:

```text
_source_file
```

## 8.3 Expected Row Behavior

All source rows must be preserved.

Therefore:

```text
customers.csv row count
=
bronze.customers row count
```

for the current batch.

---

# 9. Bronze Orders

Recommended table:

```text
bronze.orders
```

## 9.1 Grain

> One physical row per order CSV row.

Includes:

- NULL customer references,
- NULL product references,
- orphan references,
- duplicate order IDs.

## 9.2 Columns

Source:

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

Operational:

```text
_ingested_at
```

Optional:

```text
_source_file
```

---

# 10. Bronze Products

Recommended table:

```text
bronze.products
```

## 10.1 Grain

> One physical row per product CSV row.

## 10.2 Columns

```text
product_id
product_name
category
price
cost
stock_quantity
reorder_level
_ingested_at
```

Optional:

```text
_source_file
```

---

# 11. Silver Data Model

## 11.1 Purpose

Silver adds:

- data-quality validation,
- explicit quality flags,
- quality failure reasons,
- typed/validated business records.

Silver retains both valid and invalid records.

## 11.2 Design Principle

Silver answers:

> Is this row valid, and if not, why?

---

# 12. Common Silver Quality Columns

The following quality metadata is recommended where applicable:

| Column | Type | Description |
|---|---|---|
| completeness_pass | BOOLEAN | Whether required fields are populated |
| uniqueness_pass | BOOLEAN | Whether intended key uniqueness is satisfied |
| type_validation_pass | BOOLEAN | Whether expected types are valid |
| referential_integrity_pass | BOOLEAN | Whether required references exist |
| business_logic_pass | BOOLEAN | Whether configured business rules pass |
| quality_check_result | STRING | PASS / FAIL |
| quality_failure_reasons | ARRAY<STRING> or equivalent | One or more failure reasons |

Example:

```text
completeness_pass          = true
uniqueness_pass            = true
type_validation_pass       = true
referential_integrity_pass = false
business_logic_pass        = true
quality_check_result       = FAIL
quality_failure_reasons    = ["INVALID_CUSTOMER_REFERENCE"]
```

---

# 13. Silver Customers

Recommended table:

```text
silver.customers
```

## 13.1 Grain

> One physical row per Bronze customer row.

Silver does not remove duplicate customer records.

## 13.2 Columns

Business/source fields:

```text
customer_id
customer_name
email
country
signup_date
customer_segment
lifetime_value
```

Operational metadata retained where useful:

```text
_ingested_at
```

Quality fields:

```text
completeness_pass
uniqueness_pass
type_validation_pass
business_logic_pass
quality_check_result
quality_failure_reasons
```

## 13.3 Referential Integrity

Customer rows do not require parent-reference validation.

Therefore `referential_integrity_pass` may either:

- be omitted from the customer table, or
- be set to TRUE/not applicable consistently.

Preferred implementation:

> Keep only applicable quality fields per dataset if this keeps the model clearer.

The exact choice should remain consistent across code and documentation.

---

# 14. Silver Products

Recommended table:

```text
silver.products
```

## 14.1 Grain

> One physical row per Bronze product row.

## 14.2 Columns

Business/source fields:

```text
product_id
product_name
category
price
cost
stock_quantity
reorder_level
```

Quality fields:

```text
completeness_pass
uniqueness_pass
type_validation_pass
business_logic_pass
quality_check_result
quality_failure_reasons
```

Products have no parent foreign-key relationships.

---

# 15. Silver Orders

Recommended table:

```text
silver.orders
```

## 15.1 Grain

> One physical row per Bronze order row.

Invalid rows remain present.

## 15.2 Columns

Business/source fields:

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

Operational:

```text
_ingested_at
```

Quality metadata:

```text
completeness_pass
uniqueness_pass
type_validation_pass
referential_integrity_pass
business_logic_pass
quality_check_result
quality_failure_reasons
```

## 15.3 Referential Validation

Validate non-null:

```text
customer_id
```

against distinct valid customer identifiers.

Validate non-null:

```text
product_id
```

against valid product identifiers.

NULL values should be reported primarily as completeness failures.

---

# 16. Silver Row Preservation Contract

For this exercise, Silver validation should annotate records rather than delete them.

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

assuming no structural ingestion failure occurs.

This is an important integration test.

---

# 17. Silver Quality Metrics Model

Recommended table:

```text
silver.quality_metrics
```

## 17.1 Purpose

Provide measurable data-quality results for each dataset and rule.

## 17.2 Grain

> One row per dataset + quality rule + evaluation run.

## 17.3 Schema

| Column | Type | Description |
|---|---|---|
| dataset_name | STRING | customers / orders / products |
| check_category | STRING | completeness / uniqueness / type_validation / referential_integrity / business_logic |
| check_name | STRING | Specific rule name |
| records_evaluated | BIGINT | Number of rows evaluated |
| records_passed | BIGINT | Number passing |
| records_failed | BIGINT | Number failing |
| pass_percentage | DECIMAL | Percentage passing |
| evaluated_at | TIMESTAMP | Evaluation timestamp |

Example:

```text
dataset_name      = orders
check_category    = completeness
check_name        = customer_id_not_null
records_evaluated = 100000
records_failed    = 100
...
```

---

# 18. Suggested Quality Check Names

Consistent names help testing and reporting.

## Customers

```text
email_not_null
customer_id_unique
customer_id_type_valid
signup_date_type_valid
lifetime_value_type_valid
customer_segment_valid
lifetime_value_non_negative
signup_date_not_future
```

## Orders

```text
customer_id_not_null
product_id_not_null
order_id_unique
order_id_type_valid
customer_id_type_valid
product_id_type_valid
order_date_type_valid
quantity_type_valid
unit_price_type_valid
total_amount_type_valid
payment_date_type_valid
customer_reference_valid
product_reference_valid
quantity_positive
unit_price_non_negative
total_amount_non_negative
order_status_valid
total_amount_consistent
```

## Products

```text
product_id_unique
product_id_type_valid
price_type_valid
cost_type_valid
stock_quantity_type_valid
reorder_level_type_valid
price_non_negative
cost_non_negative
stock_quantity_non_negative
reorder_level_non_negative
```

Not every suggested check must be implemented if it adds unnecessary complexity.

The final set must remain aligned with `data-quality-strategy.md`.

---

# 19. Analytics Eligibility

The initial Gold input contract is:

```text
quality_check_result = 'PASS'
```

for records used in trusted analytics.

This means failed Silver records remain available but are not automatically included in Gold calculations.

This is a project design decision, not an explicit source requirement.

It may be refined if testing shows that certain non-analytical failures should not block Gold use.

Any change must be documented.

---

# 20. Gold Data Model

The required Gold layer contains three mandatory business outputs:

```text
gold.sales_by_product
gold.revenue_by_customer
gold.customer_segmentation
```

The participant guide also includes a daily/weekly trends SQL file in the repository structure, but that is treated as optional/stretch in this project.

---

# 21. Gold — Sales by Product

Recommended table:

```text
gold.sales_by_product
```

## 21.1 Grain

> One row per product.

## 21.2 Required Columns

| Column | Type | Description |
|---|---|---|
| product_id | INT | Product identifier |
| product_name | STRING | Product name |
| category | STRING | Product category |
| total_orders | BIGINT | Number of qualifying orders |
| total_revenue | DECIMAL | Revenue from qualifying orders |
| avg_order_value | DECIMAL | Average qualifying order value |

## 21.3 Intended Calculations

```text
total_orders =
COUNT(DISTINCT order_id)
```

```text
total_revenue =
SUM(total_amount)
```

```text
avg_order_value =
AVG(total_amount)
```

The final revenue-status eligibility rule must be documented before Gold implementation.

---

# 22. Gold — Revenue by Customer

Recommended table:

```text
gold.revenue_by_customer
```

## 22.1 Grain

> One row per customer.

## 22.2 Required Columns

| Column | Type | Description |
|---|---|---|
| customer_id | INT | Customer identifier |
| customer_name | STRING | Customer name |
| customer_segment | STRING | Premium / Standard / Basic |
| total_orders | BIGINT | Number of qualifying orders |
| total_revenue | DECIMAL | Total qualifying customer revenue |
| avg_order_value | DECIMAL | Average qualifying order value |
| lifetime_value_actual | DECIMAL | Revenue calculated from available order history |

## 22.3 Proposed Definition

Unless revised before implementation:

```text
lifetime_value_actual = SUM(qualifying order revenue)
```

This is distinct from source:

```text
customers.lifetime_value
```

which is synthetic source-system data.

The exact business definition must be documented before Gold implementation.

---

# 23. Gold — Customer Segmentation

Recommended table:

```text
gold.customer_segmentation
```

## 23.1 Grain

> One row per calculated segment.

## 23.2 Required Columns

| Column | Type | Description |
|---|---|---|
| segment_type | STRING | High-Value / Repeat / One-Time / Inactive |
| customer_count | BIGINT | Customers in the segment |
| avg_revenue | DECIMAL | Average revenue for segment |
| total_revenue | DECIMAL | Total segment revenue |

## 23.3 Required Segment Values

```text
High-Value
Repeat
One-Time
Inactive
```

## 23.4 Intermediate Customer-Level Segmentation

Before final aggregation, customers should conceptually receive one segment each.

Example intermediate model:

```text
customer_id
total_orders
total_revenue
segment_type
```

Possible conceptual classification:

```text
Inactive
→ 0 qualifying orders

One-Time
→ 1 qualifying order

Repeat
→ more than 1 qualifying order and not High-Value

High-Value
→ exceeds documented revenue threshold
```

The High-Value threshold is not specified by the participant guide and must be defined before implementation.

---

# 24. Inactive Customer Modeling

Inactive customers require special treatment.

If customer segmentation starts only from orders:

```text
orders INNER JOIN customers
```

customers with no orders disappear.

Therefore the model should conceptually start with:

```text
customers
LEFT JOIN revenue_by_customer / order aggregates
```

and default missing revenue/order counts appropriately.

This ensures the `Inactive` segment can exist.

---

# 25. Optional Gold — Daily/Weekly Trends

Repository placeholder:

```text
src/gold/03_daily_weekly_trends.sql
```

Possible model, only if implemented later:

```text
date_period
period_type
total_orders
total_revenue
avg_order_value
```

This is not part of the current mandatory Gold model.

Do not implement unless core requirements and documentation are complete.

---

# 26. Dashboard Data Sources

The dashboard should consume Gold outputs rather than query raw Bronze records.

## Visualization 1 — Top 10 Products by Revenue

Source:

```text
gold.sales_by_product
```

Required fields:

```text
product_name
total_revenue
```

---

## Visualization 2 — Customer Revenue Distribution

Source:

```text
gold.revenue_by_customer
```

Required field:

```text
total_revenue
```

This dataset supports customer-level revenue distribution.

---

## Visualization 3 — Customer Segmentation

Source:

```text
gold.customer_segmentation
```

Required fields:

```text
segment_type
customer_count
```

---

# 27. Layer-to-Layer Lineage

Expected high-level lineage:

```text
customers.csv
    ↓
bronze.customers
    ↓
silver.customers
    ├───────────────┐
    │               │
    │               v
    │       gold.revenue_by_customer
    │               │
    │               v
    │       gold.customer_segmentation
    │
    └───────────────┐
                    │
orders.csv          │
    ↓               │
bronze.orders       │
    ↓               │
silver.orders ──────┘
    │
    ├────────────────────────────┐
    │                            │
    v                            v
gold.sales_by_product    gold.revenue_by_customer

products.csv
    ↓
bronze.products
    ↓
silver.products
    ↓
gold.sales_by_product
```

---

# 28. Key Constraints by Layer

## Bronze

No logical PK enforcement.

Reason:

Intentional duplicate IDs must remain.

---

## Silver

Primary-key expectations are validated, not enforced by deleting rows.

Examples:

```text
customer_id should be unique
order_id should be unique
product_id should be unique
```

---

## Gold

Gold table grains should be unique by their business keys.

Expected uniqueness:

```text
gold.sales_by_product
→ product_id

gold.revenue_by_customer
→ customer_id

gold.customer_segmentation
→ segment_type
```

These should be validated during testing.

---

# 29. Decimal Handling

Monetary values should use decimal-compatible types rather than floating-point values where practical.

Examples:

```text
price
cost
unit_price
total_amount
lifetime_value
total_revenue
avg_order_value
lifetime_value_actual
```

Exact precision and scale can be finalized during implementation based on generated values and Databricks inference behavior.

The chosen precision should remain consistent across Silver and Gold.

---

# 30. Date Handling

Expected date fields:

```text
customers.signup_date

orders.order_date

orders.payment_date
```

`payment_date` is nullable by design.

NULL `payment_date` alone is therefore not a completeness failure.

---

# 31. Nullability Summary

## Intentionally Nullable

```text
customers.email
```

only because seeded defects intentionally introduce missing values.

```text
orders.customer_id
orders.product_id
```

only because seeded defects intentionally introduce missing references.

```text
orders.payment_date
```

is legitimately nullable by schema design.

---

# 32. Expected Dataset Sizes

Approximate generated sizes:

```text
Customers ≈ 10,000 logical records
Orders    ≈ 100,000 logical records
Products  ≈ 500 records
```

Important:

The final physical row counts depend on how duplicate rows are injected.

For example, if duplicate records are appended rather than created by modifying existing IDs:

```text
customers.csv physical count
```

may exceed 10,000.

Likewise for orders.

The generator must document its exact duplicate strategy so source and Bronze row-count expectations are unambiguous.

---

# 33. Duplicate Semantics

This project distinguishes between:

```text
duplicate records intentionally introduced
```

and:

```text
physical rows participating in duplicate-key groups
```

Example:

If one valid customer record is copied using the same `customer_id`:

```text
1 duplicate row introduced
```

but:

```text
2 physical rows participate in the duplicate-key violation
```

Testing and metrics must account for this distinction.

---

# 34. Naming Convention

Recommended table naming:

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

If the selected Databricks environment does not support this namespace structure, use an equivalent prefix convention.

Example:

```text
bronze_customers
silver_customers
gold_sales_by_product
```

The logical model remains unchanged.

---

# 35. Open Data Model Decisions

The following decisions remain intentionally open until sufficient environment or data evidence exists.

## DM-01 — Physical Namespace

Need to confirm:

- catalog availability,
- schema support,
- final database naming.

## DM-02 — Decimal Precision

Need to finalize precision/scale for monetary fields after inspecting generated values and Databricks behavior.

## DM-03 — Revenue-Eligible Order Status

Need to decide which statuses contribute to Gold revenue.

## DM-04 — `lifetime_value_actual`

Need to finalize the precise qualifying-order definition.

## DM-05 — High-Value Threshold

Need to inspect customer revenue distribution before defining the High-Value threshold.

## DM-06 — Silver Referential Column Consistency

Need to decide whether datasets without applicable referential checks should:

- omit `referential_integrity_pass`, or
- include it with TRUE/not-applicable semantics.

Prefer the clearest approach after implementation design.

## DM-07 — Gold Eligibility

Initial rule:

```text
quality_check_result = PASS
```

but this may be refined if certain quality failures do not affect analytical correctness.

Any refinement must be explicit and documented.

---

# 36. Data Model Acceptance Criteria

The implemented pipeline should satisfy the following model-level conditions:

- [ ] Source customers contain all required columns.
- [ ] Source orders contain all required columns.
- [ ] Source products contain all required columns.
- [ ] Bronze preserves every physical source row.
- [ ] Bronze preserves source business values.
- [ ] Silver preserves Bronze row counts.
- [ ] Silver exposes row-level quality status.
- [ ] Silver exposes failure reasons.
- [ ] Referential validation does not multiply order rows.
- [ ] Quality metrics can be reconciled with known seeded defects.
- [ ] `gold.sales_by_product` has one row per product.
- [ ] `gold.revenue_by_customer` has one row per customer.
- [ ] `gold.customer_segmentation` has one row per segment.
- [ ] Customers with no qualifying orders can participate in the Inactive segment.
- [ ] Gold calculations use documented analytics eligibility rules.
- [ ] Dashboard queries consume business-ready Gold outputs.