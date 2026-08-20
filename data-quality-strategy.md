# Data Quality Strategy

## 1. Purpose

The purpose of the Silver layer is to identify, describe, and measure data-quality problems without silently removing problematic records.

The generated datasets intentionally contain known defects so that the pipeline can demonstrate that its quality checks work correctly.

The quality strategy therefore has two responsibilities:

1. Detect operationally meaningful data-quality problems.
2. Demonstrate through metrics and tests that the expected seeded problems were found.

---

# 2. Quality Principles

The implementation will follow these principles:

### Preserve

Invalid records remain available for inspection.

### Explain

A failed record should expose the reason it failed.

### Measure

Each major quality rule should produce measurable pass/fail results.

### Separate Concerns

Pipeline failures and data-quality failures are different.

Example:

```text
Missing CSV file → pipeline failure

NULL customer_id → data-quality failure
```

### Avoid Hidden Cleaning

The pipeline should not automatically correct bad values unless such behavior is deliberately designed and documented.

### Keep Rules Understandable

Rules should remain straightforward enough for another engineer or reviewer to inspect and explain.

---

# 3. Quality Dimensions

Five dimensions will be implemented.

```text
1. Completeness
2. Uniqueness
3. Type Validation
4. Referential Integrity
5. Business Logic
```

The core quality expectations explicitly emphasized by the exercise are:

```text
Completeness
Uniqueness
Referential Integrity
```

Type validation and business logic are included as additional validation depth.

---

# 4. Completeness Check

## Objective

Ensure critical fields required for processing are populated.

---

## Customers

### Rule

```text
email IS NOT NULL
```

Expected intentional issue:

```text
50 rows with NULL email
```

### Result

Rows with NULL email:

```text
completeness_pass = false
```

Failure reason:

```text
NULL_EMAIL
```

---

## Orders

### Rules

```text
customer_id IS NOT NULL

product_id IS NOT NULL
```

Expected intentional issues:

```text
100 rows with NULL customer_id

200 rows with NULL product_id
```

Possible failure reasons:

```text
NULL_CUSTOMER_ID

NULL_PRODUCT_ID
```

---

## Products

No mandatory completeness issue is intentionally seeded.

However, structurally required fields may still be checked.

At minimum:

```text
product_id IS NOT NULL
product_name IS NOT NULL
```

This is primarily a defensive validation rather than a seeded test scenario.

---

## Threshold

The supplied template suggests:

```text
>99% complete
```

However, row-level validation will still identify every failure regardless of whether the overall threshold is met.

The threshold is useful for reporting health, not for suppressing individual failures.

---

# 5. Uniqueness Check

## Objective

Validate intended primary-key uniqueness.

---

## Customers

Expected key:

```text
customer_id
```

Expected seeded issue:

```text
10 duplicate customer_id records/occurrences
```

---

## Orders

Expected key:

```text
order_id
```

Expected seeded issue:

```text
20 duplicate order_id records/occurrences
```

---

## Products

Expected key:

```text
product_id
```

No intentional duplicate products are required.

---

## Detection Strategy

Use a window count:

```text
COUNT(*) OVER (PARTITION BY key)
```

If:

```text
count > 1
```

then the row participates in a uniqueness violation.

Example:

```text
customer_id = 123
occurs twice
```

Both records are flagged as being part of a duplicate-key condition.

---

## Important Metric Interpretation

The generator requirement and validation result may use different meanings of "duplicate count."

For example:

If 10 extra rows are appended using existing customer IDs:

```text
10 duplicate rows were seeded
```

but uniqueness validation may flag:

```text
20 physical rows
```

because both the original and duplicated row participate in the same duplicate-key condition.

Therefore reporting should distinguish:

```text
duplicate rows intentionally introduced
```

from:

```text
rows participating in duplicate-key violations
```

This difference must be documented and tested rather than treated as an error.

---

# 6. Type Validation

## Objective

Ensure fields can be interpreted using their expected logical data types.

Expected logical types include:

### Customers

```text
customer_id       INT
signup_date       DATE
lifetime_value    DECIMAL
```

