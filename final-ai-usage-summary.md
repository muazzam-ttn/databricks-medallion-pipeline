# Final AI Usage Summary

## Primary AI Tool

I used Cursor as the primary AI tool for this project. I used it inside the
repository so it could work with the requirements, design, data model,
implementation, and documentation together rather than relying on isolated
prompts.

## Where I Used AI

Cursor supported the project from planning through implementation:

- structuring requirements, assumptions, edge cases, and acceptance criteria,
- designing the Medallion layer responsibilities,
- generating deterministic synthetic data and validation assertions,
- implementing Bronze ingestion, Silver quality checks, and Gold SQL,
- preparing Gold-only dashboard queries and setup guidance,
- reviewing consistency and helping write technical documentation.

I divided the work into checkpoints and gave each prompt a narrow scope and a
stop condition. I also used short role prompts, but the repository context and
explicit validation criteria were more important than the role wording.

## How I Supplied Context

Persistent context was stored in the main planning documents and under
`tool-specific/cursor-workflow/`. Each implementation prompt told Cursor which
documents to read before editing.

My early prompts were detailed because the contracts were still being defined.
Later prompts became shorter and more targeted because row counts, quality
rules, layer boundaries, and naming decisions were already available in the
repository. Prompt history is retained under `ai-prompts/`.

## Output I Accepted

Examples of accepted AI-assisted work include:

- deterministic pandas/Faker generation with fixed seeds and exact defect
  assertions,
- fixed-row duplicate injection with documented duplicate-group semantics,
- source-preserving Bronze Delta writes and row-count reconciliation,
- reusable Silver DataFrame validation modules,
- distinct parent-key lookups that avoid multiplying Orders,
- specific Silver failure reasons instead of only a generic FAIL result,
- Gold SQL using quality-passing Completed orders,
- Gold grain and population checks,
- dashboard queries that consume Gold tables only.

I accepted these outputs after checking them against the approved requirements
and their expected behavior.

## Output I Changed or Rejected

I removed `SparkSession.getActiveSession()` from the Bronze scripts because
Databricks already supplies `spark`.

I considered replacing the Silver Python imports with `%run`, but retained
`importlib.import_module()` after the import-based approach worked in
Databricks. I also replaced `Path(__file__)` in the Gold runner after the
Databricks notebook raised a `NameError`, using the notebook working directory
instead.

I rejected adding unspecified defects simply to reach the guide's approximate
problem-row count. I also avoided unrequested malformed types, business-rule
failures, Bronze cleaning, and dashboard logic that duplicated Gold
transformations.

## Validation Approach

I treated AI output as a draft until it was reviewed or executed.

The data generator validates exact rows, columns, NULLs, orphans, duplicates,
and baseline business values. Bronze compares source and persisted counts.
Silver preserves rows, records quality flags and reasons, and prints quality
summaries. Gold includes grain and reconciliation checks. Dashboard SQL was
checked to confirm that it references only Gold tables.

I also kept runtime claims separate from static checks. The Silver module
imports and orchestration were validated in Databricks. The repository does not
record a complete Gold rerun after the `__file__` correction, so I have not
claimed that result.

## Responsible AI and Privacy

The project uses synthetic customer data. I did not provide Cursor with real
customer PII, production credentials, tokens, private keys, or confidential
datasets.

In production I would share only the minimum necessary context, preferring
sanitized schemas, redacted errors, synthetic examples, and small reproducible
cases. Secrets would remain in managed secret storage and production access
would follow normal authorization and review controls.

## Main Lesson

My main lesson was that AI was most useful when I supplied durable context,
clear boundaries, and evidence-based validation. Cursor saved time on initial
implementations and repeated patterns, but I still needed to define ambiguous
business rules, challenge generic suggestions, and test Databricks-specific
assumptions. I found it more effective as an engineering partner than as a
one-prompt code generator.
