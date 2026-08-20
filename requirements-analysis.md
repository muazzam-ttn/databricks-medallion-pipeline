# Requirement Analysis

## 1. Problem Statement

The objective of this project is to design and implement an AI-assisted Databricks Medallion Architecture pipeline for synthetic e-commerce sales data.

The source data consists of three daily CSV datasets:

- Customers
- Orders
- Products

The pipeline will ingest these files into a Bronze layer without modifying the source data, validate and flag data quality problems in a Silver layer, transform valid business data into analytical Gold tables, and expose stakeholder-oriented SQL queries through a Databricks SQL dashboard.

The exercise is not focused only on producing working code. It must also demonstrate a structured AI-assisted data engineering workflow covering requirement analysis, design, implementation, validation, testing, debugging, documentation, and reflection.

All project data will be synthetically generated. No real customer personally identifiable information (PII) will be used.

---

## 2. Project Scope

### In Scope

The project will include:

1. Synthetic data generation for customers, orders, and products.
2. Deliberate generation of specified data quality issues.
3. Bronze ingestion into Databricks.
4. Silver data quality validation and row-level quality flags.
5. Data quality metrics reporting.
6. Gold analytical aggregations.
7. Databricks SQL queries and dashboard visualizations.
8. Database/schema setup scripts.
9. At least one meaningful validation or testing tier.
10. Documentation of AI usage, design decisions, debugging, testing, and reflection.

### Out of Scope

Unless required later, the following are intentionally excluded:

- Real customer or production data.
- Streaming ingestion.
- Change Data Capture.
- Complex orchestration frameworks.
- Production CI/CD pipelines.
- Advanced infrastructure-as-code.
- Performance benchmarking at production scale.
- Machine learning or recommendation models.
- Complex dimensional modeling beyond the required Gold outputs.

The project is intentionally kept within the expected 20–25 focused development-hour scope.

---

# 3. Functional Requirements

## FR-01 — Generate Synthetic Customer Data

The system must generate a `customers.csv` file representing approximately 10,000 customer records.

Required fields:

- `customer_id` — INT, intended primary key
- `customer_name` — STRING
- `email` — STRING
- `country` — STRING
- `signup_date` — DATE
- `customer_segment` — STRING
- `lifetime_value` — DECIMAL

Allowed customer segments:

- Premium
- Standard
- Basic

The generated values should be realistic enough for data engineering testing while remaining fully synthetic.

### Intentional Quality Issues

The generated customer data must include:

- 50 rows with NULL email values.
- 10 duplicate `customer_id` occurrences.

These issues must be introduced deliberately and documented in `DATA_GENERATION_NOTES.md`.

---

## FR-02 — Generate Synthetic Product Data

The system must generate a `products.csv` file representing approximately 500 products.

Required fields:

- `product_id` — INT, intended primary key
- `product_name` — STRING
- `category` — STRING
- `price` — DECIMAL
- `cost` — DECIMAL
- `stock_quantity` — INT
- `reorder_level` — INT

Product records must be synthetically generated and suitable for joining with order data.

---

## FR-03 — Generate Synthetic Order Data

The system must generate an `orders.csv` file representing approximately 100,000 order records.

Required fields:

- `order_id` — INT, intended primary key
- `customer_id` — INT, intended foreign key
- `order_date` — DATE
- `product_id` — INT, intended foreign key
- `quantity` — INT
- `unit_price` — DECIMAL
- `total_amount` — DECIMAL
- `order_status` — STRING
- `payment_date` — DATE, nullable

Allowed order statuses:

- Pending
- Completed
- Cancelled

### Intentional Quality Issues

The generated order data must include:

- 100 rows with NULL `customer_id`.
- 200 rows with NULL `product_id`.
- 50 rows with a `customer_id` that does not exist in the customers dataset.
- 30 rows with a `product_id` that does not exist in the products dataset.
- 20 duplicate `order_id` occurrences.

The generation process must deliberately create these conditions and document how they were introduced.

---

## FR-04 — Bronze Customer Ingestion

