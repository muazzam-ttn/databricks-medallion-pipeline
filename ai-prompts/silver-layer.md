# AI Prompts — Silver Layer

## Context

This file documents the AI-assisted work completed during:

```text
Checkpoint 4 — Silver Layer
```

Primary AI tool:

```text
Cursor
```

The Silver layer is being implemented incrementally.

The first Silver task focused only on reusable data-quality validation modules.

The final Silver tables, combined quality status, failure reasons, quality metrics, and persistence were intentionally deferred to the next step.

---

# Prompt 1 — Reusable Silver Quality Modules

## Prompt Sent

```text
Act as a senior Databricks data engineer implementing the Silver data-quality validation layer. Prioritize clear quality rules, row preservation, traceability, and simple, reusable PySpark.

## Before Making Changes

Read the following files first:

* data-model.md
* data-quality-strategy.md
* design-notes.md
* tool-specific/cursor-workflow/project-context.md
* tool-specific/cursor-workflow/cursor-rules-or-instructions.md
* tool-specific/cursor-workflow/task-breakdown.md

## Active Checkpoint

**Checkpoint 4 — Silver Layer**

For this task, implement **only the reusable quality-validation modules**:

* src/silver/01_quality_completeness.py
* src/silver/02_quality_uniqueness.py
* src/silver/03_quality_type_validation.py
* src/silver/04_quality_referential_integrity.py
* src/silver/05_quality_business_logic.py

**Do not implement:**

* create_silver_tables.py
* Gold-layer logic
* Dashboard logic
* Quality-metrics persistence

## Bronze Inputs

Use the following Bronze tables:

* ecommerce_sales.bronze.customers
* ecommerce_sales.bronze.orders
* ecommerce_sales.bronze.products

The quality modules must:

* Operate on DataFrames.
* Return DataFrames containing their applicable validation-result column.
* Not independently write Silver tables.

Use these consistent result columns:

* completeness_pass
* uniqueness_pass
* type_validation_pass
* referential_integrity_pass
* business_logic_pass

## Quality Rules

### 1. Completeness

**Customers**

* email IS NOT NULL

**Orders**

* customer_id IS NOT NULL
* product_id IS NOT NULL

payment_date is legitimately nullable and must not be treated as a completeness failure.

**Products**

* Basic required-field completeness checks may be included.
* Do not invent seeded product defects.

### 2. Uniqueness

Validate the following keys:

* customers.customer_id
* orders.order_id
* products.product_id

Requirements:

* Flag **all physical rows** participating in a duplicate-key group.
* Do not drop duplicates.
* Preserve every input row.

### 3. Type Validation

* Inspect and use the actual Bronze Spark schemas.
* Validate that relevant fields conform to the expected logical data types defined in data-model.md.
* Keep type validation lightweight.
* The generated source intentionally contains no malformed-type defects.
* Do not invent malformed types or force artificial failures.

### 4. Referential Integrity

Apply referential-integrity validation to **Orders only**:

* orders.customer_id → customers.customer_id
* orders.product_id → products.product_id

Requirements:

* NULL foreign keys belong to completeness validation and must **not** be flagged as orphan-reference failures.
* Use distinct parent IDs or another safe existence-check approach so duplicate customer/product IDs do not multiply order rows.
* Customers and products should return referential_integrity_pass = true when this check is later composed, because no parent-reference validation applies to them.

### 5. Business Logic

**Customers**

* customer_segment IN ('Premium', 'Standard', 'Basic')
* lifetime_value >= 0
* signup_date <= current_date()

**Orders**

* quantity > 0
* unit_price >= 0
* total_amount >= 0
* order_status IN ('Pending', 'Completed', 'Cancelled')
* total_amount is consistent with quantity * unit_price

**Products**

* price >= 0
* cost >= 0
* stock_quantity >= 0
* reorder_level >= 0

Do not add unsupported business rules.

## Important Constraints

* Do not delete or filter bad rows.
* Do not modify Bronze tables.
* Do not write final Silver tables from these modules.
* Avoid join-induced row multiplication.
* Keep functions focused, simple, and readable.
* Use the Databricks-provided Spark session where needed.
* Do not create or retrieve a separate SparkSession.
* Do not introduce a generic data-quality framework.
* Do not introduce unnecessary classes or abstractions.
* Prefer simple, reusable PySpark.

## Expected Output

After implementation, summarize:

1. The functions created in each module.
2. The exact rules implemented.
3. How uniqueness is detected.
4. How referential integrity avoids row multiplication.
5. How type validation handles the inferred Bronze schemas.
6. Any assumptions or design issues discovered.

Then **STOP**.

Do not implement create_silver_tables.py yet.
```

Cursor was asked to act as a senior Databricks data engineer and implement only the five reusable Silver validation modules:

```text
src/silver/01_quality_completeness.py
src/silver/02_quality_uniqueness.py
src/silver/03_quality_type_validation.py
src/silver/04_quality_referential_integrity.py
src/silver/05_quality_business_logic.py
```

Cursor was instructed to read the approved project context before implementation, including:

```text
data-model.md
data-quality-strategy.md
design-notes.md
tool-specific/cursor-workflow/project-context.md
tool-specific/cursor-workflow/cursor-rules-or-instructions.md
tool-specific/cursor-workflow/task-breakdown.md
```

The modules were required to:

* operate DataFrame-to-DataFrame,
* preserve every source row,
* add one validation-result Boolean column,
* avoid independently writing Silver tables,
* avoid creating or retrieving a SparkSession,
* avoid performing Gold or dashboard work,
* avoid introducing a generic data-quality framework.

