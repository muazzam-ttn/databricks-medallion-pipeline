# AI Prompts — Data Generation

## Context

This file documents the AI-assisted work completed during:

```text
Checkpoint 2 — Synthetic Data Generation
```

Primary AI tool:

```text
Cursor
```

The implementation was generated using the approved project planning documents as persistent repository context rather than placing the full project specification inside the prompt.

Relevant context files included:

```text
requirements-analysis.md
design-notes.md
data-model.md
data-quality-strategy.md
tool-specific/cursor-workflow/project-context.md
tool-specific/cursor-workflow/spec.md
tool-specific/cursor-workflow/cursor-rules-or-instructions.md
tool-specific/cursor-workflow/task-breakdown.md
```

---

# Prompt 1 — Synthetic Data Generator

## Prompt Sent

```
Act as a senior data engineer implementing deterministic synthetic test data for this project. Follow the repository planning documents as the source of truth and do not expand scope.

Checkpoint 2 — Synthetic Data Generation

Before making changes, read and follow:

text
requirements-analysis.md
design-notes.md
data-model.md
data-quality-strategy.md
tool-specific/cursor-workflow/project-context.md
tool-specific/cursor-workflow/spec.md
tool-specific/cursor-workflow/cursor-rules-or-instructions.md
tool-specific/cursor-workflow/task-breakdown.md


Task

Implement Checkpoint 2 — Synthetic Data Generation only.

Create/update:

text
src/data_generation/generate_sample_data.py
src/data_generation/DATA_GENERATION_NOTES.md

data/customers.csv
data/orders.csv
data/products.csv


Do not implement or modify Bronze, Silver, Gold, or dashboard code.

Important decisions for this checkpoint

Use Python with pandas and Faker.

Generate valid baseline data first, then inject the intentional quality issues.

Keep final physical row counts fixed at:

text
customers = 10,000
orders    = 100,000
products  = 500


For duplicates, reuse existing IDs within the fixed row counts rather than appending extra rows.

Seed exactly the explicitly specified defects:

Customers

text
50 NULL email rows
10 rows modified to create duplicate customer_id values


Orders

text
100 NULL customer_id rows
200 NULL product_id rows
50 non-null invalid customer_id references
30 non-null invalid product_id references
20 rows modified to create duplicate order_id values


Keep these issue groups non-overlapping where practical.

Do not invent additional defects to reach the guide's approximate "~700 problematic rows" statement. Follow the explicitly specified defect counts and document the discrepancy in DATA_GENERATION_NOTES.md.

Do not intentionally seed extra type-validation or business-rule failures.

Use deterministic random seeds.

All customer-like information must be synthetic.

Validation

The generator should validate before accepting the output:

 exact physical row counts,
 required columns,
 exact NULL counts,
 invalid FK counts,
 duplicate-key conditions,
 unique product IDs,
 no unintended foreign-key failures.

Make failures explicit using assertions or clear validation errors.

Document duplicate semantics clearly—for example, 10 customer rows are deliberately modified, but 20 physical rows may later be flagged as members of duplicate-key groups.

After implementation

Provide:

1. files changed,
2. important implementation decisions,
3. how to run the generator,
4. validation results if you executed it,
5. any assumptions or issues discovered.

If you did not execute the code, say so clearly.

Then STOP. Do not proceed to Bronze.
```


Cursor was asked to implement only Checkpoint 2 — Synthetic Data Generation.

The prompt instructed Cursor to:

- read the approved planning/context files,
- use Python with pandas and Faker,
- generate valid baseline data before injecting defects,
- keep physical row counts fixed at:
  - 10,000 customers,
  - 100,000 orders,
  - 500 products,
- reuse existing IDs to create duplicate-key conditions rather than appending rows,
- seed only the explicitly required quality issues,
- keep issue groups non-overlapping where practical,
- use deterministic random seeds,
- validate expected counts programmatically,
- document the data-generation methodology,
- not implement Bronze, Silver, Gold, or dashboard functionality.

The prompt also explicitly instructed Cursor not to invent additional defects simply to make the guide's approximate "~700 problematic rows" statement match the explicitly listed defect counts.

---

# AI Response Summary

Cursor created:

```text
src/data_generation/generate_sample_data.py

src/data_generation/DATA_GENERATION_NOTES.md
```

The implementation uses:

```text
Python
pandas
Faker
Decimal
random.Random
```

The generator follows this pattern:

```text
generate valid baseline
→ validate baseline
→ inject controlled quality defects
→ validate final conditions
→ write CSV
```

Deterministic seeds are defined for both Python random generation and Faker.

The generator creates:

```text
10,000 customer rows
100,000 order rows
500 product rows
```

without increasing physical row counts for duplicate-key defects.

---

# What I Accepted

## 1. Deterministic Generation

Cursor introduced fixed seeds:

```text
RANDOM_SEED = 20260820
FAKER_SEED = 20260821
```

### Why accepted

Reproducible source data makes:

- debugging easier,
- quality-count validation predictable,
- reruns comparable,
- tests deterministic.

---

## 2. Valid Baseline Before Defect Injection

The implementation generates structurally valid datasets first and validates them before introducing intentional bad data.

### Why accepted

This isolates intentional quality failures from accidental generator defects.

It also provides a clear test contract for the Silver layer later.

---

## 3. Fixed Physical Row Counts

The implementation keeps:

```text
customers = 10,000
orders    = 100,000
products  = 500
```

even after duplicate conditions are introduced.