The pipeline must read `customers.csv` from the configured Databricks-accessible storage location and persist it into a Bronze customer table.

Bronze ingestion must:

- Preserve source records without business cleaning.
- Preserve records containing intentional quality issues.
- Infer or apply the source-compatible schema.
- Capture the number of records ingested.
- Capture an ingestion timestamp or equivalent ingestion metadata.

Bronze must not remove invalid or duplicate records.

---

## FR-05 — Bronze Order Ingestion

The pipeline must ingest `orders.csv` into a Bronze order table using the same raw-ingestion principles.

All intentional quality problems must remain available for Silver validation.

---

## FR-06 — Bronze Product Ingestion

The pipeline must ingest `products.csv` into a Bronze product table.

No business transformations should be performed in the Bronze layer.

---

## FR-07 — Completeness Validation

The Silver layer must identify records with missing values in fields considered mandatory for downstream processing.

At minimum:

### Customers

Validate:

- `email`

### Orders

Validate:

- `customer_id`
- `product_id`

Rows that fail completeness validation must be retained and flagged rather than deleted.

---

## FR-08 — Uniqueness Validation

The Silver layer must detect violations of intended primary-key uniqueness.

At minimum:

### Customers

Validate:

- duplicate `customer_id`

### Orders

Validate:

- duplicate `order_id`

Duplicate records must remain available for analysis and must be flagged as failing the appropriate validation.

---

## FR-09 — Referential Integrity Validation

Orders must be validated against parent datasets.

Checks must include:

- Non-null `customer_id` exists in customers.
- Non-null `product_id` exists in products.

Orders referencing nonexistent parent records must be retained and flagged.

NULL foreign keys should primarily be classified as completeness failures rather than being double-counted as referential-integrity failures unless explicitly documented otherwise.

---

## FR-10 — Type Validation

The Silver layer should validate whether source values conform to their expected logical types.

Examples include:

- Numeric identifiers are valid integers.
- Quantity is numeric.
- Monetary values are numeric/decimal-compatible.
- Date fields are parseable as dates.

Rows failing type validation must be flagged.

Because CSV is inherently text-based before parsing, the implementation strategy for detecting malformed values must be defined during detailed design.

---

## FR-11 — Business Logic Validation

The Silver layer should perform a limited set of business-rule validations to demonstrate additional quality depth without over-expanding scope.

Potential rules include:

- `quantity > 0`
- `unit_price >= 0`
- `total_amount >= 0`
- `price >= 0`
- `cost >= 0`
- `stock_quantity >= 0`
- `reorder_level >= 0`
- `customer_segment` belongs to the accepted domain.
- `order_status` belongs to the accepted domain.

The exact rule set will be finalized in `data-quality-strategy.md`.

---

## FR-12 — Row-Level Quality Result

Silver records must contain a `quality_check_result` column or equivalent row-level quality indicator.

The indicator must make it possible to distinguish records that:

- passed validation, or
- failed one or more validations.

The implementation should retain enough information to understand why a row failed.

A single generic `"FAILED"` value without failure details should be avoided if a simple, readable mechanism can record failed check names.

---

## FR-13 — Preserve Invalid Records

Silver processing must not silently delete data-quality failures.

Invalid records must remain inspectable so that:

- intentional issues can be demonstrated,
- quality metrics can be reconciled,
- the reviewer can verify that validation works.

Gold-layer inclusion rules for failed records must be explicitly documented.

---

## FR-14 — Data Quality Metrics Report

The pipeline must produce data quality metrics showing the percentage of records passing each quality check.

At minimum, report metrics for:

- Completeness
- Uniqueness
- Referential integrity

Additional metrics should be produced for:

- Type validation
- Business logic validation

Metrics should make it possible to determine:

- records evaluated,
- records passed,
- records failed,
- pass percentage.

---

## FR-15 — Gold: Sales by Product

Create a business-ready Gold dataset containing:

- `product_id`
- `product_name`
- `category`
- `total_orders`
- `total_revenue`
- `avg_order_value`

