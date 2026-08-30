# AI Tool Workflow

## 1. Purpose

This document describes how I used AI tools during the Databricks Medallion Architecture project.

The primary AI development tool for this exercise is:

```text
Cursor
```

The objective is not to use AI only as a code generator.

Instead, I used AI across the data engineering lifecycle for:

```text
requirements
→ design
→ implementation
→ validation
→ testing
→ debugging
→ documentation
→ reflection
```

The final engineering decisions and validation remain my responsibility.

This final version reflects the workflow actually followed and distinguishes
implemented behavior from work that was only planned or statically reviewed.

---

# 2. Primary AI Tool

Primary tool:

```text
Cursor
```

I used Cursor because it can work directly with repository context and consider
project requirements, design documentation, code, and implementation
instructions together.

The project intentionally provides Cursor with persistent repository context instead of repeatedly using isolated prompts with no background information.

---

# 3. How Project Context Is Provided to AI

A structured planning package is maintained inside the repository.

The primary project documents are:

```text
requirements-analysis.md
design-notes.md
data-model.md
data-quality-strategy.md
```

Cursor-specific context is stored under:

```text
tool-specific/cursor-workflow/
```

including:

```text
project-context.md
spec.md
cursor-rules-or-instructions.md
task-breakdown.md
```

These files provide different types of context.

### `requirements-analysis.md`

Explains:

- what needs to be built,
- functional requirements,
- non-functional requirements,
- assumptions,
- edge cases,
- ambiguities,
- acceptance criteria.

### `design-notes.md`

Explains:

- Medallion Architecture,
- responsibilities of each layer,
- validation strategy,
- testing strategy,
- error handling,
- architecture decisions.

### `data-model.md`

Defines:

- source schemas,
- table grains,
- keys,
- foreign-key relationships,
- Bronze/Silver/Gold structures,
- quality metric model.

### `data-quality-strategy.md`

Defines:

- completeness,
- uniqueness,
- type validation,
- referential integrity,
- business logic,
- failure flags,
- metrics,
- expected quality test scenarios.

### `project-context.md`

Provides Cursor with a compact persistent understanding of the entire project.

### `spec.md`

Defines the expected finished implementation and its acceptance conditions.

### `cursor-rules-or-instructions.md`

Defines how Cursor is expected to behave while editing the repository.

### `task-breakdown.md`

Defines the checkpoint-by-checkpoint implementation sequence.

---

# 4. Why Persistent Context Is Used

A one-line prompt such as:

```text
Build a Databricks medallion pipeline
```

does not provide enough context for reliable implementation.

It leaves many decisions open to the AI, including:

- source schema,
- quality rules,
- layer responsibilities,
- failure handling,
- business definitions,
- testing expectations,
- project scope.

Instead, each implementation prompt directed Cursor to read the relevant
project documents first.

The expected pattern is:

```text
persistent project context
+
task-specific prompt
+
validation requirements
```

This reduced the likelihood that AI silently invented architecture or business
logic.

The first implementation prompts were deliberately detailed while the project
contracts were still being established. For example, the data-generation
prompt repeated exact row counts, defect counts, duplicate semantics, and
validation requirements. Later prompts became shorter because those decisions
were already stored in the repository and could be referenced directly.

The Gold and dashboard prompts therefore focused mainly on the active business
decisions and allowed files instead of restating the complete pipeline. This
made the interaction more efficient without removing the source of truth.

---

# 5. How AI Is Used for Requirement Analysis

I used AI as a discussion and analysis partner rather than asking it
immediately to generate code.

The requirements workflow is:

```text
Read assessment/problem statement
        ↓
Break requirements into functional and non-functional requirements
        ↓
Identify assumptions
        ↓
Identify ambiguities
        ↓
Identify edge cases
        ↓
Create acceptance criteria
```

An important rule was to keep ambiguous requirements visible.

During planning, the unresolved questions included:

- the exact definition of `lifetime_value_actual`,
- which order statuses count as revenue,
- how High-Value customers are classified,
- how duplicate-row counts should be interpreted.

