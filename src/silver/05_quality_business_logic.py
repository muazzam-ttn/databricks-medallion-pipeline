"""Reusable approved business-rule checks for Bronze DataFrames."""

from pyspark.sql import DataFrame
from pyspark.sql.functions import coalesce, col, current_date, lit
from pyspark.sql.types import DecimalType

CUSTOMER_SEGMENTS = ("Premium", "Standard", "Basic")
ORDER_STATUSES = ("Pending", "Completed", "Cancelled")
MONEY_TYPE = DecimalType(20, 2)
QUANTITY_TYPE = DecimalType(10, 0)


def validate_customer_business_logic(customers_df: DataFrame) -> DataFrame:
    """Validate the approved customer domain, value, and date rules."""
    business_condition = (
        col("customer_segment").isin(*CUSTOMER_SEGMENTS)
        & (col("lifetime_value") >= 0)
        & (col("signup_date") <= current_date())
    )
    return customers_df.withColumn(
        "business_logic_pass",
        coalesce(business_condition, lit(False)),
    )


def validate_order_business_logic(orders_df: DataFrame) -> DataFrame:
    """Validate approved order value, status, and amount-consistency rules."""
    actual_total = col("total_amount").cast(MONEY_TYPE)
    calculated_total = (
        col("quantity").cast(QUANTITY_TYPE)
        * col("unit_price").cast(MONEY_TYPE)
    ).cast(MONEY_TYPE)

    business_condition = (
        (col("quantity") > 0)
        & (col("unit_price") >= 0)
        & (col("total_amount") >= 0)
        & col("order_status").isin(*ORDER_STATUSES)
        & (actual_total == calculated_total)
    )
    return orders_df.withColumn(
        "business_logic_pass",
        coalesce(business_condition, lit(False)),
    )


def validate_product_business_logic(products_df: DataFrame) -> DataFrame:
    """Validate the approved non-negative product value rules."""
    business_condition = (
        (col("price") >= 0)
        & (col("cost") >= 0)
        & (col("stock_quantity") >= 0)
        & (col("reorder_level") >= 0)
    )
    return products_df.withColumn(
        "business_logic_pass",
        coalesce(business_condition, lit(False)),
    )