Aggregation calculations must be reproducible from Silver data.

---

## FR-16 — Gold: Revenue by Customer

Create a Gold dataset containing:

- `customer_id`
- `customer_name`
- `customer_segment`
- `total_orders`
- `total_revenue`
- `avg_order_value`
- `lifetime_value_actual`

The definition of `lifetime_value_actual` must be explicitly documented.

Initial interpretation:

`lifetime_value_actual` represents revenue calculated from the generated order history rather than blindly copying the source customer's synthetic `lifetime_value` attribute.

This assumption must be validated during Gold-layer design.

---

## FR-17 — Gold: Customer Segmentation

Create a Gold aggregation containing:

- `segment_type`
- `customer_count`
- `avg_revenue`
- `total_revenue`

Required segment labels:

- High-Value
- Repeat
- One-Time
- Inactive

The exact classification logic is not specified by the exercise and therefore must be defined before implementation.

The classification logic must be:

- deterministic,
- understandable,
- documented,
- based on available customer/order data.

---

## FR-18 — Gold: Daily/Weekly Sales Trends

Create `ecommerce_sales.gold.daily_weekly_trends` from qualifying completed
Silver orders.

Required columns:

```text
period_type
period_start
total_orders
total_revenue
avg_order_value
```

The dataset must:

- include both `DAILY` and `WEEKLY` period types,
- use the calendar date as the daily `period_start`,
- use the Monday week start as the weekly `period_start`,
- include only orders with `quality_check_result = 'PASS'`,
- include only `Completed` orders,
- have one row per `period_type` and `period_start`,
- support downstream trend analysis and optional dashboard extensions.

---

## FR-19 — Dashboard Queries

The project must provide SQL queries for at least three stakeholder-facing visualizations.

Required visualizations:

1. Top 10 products by revenue — bar chart.
2. Customer revenue distribution — histogram.
3. Customer segmentation — pie chart.

The SQL used by the dashboard must be stored in:

`src/dashboard/dashboard_queries.sql`

---

## FR-20 — Dashboard Documentation

`DASHBOARD_GUIDE.md` must explain how to create or reproduce the dashboard in Databricks SQL.

It should document:

- source Gold table/query,
- visualization type,
- relevant X/Y or category/value fields,
- any filters,
- expected business interpretation.

---

## FR-21 — Database Setup

The repository must contain sufficient database/schema setup instructions to recreate the required structures.

At minimum:

- schema/database creation statements,
- expected table names,
- setup order,
- storage/path assumptions.

---

## FR-22 — Testing and Validation

The project must implement at least one meaningful testing tier.

Tests must verify behavior rather than merely confirm that code executes.

At minimum, the validation strategy should demonstrate that the deliberately seeded data-quality problems are detected.

Expected test scenarios include verifying detection of:

- NULL customer emails,
- NULL order customer IDs,
- NULL product IDs,
- duplicate customer IDs,
- duplicate order IDs,
- nonexistent customer references,
- nonexistent product references.

Where practical, expected issue counts should be compared against detected counts.

---

## FR-23 — Input Validation and Error Handling

Pipeline scripts should handle obvious operational failures clearly.

Examples:

- missing source file,
- unreadable input path,
- missing required columns,
- unexpected schema,
- failed table write.

Failures should produce understandable error messages rather than silently continuing.

The implementation should remain lightweight and appropriate for the exercise scope.

---

## FR-24 — AI Prompt History

AI interactions must be documented by activity.

For major interactions, documentation should include:

- prompt text or meaningful summary,
- AI response summary,
- suggestions accepted,
- suggestions modified,
- suggestions rejected,
- reasoning behind those decisions,
- validation performed before accepting AI-generated work.

Prompt history should demonstrate iteration rather than one-shot generation.

---

## FR-25 — AI Workflow Documentation

`tool-workflow.md` must describe how AI was used across:

- requirement analysis,
- project context setting,
- pipeline design,
- Python/PySpark/SQL generation,
- validation,
- testing,
- debugging,
- data quality,
- documentation,
- reflection.