I did not allow Cursor to silently convert those uncertainties into business
requirements. I later supplied the Gold decisions explicitly: Completed orders
define revenue, `lifetime_value_actual` is qualifying completed-order revenue,
and the top revenue quintile defines High-Value customers.

---

# 6. How AI Is Used for Pipeline Design

AI assisted with architecture discussions before implementation.

The approved high-level architecture is:

```text
Synthetic CSV
     ↓
Bronze
     ↓
Silver
     ↓
Gold
     ↓
Dashboard
```

Each layer has a distinct responsibility.

## Bronze

```text
Preserve what arrived.
```

Bronze does not clean or remove intentional quality problems.

## Silver

```text
Validate, flag, measure, preserve.
```

Silver detects bad data but keeps the records available.

## Gold

```text
Business-ready analytics.
```

Gold uses explicitly documented eligibility and business rules.

## Dashboard

```text
Stakeholder-facing analytical views.
```

The dashboard uses Gold data rather than rebuilding business logic directly against raw data.

---

# 7. How AI Is Used for Code Generation

Code generation followed small, focused tasks.

I did not implement the project using one prompt such as:

```text
Generate the complete repository.
```

Instead, development followed checkpoints:

```text
Checkpoint 1
Planning

Checkpoint 2
Data Generation

Checkpoint 3
Bronze

Checkpoint 4
Silver

Checkpoint 5
Gold

Checkpoint 6
Dashboard

Checkpoint 7
Final Validation & Documentation
```

Within each checkpoint, I divided the work further.

For example, Silver implementation is separated into:

```text
completeness
uniqueness
type validation
referential integrity
business logic
final Silver tables
quality metrics
tests
```

This allowed me to review AI-generated work before introducing the next layer.

## What Cursor helped me produce by checkpoint

### Data generation

Cursor implemented the pandas/Faker generator, deterministic seeds, fixed-row
duplicate strategy, exact defect injection, validation assertions, generated
CSV files, and generation notes. I rejected adding extra defects to force the
data toward an approximate issue count.

### Bronze

Cursor produced three PySpark ingestion scripts, Unity Catalog Volume paths,
Delta overwrite behavior, `_ingested_at`, inferred-schema output, and
source-to-Bronze count checks. I removed its unnecessary active Spark-session
lookup.

### Silver

Cursor produced five focused DataFrame validation modules and the final
orchestration script. The implementation preserves rows, uses distinct parent
keys for referential checks, records dimension flags and specific failure
reasons, and writes rerun-safe Silver Delta tables. I kept Python module imports
after validating them in Databricks rather than changing to `%run`.

### Gold

Cursor produced SQL for sales by product, revenue by customer, customer
segmentation, and daily/weekly trends. I supplied the business rules rather
than allowing them to be inferred: Completed orders only, PASS Silver rows,
actual lifetime value from qualifying revenue, and a top-20-percent High-Value
segment. The Python runner adds grain and reconciliation checks.

### Dashboard

Cursor produced Gold-only SQL for the three required visualizations and an
optional weekly trend, plus a guide covering field mappings, filters, and
interpretation. No dashboard query rebuilds logic from Silver.

### Documentation

Cursor helped organize planning documents, checkpoint prompt histories, setup
notes, generation notes, the dashboard guide, and debugging notes. I reviewed
runtime claims against the recorded evidence and avoided describing unrecorded
runs as successful.

---

# 8. Standard Implementation Prompt Pattern

Implementation prompts sent to Cursor generally contained:

```text
1. Active checkpoint
2. Task being implemented
3. Context files to read
4. Files allowed to change
5. Exact requirements
6. Constraints
7. Validation expectations
8. Stop condition
```

Example structure:

```text
Active checkpoint:
Checkpoint 2 — Synthetic Data Generation

Read:
- requirements-analysis.md
- data-model.md
- data-quality-strategy.md
- project-context.md
- spec.md
- cursor-rules-or-instructions.md

Task:
Implement only the synthetic data generator.

Do not:
- create Bronze code
- create Silver code
- create Gold code

After implementation:
- summarize changes
- explain important decisions
- provide validation steps
- identify assumptions
- stop
```

I also used lightweight role-based prompting, such as:

```text
Act as a senior Databricks data engineer
```