### Orders

```text
order_id          INT
customer_id       INT
order_date        DATE
product_id        INT
quantity          INT
unit_price        DECIMAL
total_amount      DECIMAL
payment_date      DATE
```

### Products

```text
product_id        INT
price             DECIMAL
cost              DECIMAL
stock_quantity    INT
reorder_level     INT
```

---

## Challenge

CSV has no native schema.

Databricks schema inference may:

- parse values into expected types,
- widen the inferred type,
- convert malformed data to NULL,
- expose corrupt-record behavior depending on configuration.

Therefore implementation will first inspect the actual Bronze inferred schema.

The validation should remain proportionate to the exercise.

No generic schema-validation framework is required.

---

## Result

Example failure reasons:

```text
INVALID_ORDER_DATE

INVALID_QUANTITY

INVALID_UNIT_PRICE
```

---

# 7. Referential Integrity

## Objective

Ensure child foreign keys refer to valid parent entities.

Referential integrity applies primarily to orders.

---

## Customer Reference Rule

For non-null:

```text
orders.customer_id
```

verify existence in:

```text
customers.customer_id
```

Expected seeded problem:

```text
50 orders with customer_id not present in customers
```

Failure reason:

```text
INVALID_CUSTOMER_REFERENCE
```

---

## Product Reference Rule

For non-null:

```text
orders.product_id
```

verify existence in:

```text
products.product_id
```

Expected seeded problem:

```text
30 orders with product_id not present in products
```

Failure reason:

```text
INVALID_PRODUCT_REFERENCE
```

---

## Null Foreign Keys

A NULL foreign key represents a completeness failure.

Therefore:

```text
customer_id IS NULL
```

should not automatically be reported as:

```text
INVALID_CUSTOMER_REFERENCE
```

Likewise:

```text
product_id IS NULL
```

is primarily a completeness failure.

This keeps metrics meaningful:

```text
missing relationship
```

and

```text
orphan relationship
```

remain separate concepts.

---

## Parent-Key Duplicate Handling

Customers intentionally contain duplicate customer IDs.

Therefore referential validation must use distinct valid identifiers:

```text
DISTINCT customer_id
```

rather than performing a naïve join against all customer rows.

Otherwise one order could be duplicated during validation.

---

# 8. Business Logic Validation

## Objective

Detect logically impossible or invalid business values that may still be technically well-typed.

---

## Customers

Proposed checks:

```text
customer_segment IN (
    'Premium',
    'Standard',
    'Basic'
)
```

```text
lifetime_value >= 0
```

```text
signup_date <= current_date()
```

Potential failure reasons:

```text
INVALID_CUSTOMER_SEGMENT

NEGATIVE_LIFETIME_VALUE

FUTURE_SIGNUP_DATE
```

---

## Orders

Proposed checks:

```text
quantity > 0
```

```text
unit_price >= 0
```

```text
total_amount >= 0
```

```text
order_status IN (
    'Pending',
    'Completed',
    'Cancelled'
)
```

Potential consistency rule:

```text
total_amount = quantity * unit_price
```

with appropriate decimal rounding.

Potential failure reasons:

```text
INVALID_QUANTITY

NEGATIVE_UNIT_PRICE

NEGATIVE_TOTAL_AMOUNT

INVALID_ORDER_STATUS

TOTAL_AMOUNT_MISMATCH
```

---

## Products

Proposed checks:

```text
price >= 0
```

```text
cost >= 0
```

```text
stock_quantity >= 0
```

```text
reorder_level >= 0
```

Failure reasons:

```text
NEGATIVE_PRODUCT_PRICE

NEGATIVE_PRODUCT_COST

NEGATIVE_STOCK_QUANTITY

NEGATIVE_REORDER_LEVEL
```

---

# 9. Payment Date Strategy

`payment_date` is explicitly nullable in the source definition.

Therefore:

```text
payment_date IS NULL
```

must not automatically fail completeness validation.

Possible business relationships such as:

```text
Completed → payment_date required
```

are not defined by the exercise.