It must also identify information that should not be unnecessarily shared with external AI systems in real production environments.

Examples include:

- real customer PII,
- production credentials,
- secrets and tokens,
- confidential datasets,
- sensitive business information,
- internal access details unless necessary and approved.

---

# 4. Non-Functional Requirements

## NFR-01 — Readability

Code should be understandable to another data engineer without requiring AI-generated explanations.

Scripts should use:

- descriptive names,
- consistent formatting,
- concise comments for non-obvious logic,
- small focused functions where useful.

---

## NFR-02 — Maintainability

Repeated logic should be avoided where a small reusable function provides clear value.

However, the project should not introduce unnecessary abstraction or framework complexity merely to appear sophisticated.

---

## NFR-03 — Reproducibility

A reviewer should be able to understand how to recreate the pipeline using the repository documentation.

Generation should preferably be reproducible through a fixed random seed where doing so does not conflict with the exercise requirements.

---

## NFR-04 — Traceability

Intentional bad data must be traceable from:

data generation  
→ Bronze  
→ Silver validation  
→ quality metrics.

This makes it possible to prove that the validation logic actually detects the known problems.

---

## NFR-05 — Data Preservation

Bronze must preserve source data.

Silver must preserve failing records while adding validation information.

No quality issue should disappear merely because processing continued downstream.

---

## NFR-06 — Explainability

Quality rules, segmentation logic, aggregation logic, and major design decisions should be simple enough to explain during a reviewer or mentor discussion.

---

## NFR-07 — Environment Portability

The solution should avoid hard-coding environment-specific locations wherever a simple configurable path can be used.

It should be possible to adjust input/catalog/schema locations without rewriting core transformation logic.

---

## NFR-08 — Responsible AI Usage

The project must demonstrate that AI-generated outputs are reviewed and validated before acceptance.

AI should assist engineering decisions but should not be treated as the source of truth for:

- data correctness,
- SQL correctness,
- quality thresholds,
- business definitions,
- environment configuration.

---

## NFR-09 — Privacy

Only synthetic data will be generated.

Names and email addresses generated for the project must be fictitious.

No production or personal customer information should be introduced into the repository or AI prompts.

---

## NFR-10 — Scope Discipline

The implementation should prioritize:

1. correct requirements,
2. working end-to-end pipeline,
3. quality validation,
4. testing,
5. documentation,
6. visible AI workflow.

Optional complexity should not reduce the quality of those core areas.

---

# 5. Assumptions

The following assumptions are currently being made and should be validated during design or implementation.

### A-01 — Batch Processing

The source files represent batch ingestion rather than streaming events.

The pipeline therefore processes CSV files as batch datasets.

### A-02 — Single Daily Snapshot for Exercise

Although the business context describes daily ingestion, the exercise does not require implementing multi-day incremental ingestion unless explicitly needed.

The initial version will process the generated datasets as one exercise batch.

### A-03 — Delta Tables

Bronze, Silver, and Gold persisted datasets will use Delta tables because the project uses Databricks and Delta Lake.

### A-04 — Synthetic Data Only

All names, emails, and customer-related attributes are generated.

No real PII will be copied into the project.

### A-05 — Invalid Silver Rows Are Retained

Rows failing Silver validations remain in Silver with quality flags.

### A-06 — Gold Uses Valid Records

Gold aggregations will normally be based only on records considered suitable for analytics.

The exact inclusion criteria will be defined in the Silver/Gold design.

### A-07 — Null Foreign Keys

NULL `customer_id` and `product_id` values will count primarily as completeness failures.

Referential integrity will evaluate non-null foreign-key values against the corresponding parent dataset.

This avoids inflating multiple failure categories for the same missing value unless multi-rule failure reporting is intentionally desired.

### A-08 — Product Data Contains No Mandatory Seeded Quality Problems

The exercise specifies deliberate issues in customers and orders but does not define required bad rows in products.

Products will therefore be generated valid by default.

### A-09 — Intentional Issue Counts Refer to Seeded Conditions

