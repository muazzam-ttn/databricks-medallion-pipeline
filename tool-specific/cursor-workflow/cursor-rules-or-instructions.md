# Cursor Rules and Instructions

## 1. Purpose

These rules define how Cursor should work inside this repository.

They are intended to keep AI-assisted changes:

- aligned with the approved requirements,
- limited to the active checkpoint,
- easy to review,
- easy to validate,
- easy to explain,
- appropriately scoped for the exercise.

These rules apply to all implementation, review, debugging, testing, and documentation tasks performed with Cursor.

---

# 2. Read Project Context Before Making Changes

Before making any non-trivial code or design change, read the relevant approved project files.

Core context:

```text
requirements-analysis.md
design-notes.md
data-model.md
data-quality-strategy.md
tool-specific/cursor-workflow/project-context.md
tool-specific/cursor-workflow/spec.md
```

Use these documents as the source of truth.

Do not rely only on the latest prompt if the repository already contains approved design context.

---

# 3. Work Only on the Active Task

Implement only the task explicitly requested in the current prompt.

Do not automatically continue into later layers.

Examples:

If the task is:

```text
Generate synthetic sample data
```

do not also create:

```text
Bronze ingestion
Silver validation
Gold tables
Dashboard queries
```

If the task is:

```text
Implement Bronze customer ingestion
```

do not automatically implement all Bronze or Silver files unless explicitly requested.

---

# 4. Respect Checkpoint Boundaries

The project follows:

```text
Checkpoint 1 — Planning

Checkpoint 2 — Data Generation

Checkpoint 3 — Bronze

Checkpoint 4 — Silver

Checkpoint 5 — Gold

Checkpoint 6 — Dashboard

Checkpoint 7 — Final Validation and Documentation
```

Do not implement a later checkpoint until the current checkpoint has been tested and accepted.

---

# 5. Do Not Invent Business Requirements

If the approved project documents do not define a business rule, do not silently create one.

Examples of currently open decisions include:

```text
Which order statuses count as revenue?

What exactly defines lifetime_value_actual?

What threshold defines a High-Value customer?

Which Silver failures should block Gold eligibility?
```

If a task depends on an unresolved decision:

1. identify the dependency,
2. state why it affects implementation,
3. avoid silently choosing an arbitrary rule.

---

# 6. Preserve the Medallion Responsibilities

## Bronze

Bronze must represent raw ingestion.

Do not:

- remove duplicates,
- replace NULL values,
- fix invalid foreign keys,
- apply business validation,
- filter bad records.

Bronze may add operational metadata such as:

```text
_ingested_at
_source_file
```

---

## Silver

Silver must validate and flag.

Do not silently delete bad records.

Silver should retain enough information to understand:

```text
whether the row passed
and
why it failed
```

---

## Gold

Gold must contain business-ready analytical outputs.

Gold must use explicitly documented eligibility and business rules.

Do not hide business assumptions inside SQL expressions without documenting them.

---

# 7. Preserve Synthetic-Only Data

All customer-like data in this project must be synthetic.

Never introduce:

- real customer names,
- real customer email addresses,
- real phone numbers,
- production customer data,
- actual PII.

Use Faker or equivalent synthetic generation.

---

# 8. Never Request or Store Secrets

Do not request, generate, or commit:

```text
passwords
API keys
access tokens
private keys
service account credentials
production secrets
```

Do not hard-code credentials into code, notebooks, configuration files, or documentation.

---

# 9. Generate Valid Data Before Injecting Defects

For synthetic data generation:

```text
generate valid baseline
→ validate baseline
→ inject intentional quality issues
→ validate expected issue counts
→ write CSV
```

Do not randomly generate bad records throughout the dataset if that makes issue counts unpredictable.

---

# 10. Make Data Generation Reproducible

Use deterministic seeds for random generation.

Where relevant, seed:

```text
random
NumPy
Faker
```

Re-running the generator should make debugging and testing predictable.

---

# 11. Protect Intentional Quality Issue Counts

The required intentional defects must remain deliberate and measurable.

Customers:

```text
50 NULL email rows
10 duplicate customer_id records
```

Orders:

```text
100 NULL customer_id rows
200 NULL product_id rows
50 invalid customer_id references
30 invalid product_id references
20 duplicate order_id records
```

Do not introduce additional accidental defects that make expected results difficult to reconcile.

Where practical, use non-overlapping issue groups.

---

# 12. Document Duplicate Semantics

Do not assume that:

```text
number of duplicate rows introduced
```

equals:

```text
number of rows flagged by uniqueness validation
```

If one duplicate row is added to an existing key, both physical records may participate in the duplicate group.

Make this distinction explicit in tests and documentation.

---

# 13. Avoid Referential Join Multiplication

Customers intentionally contain duplicate customer IDs.

Therefore, when validating:

```text
orders.customer_id
```

against customers, do not join directly to a parent table that contains duplicate IDs in a way that multiplies order rows.

Use distinct parent identifiers or another safe existence-check method.

Apply the same principle wherever duplicate parent rows could affect child cardinality.

---