or:

```text
Act as a senior Databricks analytics engineer
```

The role statement was only a short framing device. The actual control came
from the repository context, explicit requirements, file scope, and validation
criteria. I did not rely on a long persona prompt to determine correctness.

---

# 9. How AI-Generated Code Is Validated

AI-generated code is not considered correct merely because:

```text
it looks correct
```

or:

```text
it runs without an exception
```

I validated behavior where the available runtime allowed it and recorded when
only static validation was available.

The general workflow is:

```text
AI generates change
        ↓
Review implementation
        ↓
Run code
        ↓
Inspect actual results
        ↓
Compare with expected behavior
        ↓
Fix/refine if necessary
        ↓
Accept change
```

---

# 10. Validation Approach — Data Generation

The synthetic generator has known expected defects.

Therefore validation can compare expected and actual conditions.

Examples:

```text
Expected:
50 NULL customer emails

Actual:
count rows where email IS NULL
```

The generator also verified:

```text
100 NULL order customer IDs
200 NULL order product IDs
50 invalid customer references
30 invalid product references
customer duplicate condition
order duplicate condition
```

This created a deterministic validation target for AI-generated logic. I ran
the generator locally and checked the exact physical row counts, NULL counts,
orphan counts, duplicate-group semantics, and product-key uniqueness before
accepting the generated CSV files.

---

# 11. Validation Approach — Bronze

Bronze validation focused on preservation.

Examples:

```text
source row count
=
Bronze row count
```

and intentional defects must still exist.

The Bronze scripts also check:

- expected schema,
- ingestion timestamp,
- rerun behavior,
- clear handling of structural failures.

---

# 12. Validation Approach — Silver

Silver validation covered both detection and preservation.

Examples:

```text
known NULL values are detected

known orphan references are detected

duplicate-key groups are detected

Bronze row count = Silver row count

referential joins do not multiply orders
```

The composed Silver layer retained specific failure reasons. Its module imports,
validation functions, Delta writes, and row preservation were executed
successfully in Databricks.

---

# 13. Validation Approach — Gold

Gold validation was designed not to rely only on successful SQL execution.

The runner includes checks for:

- table grain,
- uniqueness,
- manual calculation of selected products/customers,
- revenue reconciliation,
- segmentation population checks.

For example:

```text
gold.sales_by_product
```

was expected to have:

```text
one row per product_id
```

and selected totals are designed to be reproducible from eligible Silver
orders. I corrected the Gold runner's notebook path handling after the
`__file__` error. A complete post-fix Gold rerun is not recorded in the
repository evidence, so I leave that runtime result open.

---

# 14. Validation Approach — Dashboard

I created dashboard SQL that reads only the Gold tables and documented the
Databricks visualization mappings. Static checks confirmed that the queries do
not reference Bronze or Silver. The repository does not record completed
dashboard runtime/configuration validation, so I do not claim it here.

Required views include:

```text
Top 10 products by revenue

Customer revenue distribution

Customer segmentation
```

---

# 15. How AI Is Used for Testing

AI assisted with identifying useful test scenarios and generating focused
validation logic.

I treated testing as verification of behavior, not simply execution.

The most important testing tier for this exercise is:

```text
data-quality detection tests
```

because the project intentionally creates known defective records.

The Silver checks were designed to prove that the known defects were identified
without dropping rows.

Additional integration validations were built around:

```text
CSV → Bronze

Bronze → Silver

Silver → Gold
```

---

# 16. How AI Is Used for Debugging

When implementation problems occurred, I used AI to help form hypotheses and
small fixes.

The debugging workflow is:

```text
Reproduce problem
      ↓
Inspect actual error/output
      ↓
Identify smallest failing component
      ↓
Form hypothesis
      ↓
Use AI for additional possible causes if useful
      ↓
Validate hypotheses
      ↓
Apply smallest appropriate fix
      ↓
Rerun tests
      ↓
Document result
```

AI explanations are treated as hypotheses until verified.

The actual issues were the unnecessary Bronze Spark-session lookup, the Silver
module import decision, and the Gold notebook's missing `__file__`. They are
documented in `debugging-notes.md`. I did not create artificial failures to
make the debugging history look larger.

