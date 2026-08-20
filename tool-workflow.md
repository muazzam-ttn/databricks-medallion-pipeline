# AI Tool Workflow

## 1. Purpose

This document describes how I use AI tools during the Databricks Medallion Architecture project.

The primary AI development tool for this exercise is:

```text
Cursor
```

The objective is not to use AI only as a code generator.

Instead, AI is used across the data engineering lifecycle for:

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

This document will be updated throughout the exercise so that it reflects the workflow actually followed rather than only the workflow originally planned.

---

# 2. Primary AI Tool

Primary tool:

```text
Cursor
```

Cursor is used because it can work directly with repository context and allows project requirements, design documentation, code, and implementation instructions to be considered together.

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

Instead, each implementation prompt will direct Cursor to read the relevant project documents first.

The expected pattern is:

```text
persistent project context
+
task-specific prompt
+
validation requirements
```

This reduces the likelihood that AI silently invents architecture or business logic.

---

# 5. How AI Is Used for Requirement Analysis

AI is used as a discussion and analysis partner rather than being asked immediately to generate code.

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

An important rule is that ambiguous requirements remain visible.

For example, the project identifies unresolved questions around:

- the exact definition of `lifetime_value_actual`,
- which order statuses count as revenue,
- how High-Value customers are classified,
- how duplicate-row counts should be interpreted.

AI should not silently convert these uncertainties into business requirements.

---

# 6. How AI Is Used for Pipeline Design

AI assists with architecture discussions before implementation.

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

Code generation follows small, focused tasks.

The project is not implemented using one prompt such as:

```text
Generate the complete repository.
```

Instead, development follows checkpoints:

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

Within each checkpoint, tasks are further divided.

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

This allows AI-generated work to be reviewed and validated before additional complexity is introduced.

---

# 8. Standard Implementation Prompt Pattern

Implementation prompts sent to Cursor should generally contain:

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

Validation should check behavior.

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

The synthetic generator will have known expected defects.

Therefore validation can compare expected and actual conditions.

Examples:

```text
Expected:
50 NULL customer emails

Actual:
count rows where email IS NULL
```

Similar checks will verify:

```text
100 NULL order customer IDs
200 NULL order product IDs
50 invalid customer references
30 invalid product references
customer duplicate condition
order duplicate condition
```

This creates a deterministic validation target for AI-generated logic.

---

# 11. Validation Approach — Bronze

Bronze validation will focus on preservation.

Examples:

```text
source row count
=
Bronze row count
```

and intentional defects must still exist.

Bronze will also be checked for:

- expected schema,
- ingestion timestamp,
- rerun behavior,
- clear handling of structural failures.

---

# 12. Validation Approach — Silver

Silver validation will verify both detection and preservation.

Examples:

```text
known NULL values are detected

known orphan references are detected

duplicate-key groups are detected

Bronze row count = Silver row count

referential joins do not multiply orders
```

Individual quality failure reasons will also be inspected.

---

# 13. Validation Approach — Gold

Gold validation will not rely only on successful SQL execution.

Checks will include:

- table grain,
- uniqueness,
- manual calculation of selected products/customers,
- revenue reconciliation,
- segmentation population checks.

For example:

```text
gold.sales_by_product
```

should have:

```text
one row per product_id
```

and selected totals should be reproducible from eligible Silver orders.

---

# 14. Validation Approach — Dashboard

Dashboard SQL will be run independently before visualizations are configured.

After dashboard creation, displayed values will be compared against the Gold tables.

Required views include:

```text
Top 10 products by revenue

Customer revenue distribution

Customer segmentation
```

---

# 15. How AI Is Used for Testing

AI assists with identifying useful test scenarios and generating focused test logic.

Testing should verify behavior, not simply execution.

The most important testing tier for this exercise is:

```text
data-quality detection tests
```

because the project intentionally creates known defective records.

Tests should prove that the Silver layer identifies them correctly.

Additional integration validations will check:

```text
CSV → Bronze

Bronze → Silver

Silver → Gold
```

---

# 16. How AI Is Used for Debugging

When an implementation problem occurs, AI may be used to help form hypotheses.

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

Debugging interactions will be documented in:

```text
debugging-notes.md
ai-prompts/debugging.md
```

Only real debugging issues will be recorded.

No bugs will be intentionally created merely to demonstrate debugging activity.

---

# 17. How AI Is Used for Data Quality

AI assists with:

- defining quality rules,
- checking whether the rules match the requirements,
- writing PySpark validation logic,
- designing failure indicators,
- designing quality metrics,
- identifying validation edge cases.

However, the expected quality conditions originate from the project requirements and approved data-quality strategy.

AI should not arbitrarily redefine quality requirements.

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

AI assists with:

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

Files include:

```text
data-generation.md
bronze-layer.md
silver-layer.md
gold-layer.md
dashboard.md
debugging.md
documentation.md
```

For meaningful interactions, the record should include:

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

A suggestion may be accepted when:

- it matches approved requirements,
- the reasoning is sound,
- it keeps the solution appropriately scoped,
- validation confirms the behavior.

## Changed

A suggestion may be modified when:

- the core idea is useful,
- but implementation details do not fit the environment or project design.

## Rejected

A suggestion should be rejected when:

- it violates the architecture,
- invents unsupported business requirements,
- unnecessarily expands scope,
- conflicts with the data model,
- cannot be validated,
- introduces unnecessary complexity.

The reason for important rejections should be documented.

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

AI assists with implementation, but responsibility remains with the engineer.

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

The intended reusable workflow is:

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
        ↓
Commit
```

This workflow can be adapted to production data engineering projects with stricter privacy, security, testing, review, and deployment controls.

---

# 27. Current Project Status

Current checkpoint:

```text
Checkpoint 1 — Planning & Cursor Context
```

Planning has been completed before generating implementation code.

The next checkpoint is:

```text
Checkpoint 2 — Synthetic Data Generation
```

No Bronze, Silver, Gold, or dashboard implementation should begin until the data-generation checkpoint has been validated.

---

# 28. Sections to Update During the Project

The following parts of this document must be revisited before final submission.

## What AI Helped With Most

**Status:** To be completed from actual project experience.

## What AI Got Wrong

**Status:** To be completed from actual Cursor interactions.

## What I Changed or Rejected

**Status:** To be completed from actual prompt history.

## Debugging Experience

**Status:** To be completed from actual issues encountered.

## Lessons Learned

**Status:** To be completed after the end-to-end pipeline is complete.

## What I Would Do Differently in Production

**Status:** To be finalized during reflection.

---

# 29. Planned Final Review

Before submission, this document should be reviewed against:

```text
ai-prompts/*
debugging-notes.md
reflection.md
final-ai-usage-summary.md
Git history
final implementation
```

Any statement describing AI usage should be supported by what actually happened during the project.