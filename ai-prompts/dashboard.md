# AI Prompt History — Dashboard

## Interaction — Gold-only dashboard queries

### Prompt / task

I asked Cursor to create `dashboard_queries.sql` and `DASHBOARD_GUIDE.md` using
only the four existing Gold tables. The three required views were:

- Top 10 products by revenue;
- customer revenue distribution;
- customer segmentation.

I allowed one additional daily/weekly trend query but kept it optional for the
dashboard. I explicitly prohibited rebuilding business logic from Silver.

### AI response summary

Cursor created:

- a Top 10 product query for a bar chart;
- customer-level revenue output for a histogram;
- segment counts for a pie chart;
- an optional weekly revenue query for a line chart.

The guide records each query's purpose, Gold source, visualization type, field
mappings, filters, and interpretation.

### What I accepted

I accepted the simple Gold-only queries and the optional weekly trend. Keeping
the weekly filter explicit avoids mixing daily and weekly grains in one
ungrouped line.

### What I changed or rejected

No implementation correction was recorded for this checkpoint. I rejected
querying Bronze or Silver and did not add dashboard-side revenue or
segmentation logic.

### Validation status

Static checks confirmed that all four queries reference Gold tables only and
that the required visualization fields are present. The repository does not
record completed Databricks dashboard configuration or visual validation.
