"""Reusable intended-key uniqueness checks for Bronze DataFrames."""

from pyspark.sql import DataFrame
from pyspark.sql.functions import col, count, lit
from pyspark.sql.window import Window


def _with_uniqueness_result(source_df: DataFrame, key_column: str) -> DataFrame:
    """Flag every row in a duplicate-key group without removing any row."""
    if key_column not in source_df.columns:
        raise ValueError(f"Required uniqueness key is missing: {key_column}")

    key_window = Window.partitionBy(col(key_column))
    return source_df.withColumn(
        "uniqueness_pass",
        count(lit(1)).over(key_window) == 1,
    )


def validate_customer_uniqueness(customers_df: DataFrame) -> DataFrame:
    """Validate customer_id uniqueness."""
    return _with_uniqueness_result(customers_df, "customer_id")


def validate_order_uniqueness(orders_df: DataFrame) -> DataFrame:
    """Validate order_id uniqueness."""
    return _with_uniqueness_result(orders_df, "order_id")


def validate_product_uniqueness(products_df: DataFrame) -> DataFrame:
    """Validate product_id uniqueness."""
    return _with_uniqueness_result(products_df, "product_id")
