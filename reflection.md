# Personal Reflection

I built this project as a small end-to-end Databricks Medallion pipeline rather
than as a collection of unrelated scripts. It starts with deterministic
synthetic customer, order, and product data, loads the CSV files into Bronze,
adds data-quality results in Silver, creates four Gold datasets, and finishes
with SQL and setup guidance for a dashboard. The technical pieces were useful,
but the more interesting part for me was learning how to work with Cursor
without treating its output as automatically correct.

One thing that became clear during the exercise was that giving Cursor more
text was not always better. At the beginning my prompts were very detailed
because the project decisions were still being established. The data-generation
prompt included exact row counts, defect counts, duplicate semantics, file
boundaries, and validation expectations. Once those decisions were written
into `requirements-analysis.md`, `design-notes.md`, `data-model.md`,
`data-quality-strategy.md`, and the Cursor workflow files, I did not need to
repeat everything in every prompt. Later prompts could be shorter and focused
on the active task because Cursor could read the repository context first.

That persistent context was probably the most useful part of the workflow. It
gave me somewhere to record decisions that should survive beyond one chat
message. It also made contradictions easier to notice. For example, the
approximate statement about “~700 problematic rows” did not match the explicit
defect counts. Instead of asking Cursor to make the numbers look right, I kept
the explicit counts, documented the difference, and generated only the defects
that were actually required. The same approach helped with duplicate IDs:
modifying 10 customer rows creates 10 duplicate groups, but a uniqueness check
correctly flags 20 physical rows. Writing that distinction down before Silver
made the later logic much easier to reason about.

I used short role prompts such as “Act as a senior Databricks data engineer,”
but I did not expect the role description to provide correctness. The useful
controls were the source files to read, the files Cursor was allowed to change,
the exact rules, the validation criteria, and a clear instruction to stop at
the end of the checkpoint. This prevented a Bronze request from turning into a
partial Silver implementation and kept each change small enough for me to
review.

Cursor saved me time on the mechanical parts of the project. It generated the
pandas and Faker data generator, repeated the Bronze ingestion pattern across
three sources, created focused Silver validation functions, wrote the Gold SQL,
and produced the dashboard queries and guide. It was especially helpful where
the work was repetitive but still needed to stay consistent, such as applying
the same rerun-safe Delta write pattern or adding the same set of quality
columns to multiple datasets. It also helped turn decisions into documentation
while those decisions were still fresh.

At the same time, I still needed to understand and challenge what it produced.
The first Bronze scripts included `SparkSession.getActiveSession()`. That is a
reasonable generic Spark pattern, but it was unnecessary for these scripts
because they run in Databricks, where `spark` is already provided. I asked
Cursor to remove the lookup and the helper around it. The resulting code was
smaller and more honest about its execution environment. That was a useful
example of code being technically plausible without being the best fit for the
project.

The Silver imports were a different kind of decision. The validation filenames
begin with numbers, so normal static Python import syntax was not available. I
considered using Databricks `%run`, but the files were reusable Python modules,
not notebooks that needed to share a namespace. Cursor used
`importlib.import_module()`, and I kept that approach after it worked in
Databricks. I would not choose numeric module names for a new production
package, but given the required repository structure, testing the import-based
solution was better than changing to `%run` simply because it was
Databricks-specific.

I deliberately kept Bronze simple. Its job is to preserve what arrived, not to
make the data look clean. The NULL emails, missing foreign keys, orphan
references, and duplicate IDs had to survive so Silver could prove that it
detected them. Adding cleaning to Bronze would have made the pipeline appear
healthier while removing the evidence needed to test it. The only added
business-independent field is `_ingested_at`, and the main validation is that
the source and Bronze physical row counts match.

Separating Silver quality checks into five modules helped me understand the
difference between a quality rule and pipeline orchestration. Completeness,
uniqueness, type validation, referential integrity, and business logic each
return a DataFrame with one dimension result. The final Silver script composes
them, creates specific failure reasons, derives the overall PASS or FAIL, and
writes the tables. This structure made individual rules easier to inspect. It
also exposed an important referential-integrity detail: customer IDs are
intentionally duplicated, so checking orders against the raw customer rows
could multiply orders. Using distinct parent IDs avoids that problem without
deleting the duplicate customer records.

Validation mattered throughout the project because generated code can look
convincing even when its assumptions are wrong. The data generator asserts
exact row counts and defect counts before writing files. Bronze compares source
and table counts. Silver checks row preservation and prints dimension-level
results. Gold checks table grains and reconciles customer, product,
segmentation, and trend populations. I also learned to distinguish static
review from runtime evidence. The Silver module imports were exercised in
Databricks, while the repository does not record a complete Gold rerun after
the path fix, so I should not present that rerun as completed.

The Gold path issue reinforced the same point. Cursor initially used
`Path(__file__)`, which is normal in a Python script, but Databricks notebooks
do not define `__file__`. The actual runtime raised a `NameError`, so I changed
the runner to use `Path.cwd()`. That was not a complicated bug, but it was a
good reminder that local Python assumptions need to be checked in the target
platform.

I also tried not to hide ambiguous business rules inside code. The original
requirements did not define which order statuses counted as revenue, what
`lifetime_value_actual` meant, or where the High-Value threshold should be.
Those questions stayed open until I made explicit decisions for the Gold
checkpoint: only Completed, quality-passing orders contribute to revenue;
`lifetime_value_actual` is the sum of that revenue; and High-Value customers
are the top revenue quintile. Customers with no qualifying orders are retained
so they can be classified as Inactive. Supplying those decisions directly was
better than allowing Cursor to choose rules that merely sounded reasonable.

For a real production pipeline, I would change several things. I would use
conventional Python package and module names, explicit source schemas, external
environment configuration, richer run and lineage metadata, automated tests,
and deployment checks. I would choose an incremental ingestion strategy based
on the source system instead of overwriting a single snapshot. I would also
persist and monitor data-quality measurements, define ownership and alerting,
and test notebook filesystem behavior before depending on relative paths.
Security would need stronger access controls and managed secrets, and I would
not provide an AI tool with real customer data, credentials, confidential
records, or unnecessary infrastructure details. Synthetic schemas and minimal
reproducible examples would usually be enough.

My main takeaway is that Cursor was most effective as an engineering partner
when I gave it boundaries and evidence. It was good at producing a first
implementation, repeating consistent patterns, and helping me document the
reasoning. My role was still to define the business decisions, understand the
code, run it in the actual environment, question generic suggestions, and be
honest about what had and had not been validated. That felt much more useful
than treating AI as a one-prompt code generator.
