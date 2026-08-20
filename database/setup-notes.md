# Databricks Free Edition Bronze Setup

## Environment

This checkpoint targets Databricks Free Edition with Unity Catalog.

Existing source objects:

- Catalog: `ecommerce_sales`
- Source schema: `ecommerce_sales.raw`
- Volume: `ecommerce_sales.raw.source_files`

Source files:

```text
/Volumes/ecommerce_sales/raw/source_files/customers.csv
/Volumes/ecommerce_sales/raw/source_files/orders.csv
/Volumes/ecommerce_sales/raw/source_files/products.csv
```

Bronze target schema:

```text
ecommerce_sales.bronze
```

The source catalog, raw schema, Volume, and uploaded CSV files are prerequisites.
This checkpoint does not recreate or replace them.

## Minimal schema setup

Run `database/schema.sql` in a Databricks SQL editor or notebook SQL cell:

```sql
CREATE SCHEMA IF NOT EXISTS ecommerce_sales.bronze;
```

Each ingestion script also runs this idempotent statement so it can fail less
ambiguously when executed independently. The user running the scripts must have
permission to create the schema and tables in `ecommerce_sales`.

## Running Bronze ingestion

Attach Databricks compute and run these Python files:

1. `src/bronze/01_ingest_customers.py`
2. `src/bronze/02_ingest_orders.py`
3. `src/bronze/03_ingest_products.py`

The scripts are independent; this order is used only for a predictable manual
run. Each script:

1. Reads one CSV using `header=True` and `inferSchema=True`.
2. Checks the exact source header and expected physical row count.
3. prints the inferred source schema.
4. Adds only `_ingested_at`.
5. Overwrites the corresponding Delta table.
6. Reads the table count back and fails if it differs from the source count.
7. Prints the persisted Bronze schema and source/Bronze counts.

Databricks provides the active `spark` variable automatically to Python
notebooks and scripts running on attached compute. The ingestion files use that
environment-provided session directly; they do not create a `SparkSession` or
include a `get_spark()` helper. This keeps the scripts aligned with their
Databricks-only execution context.

## Tables and expected counts

| Source | Bronze Delta table | Source rows | Bronze rows |
|---|---|---:|---:|
| `customers.csv` | `ecommerce_sales.bronze.customers` | 10,000 | 10,000 |
| `orders.csv` | `ecommerce_sales.bronze.orders` | 100,000 | 100,000 |
| `products.csv` | `ecommerce_sales.bronze.products` | 500 | 500 |

These are validation expectations. They must be confirmed from actual
Databricks output after execution.

## Schema inference

The scripts intentionally do not cast source columns because this checkpoint
requires Spark CSV schema inference. Based on the generated CSV representation,
the expected logical inference is:

### Customers

```text
customer_id       integer
customer_name     string
email             string
country           string
signup_date       date
customer_segment  string
lifetime_value    numeric (commonly double or decimal, runtime-dependent)
_ingested_at      timestamp
```

### Orders

```text
order_id          integer
customer_id       integer
order_date        date
product_id        integer
quantity          integer
unit_price        numeric (commonly double or decimal, runtime-dependent)
total_amount      numeric (commonly double or decimal, runtime-dependent)
order_status      string
payment_date      date
_ingested_at      timestamp
```

### Products

```text
product_id        integer
product_name      string
category          string
price             numeric (commonly double or decimal, runtime-dependent)
cost              numeric (commonly double or decimal, runtime-dependent)
stock_quantity    integer
reorder_level     integer
_ingested_at      timestamp
```

## Source preservation and reruns

Bronze performs no cleaning, deduplication, filtering, NULL replacement,
foreign-key correction, or business-rule validation. The known NULL values,
invalid references, and duplicate IDs therefore remain in the Delta tables.
Those conditions are evaluated later in Silver, not in these scripts.

The tables use Delta overwrite mode with schema overwrite enabled. Re-running a
script replaces that table with the current source snapshot instead of
appending another copy. `_ingested_at` is refreshed on each run.

After running, the basic reconciliation query is:

```sql
SELECT 'customers' AS dataset, COUNT(*) AS bronze_rows
FROM ecommerce_sales.bronze.customers
UNION ALL
SELECT 'orders', COUNT(*)
FROM ecommerce_sales.bronze.orders
UNION ALL
SELECT 'products', COUNT(*)
FROM ecommerce_sales.bronze.products;
```

Expected result:

```text
customers  10000
orders     100000
products   500
```

## Free Edition considerations

- Volume paths are available from Databricks compute, not from the local Python
  environment in this repository.
- Databricks compute must be running for PySpark and Delta table writes; the
  platform supplies the active `spark` session automatically.
- Free Edition capacity and compute startup can be limited, but these dataset
  sizes do not require partitioning or optimization.
- SQL Warehouse features are not required for this checkpoint.