---

# 17. How AI Is Used for Data Quality

AI assisted with:

- defining quality rules,
- checking whether the rules match the requirements,
- writing PySpark validation logic,
- designing failure indicators,
- designing quality metrics,
- identifying validation edge cases.

However, the expected quality conditions originate from the project requirements and approved data-quality strategy.

I did not allow AI to arbitrarily redefine quality requirements.

---

# 18. Data Quality Dimensions

The project implements five quality categories:

```text
Completeness
Uniqueness
Type Validation
Referential Integrity
Business Logic
```

The project treats the following as mandatory core validations:

```text
Completeness
Uniqueness
Referential Integrity
```

Type validation and business logic provide additional depth.

---

# 19. Data Quality Preservation Principle

The main Silver tables follow:

```text
detect
+
flag
+
measure
+
preserve
```

rather than:

```text
detect
+
delete
```

Invalid records remain available for investigation and quality reporting.

---

# 20. How AI Is Used for Documentation

AI assisted with:

- document organization,
- translating implementation details into clear explanations,
- checking consistency,
- identifying missing information,
- improving readability.

AI must not invent:

- test results,
- debugging incidents,
- implementation outcomes,
- business decisions that were never made.

Documentation must describe what actually happened.

---

# 21. Prompt History

AI usage is recorded by activity under:

```text
ai-prompts/
```

The prompt-history files present in this repository are:

```text
data-generation.md
bronze-layer.md
silver-layer.md
gold-layer.md
```

Dashboard and documentation work is represented by the resulting implementation
files and this finalized workflow document rather than by prompt-history files
that do not exist.

For meaningful interactions, I recorded:

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

The objective is to show reasoning and iteration rather than simply collect prompts.

---

# 22. How AI Suggestions Are Evaluated

AI suggestions fall into three categories.

## Accepted

I accepted a suggestion when:

- it matched approved requirements,
- the reasoning was sound,
- it kept the solution appropriately scoped,
- validation confirmed the behavior.

## Changed

I modified a suggestion when:

- the core idea was useful,
- but implementation details did not fit the environment or project design.

## Rejected

I rejected a suggestion when it:

- violated the architecture,
- invented unsupported business requirements,
- unnecessarily expanded scope,
- conflicted with the data model,
- could not be validated,
- introduced unnecessary complexity.

I documented the reason for important rejections.

---

# 23. Information I Would Avoid Sharing With AI in Production

This exercise uses fully synthetic data.

In a real production project, I would avoid unnecessarily sharing:

```text
real customer PII

real names and email addresses

health or financial information

production passwords

API keys

access tokens

private keys

service account credentials

database passwords

production secrets

confidential customer datasets

sensitive business metrics

security configurations

internal infrastructure information that is not required
```

The principle is:

```text
share the minimum context necessary
```

rather than:

```text
share everything because it may help
```

---

# 24. Production-Safe Alternatives

Where AI assistance is useful but production data is sensitive, safer context can include:

```text
synthetic sample records

redacted values

schema definitions

table names where permitted

sanitized error messages

representative fake examples

aggregated statistics

minimal reproducible test cases
```

The objective is to provide enough information to solve the engineering problem without unnecessarily exposing sensitive data.

---

# 25. Human Ownership

Cursor assisted me with implementation, but responsibility remained with me.

I remain responsible for:

- understanding the generated code,
- validating results,
- identifying unsupported assumptions,
- making final design decisions,
- confirming security and privacy requirements,
- deciding what is committed to the repository.

A Cursor-generated solution is not considered complete until it has been reviewed and validated.

---

# 26. Reusable Workflow

The reusable workflow I followed is:

```text
Understand problem
        ↓
Write requirements
        ↓
Identify assumptions and ambiguity
        ↓
Design solution
        ↓
Provide persistent context to AI
        ↓
Break implementation into small tasks
        ↓
Generate focused change
        ↓
Review
        ↓
Run
        ↓
Validate
        ↓
Refine
        ↓
Document
```

This workflow can be adapted to production data engineering projects with stricter privacy, security, testing, review, and deployment controls.

---

# 27. Current Project Status

