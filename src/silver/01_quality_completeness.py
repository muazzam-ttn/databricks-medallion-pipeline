"""Reusable completeness checks for Bronze DataFrames."""

from pyspark.sql import DataFrame
from pyspark.sql.functions import col


def validate_customer_completeness(customers_df: DataFrame) -> DataFrame:
    """Require the customer email used by the approved completeness rule."""
    return customers_df.withColumn("completeness_pass", col("email").isNotNull())


def validate_order_completeness(orders_df: DataFrame) -> DataFrame:
    """Require both order foreign keys; payment_date remains nullable."""
    completeness_condition = col("customer_id").isNotNull() & col(
        "product_id"
    ).isNotNull()
    return orders_df.withColumn("completeness_pass", completeness_condition)


def validate_product_completeness(products_df: DataFrame) -> DataFrame:
    """Apply the documented defensive product completeness checks."""
    completeness_condition = col("product_id").isNotNull() & col(
        "product_name"
    ).isNotNull()
    return products_df.withColumn("completeness_pass", completeness_condition)