We will not enforce them initially unless the generated data contract explicitly defines that behavior.

This avoids inventing an unsupported business rule.

---

# 10. Row-Level Quality Schema

Recommended Silver quality metadata:

```text
completeness_pass
uniqueness_pass
type_validation_pass
referential_integrity_pass
business_logic_pass
quality_check_result
quality_failure_reasons
```

Example passing row:

```text
completeness_pass          = true
uniqueness_pass            = true
type_validation_pass       = true
referential_integrity_pass = true
business_logic_pass        = true
quality_check_result       = "PASS"
quality_failure_reasons    = []
```

Example failing row:

```text
completeness_pass          = true
uniqueness_pass            = true
type_validation_pass       = true
referential_integrity_pass = false
business_logic_pass        = true
quality_check_result       = "FAIL"
quality_failure_reasons    = ["INVALID_CUSTOMER_REFERENCE"]
```

Example multiple failures:

```text
quality_failure_reasons =
[
    "NULL_PRODUCT_ID",
    "INVALID_QUANTITY"
]
```

---

# 11. Overall Quality Result

A row passes overall quality only when all applicable checks pass.

Conceptually:

```text
quality_check_result =
    PASS
    if all applicable checks are true
    else FAIL
```

Products may not require referential-integrity validation.

Therefore the final result should account for only checks relevant to that dataset.

---

# 12. Quality Metrics Report

A persisted metrics table is recommended:

```text
silver.quality_metrics
```

Suggested schema:

```text
dataset_name        STRING
check_name          STRING
records_evaluated   BIGINT
records_passed      BIGINT
records_failed      BIGINT
pass_percentage     DECIMAL
evaluated_at        TIMESTAMP
```

Example:

```text
orders
completeness_customer_id
100000
99900
100
99.90
...
```

---

# 13. Metrics Granularity

Rather than reporting only:

```text
Completeness = 99.7%
```

the implementation should preferably expose rule-level metrics.

Example:

```text
customers.email_completeness

customers.customer_id_uniqueness

orders.customer_id_completeness

orders.product_id_completeness

orders.order_id_uniqueness

orders.customer_referential_integrity

orders.product_referential_integrity
```

These may also be grouped into higher-level categories for summary reporting.

This makes failures easier to reconcile with known seeded defects.

---

# 14. Pass Percentage Formula

For a rule:

```text
pass_percentage =
(records_passed / records_evaluated) * 100
```

Use safe handling if:

```text
records_evaluated = 0
```

although that scenario is not expected for the generated datasets.

---

# 15. Expected Seeded Issues

The generator must deliberately introduce:

## Customers

```text
50 NULL email rows
10 duplicate customer_id rows
```

## Orders

```text
100 NULL customer_id rows
200 NULL product_id rows
50 nonexistent customer_id references
30 nonexistent product_id references
20 duplicate order_id rows
```

## Products

```text
No mandatory seeded defects
```

The exercise describes this as roughly:

```text
~700 problematic rows
~0.7%
```

The exact count of **rows failing Silver** may differ depending on:

- duplicate-detection semantics,
- whether issue groups overlap,
- whether both original and duplicate records are marked,
- additional defensive rules.

Therefore `~700` should be treated as the intended source-quality profile, not assumed to be the exact final count of all failure flags.

---

# 16. Intentional Issue Injection Strategy

To make validation deterministic:

1. Generate valid baseline records.
2. Verify baseline structural validity.
3. Select issue indexes.
4. Keep issue groups non-overlapping where practical.
5. Inject each issue category.
6. Record selected counts.
7. Validate the final dataset before writing CSV.

Example:

```text
valid orders
   ↓
select 100 indexes
   ↓
set customer_id = NULL
   ↓
select separate 200 indexes
   ↓
set product_id = NULL
```

This prevents accidental overlap from making expected metrics difficult to explain.

---

# 17. Quality Validation Tests

The primary test tier will verify that Silver detects intentionally generated defects.

---

## Test 1 — Customer Email Completeness

Expected:

```text
50 seeded NULL emails
```

Validate:

```text
count of NULL_EMAIL failures
```

matches the generated input expectation.

---

## Test 2 — Customer Key Uniqueness

Validate that duplicated customer IDs are identified.

The assertion must account for whether the quality implementation counts:

```text
duplicate records added
```

or:

```text
all records participating in duplicate groups
```

---

## Test 3 — Order Customer Completeness

Expected:

```text
100 NULL customer_id rows
```

Validate corresponding completeness failures.

---

## Test 4 — Order Product Completeness

Expected:

```text
200 NULL product_id rows
```

Validate corresponding completeness failures.

---

## Test 5 — Customer Referential Integrity

Expected:

```text
50 non-null invalid customer references
```

Validate:

```text
INVALID_CUSTOMER_REFERENCE
```

count.

---

## Test 6 — Product Referential Integrity

Expected:

```text
30 non-null invalid product references
```

Validate:

```text
INVALID_PRODUCT_REFERENCE
```

count.

---

## Test 7 — Order Key Uniqueness

Validate the seeded duplicate-order condition.

Again, distinguish:

```text
duplicates intentionally appended
```

from:

```text
all rows belonging to duplicate-key groups
```

---

# 18. Baseline Quality Assertions

Before introducing bad data, the generator should preferably ensure the base records satisfy basic rules.

Examples:

```text
valid customer_id ranges

valid product_id ranges

positive quantity

non-negative prices

valid statuses

valid customer segments
```

This prevents accidental defects from making expected validation results unreliable.

---

# 19. Gold Eligibility

Initial analytics rule:

```text
quality_check_result = 'PASS'
```

Only rows passing all applicable Silver validations are used for Gold aggregations.

Reason:

This creates a straightforward relationship between:

```text
Silver trusted records
```

and:

```text
Gold analytical data
```

A more nuanced model could allow non-critical failures such as missing email to remain analytically usable, but that additional policy complexity is unnecessary unless testing shows it materially improves the project.

---

# 20. Quality Reporting Example

A reviewer should be able to inspect results similar to:

```text
Dataset    Rule                              Failed    Passed %
----------------------------------------------------------------
customers  email completeness                  50       ...
customers  customer_id uniqueness              ...      ...
orders     customer_id completeness            100      ...
orders     product_id completeness             200      ...
orders     customer referential integrity       50      ...
orders     product referential integrity        30      ...
orders     order_id uniqueness                  ...      ...
```

The exact uniqueness failed-row counts depend on duplicate-group semantics and should be explained.

---

# 21. Data Quality vs Data Cleaning

The Silver layer is primarily a validation layer for this exercise.

It should not silently:

- invent missing emails,
- replace invalid foreign keys,
- drop duplicates,
- convert orphan orders to another customer/product,
- modify invalid values without evidence.

Instead:

```text
detect
flag
measure
preserve
```

This supports traceability and makes the quality workflow visible.

---

# 22. Debugging Data Quality

When observed metrics do not match expected seeded conditions:

1. Check generator issue counts.
2. Check whether intentional issue groups overlap.
3. Check Bronze row counts.
4. Inspect inferred Bronze schema.
5. Inspect specific failed records.
6. Check window/join logic.
7. Verify NULL handling.
8. Compare distinct IDs before referential joins.
9. Confirm duplicated rows have not multiplied joins.
10. Document the root cause and correction.

---

# 23. Quality Strategy Success Criteria

The strategy is considered successfully implemented when:

- [ ] Required seeded issues exist in generated files.
- [ ] Bronze preserves them.
- [ ] Completeness checks identify expected missing values.
- [ ] Uniqueness checks identify duplicate key groups.
- [ ] Referential checks identify orphan customer/product references.
- [ ] Type validation executes successfully.
- [ ] Selected business rules execute successfully.
- [ ] Failing records remain in Silver.
- [ ] Failure reasons are inspectable.
- [ ] Metrics report passed/failed counts and percentages.
- [ ] Known seeded problems are verified by tests.
- [ ] Gold uses a clearly documented trusted-data policy.
- [ ] Quality behavior is documented and explainable.