The requested quality dimensions were:

```text
Completeness
Uniqueness
Type Validation
Referential Integrity
Business Logic
```

---

# AI Response Summary

Cursor implemented five reusable modules.

The response summarized the implementation as:

> The five modules now expose only DataFrame-to-DataFrame validation functions. Referential checks filter only temporary distinct parent-key sets—not order rows—and every module adds or replaces one boolean result column without writing tables.

The implemented function groups were:

```text
Completeness
- customer validator
- order validator
- product validator

Uniqueness
- customer validator
- order validator
- product validator

Type Validation
- customer validator
- order validator
- product validator

Referential Integrity
- customer validator
- order validator
- product validator

Business Logic
- customer validator
- order validator
- product validator
```

Cursor explicitly stopped before implementing:

```text
create_silver_tables.py
quality metrics
Gold
dashboard
```

---

# What I Accepted

## 1. DataFrame-to-DataFrame Validation Functions

Each module accepts a DataFrame and returns the same logical records with one additional quality-result column.

### Why accepted

This keeps individual checks reusable and makes the final Silver orchestration responsible for composing them.

It avoids having five different scripts independently writing competing versions of the same Silver table.

---

# 2. Completeness Rules

Implemented customer completeness:

```text
email IS NOT NULL
```

Implemented order completeness:

```text
customer_id IS NOT NULL
AND
product_id IS NOT NULL
```

Implemented defensive product completeness:

```text
product_id IS NOT NULL
AND
product_name IS NOT NULL
```

`payment_date` remains legitimately nullable.

### Why accepted

These rules match the approved data-quality strategy.

The product rule provides a lightweight structural safeguard without inventing product defects.

---

# 3. Uniqueness Using a Window Function

Cursor implemented uniqueness using:

```text
COUNT(*) OVER (PARTITION BY key)
```

with the equivalent rule:

```text
count == 1
→ PASS

count > 1
→ FAIL
```

### Why accepted

This correctly flags every physical record participating in a duplicate-key group without deleting records.

Therefore the expected uniqueness failures are based on duplicate-group membership rather than only the number of rows deliberately modified during data generation.

For the generated datasets:

```text
Customers:
10 duplicate groups
20 physical rows expected to fail uniqueness

Orders:
20 duplicate groups
40 physical rows expected to fail uniqueness
```


# 4. NULL Foreign Keys Belong to Completeness

The referential-integrity implementation follows:

```text
NULL customer_id
→ completeness failure
→ RI passes / not treated as orphan

non-null unknown customer_id
→ RI failure
```

The same behavior applies to `product_id`.

### Why accepted

Missing references and orphan references are different quality problems.

Keeping them separate produces clearer metrics later.

---

# 5. Decimal-Safe Order Total Validation

Cursor casts monetary values to Decimal types before comparing:

```text
total_amount
```

with:

```text
quantity * unit_price
```

### Why accepted

This avoids unnecessary floating-point comparison issues after CSV schema inference.

---

# What I Rejected / Did Not Add

## 1. Independent Silver Writes

The individual validation modules do not write:

```text
ecommerce_sales.silver.customers
ecommerce_sales.silver.orders
ecommerce_sales.silver.products
```

### Reason

Persistence belongs in:

```text
create_silver_tables.py
```

after all applicable validation dimensions have been composed.

---

# 2. Row Filtering

No validation module removes bad records.

### Reason

The Silver requirement is:

```text
validate
+
flag
+
preserve
```

not:

```text
validate
+
delete
```

---

# 3. Additional Business Rules

No unsupported business rules were added.

Examples intentionally avoided include rules such as:

```text
price must always exceed cost
Completed order must always have payment_date
specific revenue-status behavior
```

because these were not established as project requirements.

---

# Runtime Validation Status

Cursor reported:

```text
No linter errors.
```

However:

```text
PySpark behavior was not executed locally.
```

because the modules require Databricks/PySpark runtime data.

Therefore the current status is:

```text
Implementation review:
ACCEPTED

Databricks runtime validation:
PENDING
```

Runtime validation will occur when the functions are composed inside:

```text
create_silver_tables.py
```

and executed against:

```text
ecommerce_sales.bronze.customers
ecommerce_sales.bronze.orders
ecommerce_sales.bronze.products
```

---

# Expected Runtime Results

Based on the generated source data, the important expected failures include:

## Completeness

```text
Customers email:
50 failed rows

Orders customer_id:
100 failed rows

Orders product_id:
200 failed rows
```

## Uniqueness

```text
Customers:
20 physical rows expected to fail

Orders:
40 physical rows expected to fail

Products:
0 expected failures
```

## Referential Integrity

```text
Orders invalid customer references:
50

Orders invalid product references:
30
```

NULL foreign keys should not contribute to RI failures.

## Type Validation

Expected:

```text
PASS
```

provided the actual Bronze inferred Spark types match one of the approved logical type families.

## Business Logic

Expected:

```text
mostly/all PASS
```

because the generated baseline intentionally satisfies the approved business rules.

---

# Next Step

The next Silver task is to compose the five modules inside:

```text
src/silver/create_silver_tables.py
```

The composition step will:

```text
read Bronze
→ apply all five validations
→ produce common quality metadata
→ generate quality_failure_reasons
→ generate overall quality_check_result
→ persist Silver tables
→ preserve Bronze row counts
```

Quality metrics will also be derived from the resulting validation columns once the final Silver representation is available.
