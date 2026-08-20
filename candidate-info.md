# Candidate Information

**Name:** Muazzam Sayyed  
**Role:** SSE  
**Primary Technology Stack:** Python / PySpark, SQL, Databricks  
**Primary AI Tool Used:** Cursor  
**Project Option Selected:** Data Pipeline — Medallion Architecture  
**Assessment Start Date:** [2026-08-14]  
**Submission Date:** [To be completed at submission]

---

## Tools & Environment

### Databricks

**Environment:** Free Edition

Catalog:
ecommerce_sales

Source schema:
raw

Source volume:
source_files

Source base path:
/Volumes/ecommerce_sales/raw/source_files/

### Languages

- Python
- PySpark
- SQL

### Libraries / Technologies

- Apache Spark / PySpark
- Delta Lake
- pandas
- Faker

### AI Tool

- Cursor

### Version Control

- Git
- Repository: `databricks-medallion-pipeline`

---

## Project Summary

This project implements an AI-assisted Databricks Medallion Architecture pipeline for synthetic e-commerce sales data.

The pipeline processes three source datasets:

- Customers
- Orders
- Products

The architecture follows:

```text
Synthetic CSV Data
        ↓
Bronze
        ↓
Silver
        ↓
Gold
        ↓
Databricks SQL Dashboard
```

The exercise focuses not only on delivering a working data pipeline, but also on demonstrating how AI is used responsibly and effectively throughout the data engineering lifecycle.

The project will therefore include evidence of AI-assisted work across:

- requirement analysis,
- architecture and data modeling,
- synthetic data generation,
- Bronze ingestion,
- Silver data-quality validation,
- Gold aggregation,
- dashboard development,
- testing,
- debugging,
- documentation,
- reflection.

---

## Dataset Summary

The project generates only synthetic data.

### Customers

Approximately:

```text
10,000 customers
```

### Orders

Approximately:

```text
100,000 orders
```

### Products

Approximately:

```text
500 products
```

Intentional data-quality issues will be introduced so the Silver layer can demonstrate:

- completeness validation,
- uniqueness validation,
- referential-integrity validation,
- type validation,
- business-logic validation.

No real customer PII will be used.

---

## Setup Summary

The planned workflow is:

```text
1. Generate synthetic CSV files locally.
2. Validate that intentional quality issues exist.
3. Make the files accessible to Databricks.
4. Ingest the source files into Bronze Delta tables.
5. Apply Silver data-quality validation without deleting bad rows.
6. Generate data-quality metrics.
7. Build Gold analytical aggregations.
8. Create Databricks SQL dashboard queries and visualizations.
9. Perform end-to-end validation.
10. Complete prompt history, debugging notes, reflection, and AI usage documentation.
```

Detailed setup and execution instructions will be maintained in:

```text
README.md
database/setup-notes.md
```

---

## Current Status

Current project phase:

```text
Checkpoint 1 — Planning & Cursor Context
```

Planning artifacts currently prepared:

```text
requirements-analysis.md
design-notes.md
data-quality-strategy.md
data-model.md

tool-specific/cursor-workflow/project-context.md
tool-specific/cursor-workflow/spec.md
tool-specific/cursor-workflow/cursor-rules-or-instructions.md
tool-specific/cursor-workflow/task-breakdown.md
```

Pipeline implementation has intentionally not started yet.

The next implementation checkpoint will be:

```text
Checkpoint 2 — Synthetic Data Generation
```

after Checkpoint 1 has been reviewed and accepted.