# 14. Separate NULL Foreign Keys From Orphan References

Treat:

```text
customer_id IS NULL
```

as a completeness failure.

Treat:

```text
customer_id IS NOT NULL
but no parent customer exists
```

as a referential-integrity failure.

Apply the same distinction to:

```text
product_id
```

Do not double-count NULL foreign keys as orphan references unless explicitly required.

---

# 15. Keep payment_date Nullable

The source contract explicitly allows:

```text
payment_date = NULL
```

Do not treat NULL `payment_date` as a completeness failure.

Do not impose additional payment-date business rules unless they are explicitly approved.

---

# 16. Use Readable Quality Metadata

Prefer explicit row-level validation fields.

Recommended pattern:

```text
completeness_pass
uniqueness_pass
type_validation_pass
referential_integrity_pass
business_logic_pass
quality_check_result
quality_failure_reasons
```

Do not produce only:

```text
quality_check_result = FAIL
```

when failure reasons can be captured clearly.

---

# 17. Do Not Drop Silver Failures

Silver must retain invalid rows.

Do not use:

```text
filter(valid_only)
```

to construct the main Silver table.

Filtering may be used later when explicitly selecting analytics-eligible records for Gold.

---

# 18. Preserve Bronze-to-Silver Row Counts

The expected validation pattern is:

```text
Bronze row
→ Silver row with quality metadata
```

Therefore the main Silver tables should preserve Bronze physical row counts.

If counts differ, investigate and explain the reason before accepting the implementation.

---

# 19. Keep Quality Rules Explicit

Quality rules should be implemented in a way another engineer can understand.

Avoid hiding all validation behavior inside overly generic abstractions.

Prefer clear expressions and focused helper functions.

The project should demonstrate engineering judgment, not framework complexity.

---

# 20. Keep Type Validation Proportionate

Do not build a generic schema-validation platform.

First inspect how Databricks parsed the source CSV.

Then implement only the type-validation logic necessary for this exercise.

If the generated input contains no intentional malformed type values, verify that:

- expected fields are represented correctly,
- valid rows pass,
- the validation mechanism behaves consistently.

---

# 21. Use Decimal-Safe Monetary Logic

For monetary values such as:

```text
price
cost
unit_price
total_amount
lifetime_value
total_revenue
```

avoid unnecessary floating-point logic where decimal-safe handling is practical.

If comparing:

```text
total_amount
```

with:

```text
quantity * unit_price
```

account for decimal precision appropriately.

---

# 22. Use Clear Error Handling

Differentiate:

```text
pipeline error
```

from:

```text
data-quality error
```

Examples:

```text
Missing input file
→ fail clearly
```

```text
Missing required source column
→ fail clearly
```

```text
NULL customer_id
→ retain row and flag in Silver
```

Do not catch every exception and silently continue.

---

# 23. Avoid Over-Engineering

Do not introduce unnecessary:

```text
class hierarchies
frameworks
factory patterns
complex configuration systems
generic plugin architectures
large dependency stacks
```

Prefer focused functions and straightforward PySpark/SQL.

The core exercise is intentionally modest.

---

# 24. Do Not Add Unrequested Platform Features

Unless explicitly requested, do not introduce:

```text
streaming
Structured Streaming
Auto Loader
CDC
Change Data Feed
Lakeflow Declarative Pipelines
Delta Live Tables
complex Databricks Workflows
Terraform
advanced CI/CD
MLflow
machine learning
recommendation systems
```

These are outside the current scope.

---

# 25. Avoid Premature Performance Optimization

The datasets are approximately:

```text
10,000 customers
100,000 orders
500 products
```

Do not introduce advanced optimization merely because Databricks supports it.

Examples to avoid unless evidence requires them:

```text
manual partitioning strategies
Z-ORDER optimization
liquid clustering
complex caching
custom repartition strategies
```

Correctness and explainability come first.

---

# 26. Centralize Environment Configuration

Avoid hard-coded environment values scattered across files.

Values such as:

```text
source path
catalog
bronze schema
silver schema
gold schema
```

should be configurable from a small, obvious location where practical.

Do not create a large configuration framework.

---

# 27. Keep Environment Assumptions Visible

The final Databricks environment may affect:

```text
catalog naming
schema naming
storage paths
DBFS availability
Unity Catalog usage
SQL Warehouse availability
```

Do not assume features are available until confirmed.

If implementation depends on an unavailable feature, use the simplest compatible alternative and document it.

---

# 28. Keep Functions Focused

Use functions where they improve:

- readability,
- reuse,
- testing,
- debugging.

Avoid very large procedural scripts where logical units can be separated cleanly.

Also avoid breaking simple logic into excessive micro-functions.

---

# 29. Comment Non-Obvious Logic

Comments should explain:

```text
why this is needed
```

Examples:

```text
why distinct parent IDs are used for RI validation

why bad rows are preserved

why specific seeded indexes are kept separate
```

Do not comment every obvious line.

---

# 30. Preserve Existing Approved Work

Do not rewrite or refactor unrelated stable files while implementing a focused task.

If a requested change requires another file to change:

