"""Ingest the product CSV into the Bronze Delta table."""

from pyspark.sql import DataFrame
from pyspark.sql.functions import current_timestamp

SOURCE_PATH = "/Volumes/ecommerce_sales/raw/source_files/products.csv"
TARGET_SCHEMA = "ecommerce_sales.bronze"
TARGET_TABLE = f"{TARGET_SCHEMA}.products"
EXPECTED_ROW_COUNT = 500
EXPECTED_COLUMNS = [
    "product_id",
    "product_name",
    "category",
    "price",
    "cost",
    "stock_quantity",
    "reorder_level",
]


def validate_source(source_df: DataFrame) -> int:
    """Validate structural source expectations without evaluating data quality."""
    if source_df.columns != EXPECTED_COLUMNS:
        raise ValueError(
            "Product source columns do not match the expected CSV contract. "
            f"Expected {EXPECTED_COLUMNS}, found {source_df.columns}."
        )

    source_count = source_df.count()
    if source_count != EXPECTED_ROW_COUNT:
        raise ValueError(
            f"Product source must contain {EXPECTED_ROW_COUNT:,} rows; "
            f"found {source_count:,}."
        )
    return source_count


def ingest_products() -> None:
    """Overwrite the Bronze product table with the current source snapshot."""
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {TARGET_SCHEMA}")

    source_df = (
        spark.read.option("header", True)
        .option("inferSchema", True)
        .csv(SOURCE_PATH)
    )
    source_count = validate_source(source_df)

    print(f"Inferred schema for {SOURCE_PATH}:")
    source_df.printSchema()

    bronze_df = source_df.withColumn("_ingested_at", current_timestamp())
    (
        bronze_df.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(TARGET_TABLE)
    )

    bronze_count = spark.table(TARGET_TABLE).count()
    if bronze_count != source_count:
        raise RuntimeError(
            f"Row preservation failed for {TARGET_TABLE}: "
            f"source={source_count:,}, bronze={bronze_count:,}."
        )

    print(
        f"Product ingestion complete: source_rows={source_count:,}, "
        f"bronze_rows={bronze_count:,}, table={TARGET_TABLE}"
    )
    spark.table(TARGET_TABLE).printSchema()


if __name__ == "__main__":
    ingest_products()