The implemented repository now includes:

```text
deterministic synthetic data generation
Bronze CSV ingestion
Silver quality validation and persisted Silver tables
four Gold analytical outputs
dashboard SQL and dashboard setup guidance
```

The Silver orchestration and its Python module imports were validated in
Databricks. The Gold runner was corrected after the notebook environment raised
a `NameError` for `__file__`; the repository does not contain evidence of a
complete Gold rerun after that correction, so I do not describe that rerun as
passed here. Dashboard queries and documentation were checked statically
against the Gold-only source requirement.

---

# 28. What AI Helped With Most

Cursor was most useful when the task had a clear contract and a narrow file
scope. It helped me turn the planning documents into:

- deterministic generation code with exact defect assertions,
- repetitive but consistent Bronze ingestion scripts,
- reusable Silver validation functions,
- readable Gold SQL and validation checks,
- visualization-ready dashboard queries,
- structured implementation and debugging documentation.

The strongest results came from giving Cursor the rule, the allowed files, the
validation expectation, and an explicit stop condition.

## What AI Got Wrong

Cursor initially added `SparkSession.getActiveSession()` to the Bronze scripts.
That was generic Python/Spark boilerplate rather than a requirement of this
Databricks-only environment, so I removed it.

Cursor also used `Path(__file__)` in the Gold runner. That works in a normal
Python script but failed in the Databricks notebook with:

```text
NameError: name '__file__' is not defined
```

I changed the runner to use `Path.cwd()`. This was a reminder that plausible
local Python patterns still need validation in the actual notebook runtime.

## What I Changed or Rejected

I changed or rejected several suggestions and possible extensions:

- I removed explicit Spark-session retrieval and used Databricks' built-in
  `spark`.
- I did not add unspecified defects merely to make the approximate “~700”
  statement match; I kept the explicit seeded counts.
- I kept pandas and Faker for local data generation rather than introducing
  PySpark for a small generation workload.
- I did not add malformed types or extra business-rule failures that were not
  required.
- I considered `%run` for the numerically prefixed Silver files but retained
  `importlib.import_module()` after it worked in Databricks.
- I kept dashboard queries on Gold tables and did not recreate Silver or Gold
  business logic in the dashboard layer.

## Debugging Experience

The actual debugging work was small but useful:

1. I removed the unnecessary Bronze active-session lookup.
2. I tested Python module imports against `%run` and retained imports after
   Databricks execution succeeded.
3. I replaced the Gold runner's `__file__` path logic after the Databricks
   notebook raised a `NameError`.

The detailed observations, decisions, and validation evidence are recorded in
`debugging-notes.md`.

## Lessons Learned

Persistent context improved consistency, but it did not remove the need for
runtime review. Cursor followed detailed data-quality and scope constraints
well, while environment-specific assumptions still required my intervention.

I also found that deterministic data made downstream validation much easier.
Because the defect counts and duplicate semantics were fixed, I could reason
about expected Silver failures instead of treating every discrepancy as an
unknown.

## What I Would Do Differently in Production

For production work I would:

- package Python modules with conventional identifiers instead of numeric
  filenames requiring dynamic imports,
- use explicit source schemas and a controlled schema-evolution policy rather
  than relying only on CSV inference,
- move catalog, schema, and storage paths into reviewed environment
  configuration,
- use incremental ingestion and idempotent keys where the source process
  requires them instead of snapshot overwrite,
- add automated unit, integration, and deployment checks,
- persist quality metrics and connect them to monitoring and alerting,
- record run IDs and richer lineage/audit metadata,
- validate notebook filesystem behavior before using local path assumptions,
- apply production access controls and secret management.

I would still use sanitized schemas, synthetic examples, and minimal
reproducible samples when asking AI for help.

---

# 29. Evidence Used for This Finalization

I finalized this document against:

```text
ai-prompts/data-generation.md
ai-prompts/bronze-layer.md
ai-prompts/silver-layer.md
ai-prompts/gold-layer.md
debugging-notes.md
requirements-analysis.md
design-notes.md
the implemented pipeline and dashboard files
```

Statements about runtime success are limited to results recorded in those
artifacts.