1. identify the dependency,
2. explain why,
3. make the smallest appropriate change.

---

# 31. Validate Generated Code Before Considering It Complete

For every implementation task, provide validation steps.

Examples:

Data generation:

```text
verify row counts
verify NULL counts
verify orphan counts
verify duplicate groups
```

Bronze:

```text
compare source and target row counts
inspect schema
confirm bad rows preserved
```

Silver:

```text
verify expected failures
verify no row multiplication
verify row preservation
inspect failure reasons
```

Gold:

```text
manual aggregation spot checks
check grain uniqueness
reconcile totals
```

---

# 32. Testing Must Validate Behavior

Do not write tests whose only assertion is:

```text
script executes successfully
```

Tests should prove meaningful behavior.

Examples:

```text
seeded NULL emails are detected

invalid customer references are flagged

duplicate-key groups are detected

Silver preserves Bronze rows

Gold product_id is unique
```

---

# 33. Do Not Fake Test Results

Never document a test as passing unless it was actually executed and its output was observed.

If a test cannot be executed in the current environment, state that clearly.

---

# 34. Do Not Fake Debugging History

Only document real issues encountered.

Do not intentionally introduce bugs simply to create debugging evidence.

When an actual issue occurs, preserve enough detail to explain:

```text
symptom
hypothesis
root cause
fix
validation
```

---

# 35. Explain Non-Trivial Suggestions

Whenever proposing something beyond a direct mechanical implementation, explain:

```text
what is proposed
why it helps
trade-off if relevant
```

Examples:

- choosing a window function for duplicates,
- using distinct parent IDs,
- choosing overwrite behavior,
- structuring quality metrics.

This reasoning may be recorded in AI prompt history.

---

# 36. Make Assumptions Explicit

When an implementation depends on an assumption:

1. state the assumption,
2. identify whether it is already approved,
3. avoid presenting it as a source requirement if it is only a project decision.

---

# 37. Respect Open Decisions

Current open decisions include:

```text
Databricks physical namespace

Gold revenue-eligible order statuses

lifetime_value_actual definition

High-Value threshold

Gold analytics eligibility policy

exact duplicate physical-row generation strategy
```

Do not resolve these silently.

---

# 38. Keep Gold Business Logic Visible

Gold SQL should make important calculations easy to identify.

Avoid unnecessary nested transformations that obscure:

```text
counts
sums
averages
eligibility filters
segmentation conditions
```

Business logic should be reviewable directly from the SQL.

---

# 39. Preserve Customers With No Orders

Customer segmentation requires:

```text
Inactive
```

customers.

Do not construct the customer segmentation population solely from Orders.

Use a customer-first approach that preserves customers with zero qualifying orders.

---

# 40. Gold Grain Must Be Testable

Expected Gold uniqueness:

```text
gold.sales_by_product
→ one row per product_id

gold.revenue_by_customer
→ one row per customer_id

gold.customer_segmentation
→ one row per segment_type
```

Validation should confirm these grains.

---

# 41. Dashboard Must Use Gold Data

Do not build required dashboard queries directly from Bronze unless explicitly justified.

Required dashboard sources should be business-ready Gold outputs.

---

# 42. Keep Dashboard Scope Small

Required dashboard:

```text
Top 10 products by revenue — bar

Customer revenue distribution — histogram

Customer segmentation — pie
```

Do not create a large dashboard suite unless explicitly requested.

---

# 43. Maintain Prompt-History-Friendly Responses

When completing a task, structure the response so the engineer can easily record:

```text
what changed
important design choices
validation to perform
assumptions
open questions
```

Avoid responses that provide code without context.

---

# 44. Prefer Small Iterations

Recommended implementation cycle:

```text
read context
→ implement one focused task
→ validate
→ inspect output
→ refine
→ document
→ commit
```

Avoid large one-shot implementations.

---

# 45. Stop After the Requested Scope

After finishing a task:

- summarize what was changed,
- provide validation steps,
- identify any unresolved issue,
- stop.

Do not automatically begin the next checkpoint.

---

# 46. Responsible Production-AI Mindset

Although this exercise uses synthetic data, recommendations should reflect production-aware judgment.

In real production settings, avoid unnecessarily sharing with AI:

- real PII,
- sensitive health/financial information,
- production credentials,
- proprietary customer datasets,
- confidential queries or data samples,
- internal secrets,
- unnecessary infrastructure details.

Use sanitized schemas, synthetic examples, or redacted samples whenever sufficient.

---

# 47. Priorities

When trade-offs occur, prioritize in this order:

```text
1. Correctness

2. Alignment with approved requirements

3. Data traceability

4. Validation and testing

5. Readability

6. Documentation

7. Maintainability

8. Simplicity

9. Optional enhancements
```

Do not sacrifice the first six priorities for unnecessary sophistication.

---

# 48. Definition of an Acceptable Cursor Change

A Cursor-generated change is not considered accepted merely because code was produced.

It becomes acceptable only after:

```text
requirements reviewed
+
code reviewed
+
tests/validation executed
+
results inspected
+
assumptions understood
```

The engineer remains responsible for the final implementation.