The specified figures represent deliberate quality conditions introduced into the synthetic data.

Care must be taken when generating records so accidental problems do not distort the expected counts.

### A-10 — Duplicate Meaning

A duplicate primary-key issue means multiple records share the same intended primary-key value.

It does not necessarily mean the entire physical row is byte-for-byte identical.

This definition will be fixed during data-generation design.

---

# 6. Edge Cases

## EC-01 — Duplicate Parent Keys During Referential Validation

Because customers intentionally contain duplicate `customer_id` values, joining orders directly against the raw customer table could multiply order records.

Referential-integrity validation must therefore validate existence against a distinct set of parent IDs rather than naïvely joining against duplicate parent rows.

---

## EC-02 — Duplicate Product/Customer Dimension Rows in Gold Joins

Gold joins must avoid accidental row multiplication if an upstream parent dataset contains duplicate identifiers.

The valid/analytics-ready representation used by Gold must therefore have a deterministic uniqueness strategy.

---

## EC-03 — NULL vs Invalid Foreign Key

A NULL foreign key represents missing information.

A non-null foreign key that does not exist in its parent dataset represents an orphan reference.

These should remain distinguishable in quality reporting.

---

## EC-04 — CSV Type Inference

Malformed numeric or date values may cause schema inference to:

- infer an unexpected type,
- return NULL after parsing,
- treat the entire field as string.

The implementation must ensure type validation can still identify malformed values.

---

## EC-05 — Duplicate Issue Counts

When 10 duplicate customer IDs or 20 duplicate order IDs are generated, the interpretation of the count must be documented.

For example:

- 10 additional duplicate rows, or
- 10 IDs involved in duplication.

We should use one definition consistently and test against it.

---

## EC-06 — Overlapping Data Quality Failures

A single row may fail multiple checks.

For example, an order could theoretically have:

- NULL customer ID,
- invalid product ID,
- invalid quantity.

The row-level quality representation must support multiple failure reasons or define an explicit prioritization strategy.

---

## EC-07 — Payment Date Rules

`payment_date` is intentionally nullable.

A NULL payment date therefore cannot automatically be treated as a completeness issue.

If business validation is added, expected payment-date behavior should depend on `order_status`.

---

## EC-08 — Cancelled/Pending Revenue

It is currently unclear whether Pending and Cancelled orders should contribute to Gold revenue.

The Gold design must explicitly define which statuses contribute to analytical revenue.

---

## EC-09 — Order Amount Consistency

If:

`total_amount = quantity × unit_price`

then floating/decimal precision may produce small comparison differences.

Any business-rule validation should therefore use appropriate decimal handling rather than unsafe floating-point equality.

---

## EC-10 — Customer With No Orders

Customers without orders must still be considered when producing the `Inactive` segmentation category.

An inner join between customers and orders would incorrectly remove them.

---

## EC-11 — Revenue Distribution

A customer revenue histogram requires individual customer revenue values rather than only pre-aggregated segment totals.

The dashboard query should therefore use the Revenue by Customer Gold table.

---

## EC-12 — Re-running the Pipeline

Development runs will likely occur repeatedly.

Table creation and writes should therefore have predictable rerun behavior and should not accidentally double the dataset.

The exact overwrite/idempotency approach will be defined during design.

---

# 7. Clarifications Needed

The following items are either ambiguous in the guide or depend on the chosen Databricks environment.

## C-01 — Databricks Environment

Need to confirm:

- Databricks Community Edition / Free Edition or another workspace?
- Unity Catalog available?
- DBFS access available?
- SQL Warehouse available for dashboard development?

This will affect storage paths, table naming, and dashboard setup instructions.

---

## C-02 — Primary AI Tool

Need to confirm the tool that should be documented as primary:

- Cursor,
- Claude,
- another approved tool.

If Cursor is used, the participant guide additionally expects evidence such as:

- project context,
- specification,
- Cursor rules/instructions,
- task breakdown.

---

## C-03 — Repository Location

Need to confirm whether development will begin in:

- an existing local repository,
- a new local Git repository,
- an empty GitHub repository.

---

## C-04 — Number of Quality Checks

The guide contains slightly different descriptions:

- detailed Silver core logic explicitly describes completeness, uniqueness, and referential integrity;
- acceptance criteria refer to four quality checks;
- required repository structure contains scripts for five categories:
  - completeness,
  - uniqueness,
  - type validation,
  - referential integrity,
  - business logic.

Working interpretation:

- Mandatory core: completeness, uniqueness, referential integrity.
- Additional implementation depth: type validation and business logic.

This should remain documented rather than silently treated as an unambiguous requirement.

---

## C-05 — Gold Revenue Status

Need to decide which order statuses contribute to:

- total revenue,
- average order value,
- customer lifetime revenue.

Recommended question to resolve during Gold design:

Should revenue include only `Completed` orders, or all orders except `Cancelled`?

---

## C-06 — Customer Segmentation Rules

The required labels are provided but the thresholds are not.

Need to define deterministic logic for:

- High-Value
- Repeat
- One-Time
- Inactive

This should be a documented project decision rather than an AI-invented rule presented as a supplied business requirement.

---

## C-07 — `lifetime_value_actual`

The required Revenue by Customer output contains `lifetime_value_actual`, but the precise formula is not specified.

Need to confirm or define whether it means:

- completed-order revenue,
- all non-cancelled revenue,
- total historical generated order amount,
- another business metric.

---

## C-08 — Quality Metrics Storage

The guide requires a quality metrics report but does not mandate its physical representation.

Options include:

- Delta quality metrics table,
- generated DataFrame displayed/logged during execution,
- persisted report output.

A persisted Delta metrics table is likely the most useful approach, but this should be confirmed during design rather than treated as a requirement.

---

# 8. Initial Acceptance Criteria

The project will be considered functionally complete when:

- [ ] Three synthetic CSV datasets are generated.
- [ ] Required intentional quality issues are present.
- [ ] Data-generation methodology is documented.
- [ ] All three datasets are ingested successfully into Bronze.
- [ ] Bronze retains raw problematic records.
- [ ] Ingestion row counts and timestamps are captured.
- [ ] Silver performs mandatory completeness checks.
- [ ] Silver performs mandatory uniqueness checks.
- [ ] Silver performs mandatory referential-integrity checks.
- [ ] Type validation is implemented.
- [ ] Selected business-logic validations are implemented.
- [ ] Invalid rows are flagged rather than discarded.
- [ ] Quality metrics show pass/fail percentages.
- [ ] Tests demonstrate that known seeded issues are detected.
- [ ] Sales by Product Gold table is correct.
- [ ] Revenue by Customer Gold table is correct.
- [ ] Customer Segmentation Gold table is correct.
- [ ] Daily/Weekly Sales Trends Gold table is correct.
- [ ] Dashboard SQL includes at least three required visualizations.
- [ ] Dashboard creation/configuration is documented.
- [ ] Database setup instructions are present.
- [ ] README supports end-to-end execution.
- [ ] AI prompt history documents major iterations and decisions.
- [ ] Testing and debugging evidence is documented.
- [ ] Reflection and final AI usage summary are completed.

---

# 9. Success Criteria for the AI-Assisted Workflow

Beyond pipeline correctness, successful completion should demonstrate that AI was used as an engineering assistant rather than an unchecked code generator.

Evidence should show that I:

1. Provided AI with sufficient project context before requesting implementation.
2. Broke work into focused tasks rather than asking for the entire project at once.
3. Reviewed AI-generated logic before accepting it.
4. Tested important assumptions and generated code.
5. Corrected or rejected suggestions that did not match the project requirements.
6. Used AI during debugging without accepting explanations without validation.
7. Recorded meaningful prompt iterations.
8. Can explain the final architecture and implementation without depending on AI.
9. Avoided sharing real customer data, credentials, secrets, or unnecessary sensitive information.
10. Developed a workflow that could be adapted to a real production data engineering project.