### Why accepted

This resolves the ambiguity between logical row-count requirements and duplicate injection while preserving the explicitly requested dataset sizes.

---

## 4. Duplicate-Key Strategy

For customers:

```text
10 rows are modified to reuse existing customer IDs.
```

This creates:

```text
10 duplicate-key groups
20 physical rows participating in duplicate groups
```

For orders:

```text
20 rows are modified to reuse existing order IDs.
```

This creates:

```text
20 duplicate-key groups
40 physical rows participating in duplicate groups
```

### Why accepted

This strategy:

- preserves physical row counts,
- produces deterministic uniqueness failures,
- makes later uniqueness testing straightforward.

---

## 5. Non-Overlapping Order Defects

Cursor reserves duplicate-related rows first and selects the remaining quality issue indexes from non-overlapping rows.

### Why accepted

This makes quality metrics easier to reconcile.

For example:

```text
NULL customer_id
```

does not unintentionally overlap with:

```text
invalid product_id
```

unless intentionally designed.

---

## 6. Guaranteed Invalid Foreign Keys

Invalid customer IDs are generated above the maximum valid customer ID.

Invalid product IDs are generated above the maximum valid product ID.

### Why accepted

This guarantees the values are genuine orphan references rather than relying on probability.

---

## 7. Explicit Validation Functions

The script includes validation for:

- exact row counts,
- expected columns,
- NULL counts,
- invalid foreign-key counts,
- duplicate groups,
- unintended NULLs,
- valid domains,
- order amount consistency,
- non-overlapping order defects.

### Why accepted

The generator validates its own output rather than assuming generation logic is correct.

This provides our first meaningful test tier.

---

## 8. Decimal-Based Monetary Generation

Monetary values are generated from integer cents using `Decimal`.

### Why accepted

This avoids unnecessary floating-point precision problems for:

```text
price
cost
unit_price
total_amount
lifetime_value
```

and makes:

```text
total_amount = quantity * unit_price
```

deterministic.

---

# What I Changed

No major architecture changes were required after Cursor generated the implementation.

The implementation followed the approved Checkpoint 2 design closely.

The environment setup, however, changed from the original generic storage assumption.

The generated CSV files were manually uploaded to a Databricks Volume because the Databricks Free Edition environment does not use DBFS for this project.

The actual source paths are:

```text
/Volumes/ecommerce_sales/raw/source_files/customers.csv

/Volumes/ecommerce_sales/raw/source_files/orders.csv

/Volumes/ecommerce_sales/raw/source_files/products.csv
```

The Databricks objects now created are:

```text
Catalog:
ecommerce_sales

Schema:
raw

Volume:
source_files
```

This environment-specific information will be used by the Bronze ingestion implementation.

---

# What I Rejected / Did Not Add

## 1. Additional Defects to Reach "~700"

No additional quality failures were added solely to make the guide's approximate "~700 problematic rows" statement match.

### Why

The explicitly specified conditions total:

```text
50 + 10 + 100 + 200 + 50 + 30 + 20
= 460
```

deliberately modified rows/conditions.

Introducing unspecified bad records would weaken traceability.

---

## 2. Additional Type Errors

No malformed numeric/date/string values were intentionally seeded.

### Why

The project includes type validation later, but the source requirements do not specify intentional malformed-type rows.

---

## 3. Additional Business-Logic Errors

No negative quantities, invalid statuses, invalid customer segments, or similar extra failures were seeded.

### Why

Business-logic validation will still exist in Silver, but the generator should not invent additional defects that were never required.

---

## 4. PySpark for Local Data Generation

PySpark was not used for synthetic data generation.

### Why

The source datasets are small enough for pandas/Faker, making the implementation simpler and easier to validate.

PySpark will be used for Databricks pipeline processing.

---

# Validation Performed

The generated implementation contains assertions that verify:

## Customers

```text
10,000 physical rows
50 NULL emails
10 duplicate-key groups
20 rows participating in duplicate-key groups
valid segment values
no unexpected NULL values
```

## Products

```text
500 physical rows
unique product_id
no unexpected NULL values
non-negative monetary/inventory fields
```

## Orders

```text
100,000 physical rows
100 NULL customer_id values
200 NULL product_id values
50 invalid non-null customer references
30 invalid non-null product references
20 duplicate-key groups
40 rows participating in duplicate-key groups
non-overlapping intentional issue groups
valid quantities/statuses
consistent order totals
```

The generated files were subsequently uploaded to a Databricks Volume for the next pipeline checkpoint.

---

# Databricks Source Location

Current source location:

```text
Catalog: ecommerce_sales
Schema: raw
Volume: source_files
```

Files:

```text
/Volumes/ecommerce_sales/raw/source_files/customers.csv
/Volumes/ecommerce_sales/raw/source_files/products.csv
/Volumes/ecommerce_sales/raw/source_files/orders.csv
```

This becomes the source contract for Checkpoint 3 — Bronze ingestion.

---

# Final Decision

**ACCEPTED**

The generated implementation is suitable as the Checkpoint 2 baseline because it:

- follows the approved data model,
- keeps generation deterministic,
- preserves exact physical row counts,
- seeds the requested quality issues,
- validates those issues before output,
- avoids adding unsupported defects,
- remains appropriately scoped.

Checkpoint 2 is considered complete once the generated CSVs and their validation results have been confirmed in the development environment.

The next implementation phase is:

```text
Checkpoint 3 — Bronze Layer
```