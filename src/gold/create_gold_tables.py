"""Create and validate the required Gold Delta tables."""

from decimal import Decimal
from pathlib import Path

from pyspark.sql.functions import col, sum as spark_sum

GOLD_SCHEMA = "ecommerce_sales.gold"
GOLD_DIRECTORY = Path(__file__).resolve().parent

SALES_BY_PRODUCT = f"{GOLD_SCHEMA}.sales_by_product"
REVENUE_BY_CUSTOMER = f"{GOLD_SCHEMA}.revenue_by_customer"
DAILY_WEEKLY_TRENDS = f"{GOLD_SCHEMA}.daily_weekly_trends"
CUSTOMER_SEGMENTATION = f"{GOLD_SCHEMA}.customer_segmentation"

SILVER_CUSTOMERS = "ecommerce_sales.silver.customers"
SILVER_ORDERS = "ecommerce_sales.silver.orders"
SILVER_PRODUCTS = "ecommerce_sales.silver.products"

REQUIRED_SEGMENTS = {"High-Value", "Repeat", "One-Time", "Inactive"}


def _execute_sql_file(file_name: str) -> None:
    """Execute one Gold CREATE OR REPLACE TABLE statement."""
    sql_path = GOLD_DIRECTORY / file_name
    if not sql_path.is_file():
        raise FileNotFoundError(f"Required Gold SQL file was not found: {sql_path}")

    sql_text = sql_path.read_text(encoding="utf-8").strip()
    if not sql_text:
        raise ValueError(f"Required Gold SQL file is empty: {sql_path}")

    spark.sql(sql_text)
    print(f"Executed {file_name}")


def _validate_unique_grain(table_name: str, key_column: str) -> int:
    """Validate one-row-per-key grain and return the table row count."""
    gold_df = spark.table(table_name)
    row_count = gold_df.count()
    distinct_key_count = gold_df.select(key_column).distinct().count()

    if row_count != distinct_key_count:
        raise RuntimeError(
            f"Gold grain validation failed for {table_name}: "
            f"rows={row_count:,}, distinct_{key_column}={distinct_key_count:,}."
        )

    print(
        f"{table_name}: rows={row_count:,}, "
        f"distinct_{key_column}={distinct_key_count:,}"
    )
    return row_count


def _validate_source_population(
    gold_table: str,
    silver_table: str,
    gold_row_count: int,
) -> None:
    """Confirm dimension-oriented Gold tables retain every valid entity."""
    expected_count = (
        spark.table(silver_table)
        .where(col("quality_check_result") == "PASS")
        .count()
    )
    if gold_row_count != expected_count:
        raise RuntimeError(
            f"Gold population validation failed for {gold_table}: "
            f"expected_valid_silver_rows={expected_count:,}, "
            f"gold_rows={gold_row_count:,}."
        )


def _validate_segmentation(expected_customer_count: int) -> None:
    """Validate required segment labels and complete customer allocation."""
    segmentation_df = spark.table(CUSTOMER_SEGMENTATION)
    actual_segments = {
        row["segment_type"]
        for row in segmentation_df.select("segment_type").collect()
    }
    if actual_segments != REQUIRED_SEGMENTS:
        raise RuntimeError(
            "Customer segmentation labels do not match the required set: "
            f"expected={sorted(REQUIRED_SEGMENTS)}, "
            f"actual={sorted(actual_segments)}."
        )

    segmented_customer_count = (
        segmentation_df.agg(spark_sum("customer_count").alias("customer_count"))
        .first()["customer_count"]
    )
    if segmented_customer_count != expected_customer_count:
        raise RuntimeError(
            "Customer segmentation population does not reconcile with "
            f"{REVENUE_BY_CUSTOMER}: expected={expected_customer_count:,}, "
            f"segmented={segmented_customer_count:,}."
        )

    print(
        f"{CUSTOMER_SEGMENTATION}: rows={len(actual_segments):,}, "
        f"segmented_customers={segmented_customer_count:,}"
    )


def _validate_daily_weekly_trends() -> None:
    """Validate trend grain and reconcile both period types to Silver orders."""
    trends_df = spark.table(DAILY_WEEKLY_TRENDS)
    row_count = trends_df.count()
    distinct_period_count = trends_df.select(
        "period_type",
        "period_start",
    ).distinct().count()
    if row_count != distinct_period_count:
        raise RuntimeError(
            f"Gold grain validation failed for {DAILY_WEEKLY_TRENDS}: "
            f"rows={row_count:,}, "
            f"distinct_periods={distinct_period_count:,}."
        )

    period_summaries = {
        row["period_type"]: row
        for row in trends_df.groupBy("period_type")
        .agg(
            spark_sum("total_orders").alias("total_orders"),
            spark_sum("total_revenue").alias("total_revenue"),
        )
        .collect()
    }
    expected_period_types = {"DAILY", "WEEKLY"}
    if set(period_summaries) != expected_period_types:
        raise RuntimeError(
            f"Trend period types are invalid for {DAILY_WEEKLY_TRENDS}: "
            f"expected={sorted(expected_period_types)}, "
            f"actual={sorted(period_summaries)}."
        )

    qualifying_orders = spark.table(SILVER_ORDERS).where(
        (col("quality_check_result") == "PASS")
        & (col("order_status") == "Completed")
    )
    expected_order_count = qualifying_orders.count()
    expected_revenue = (
        qualifying_orders.select(
            col("total_amount").cast("decimal(20, 2)").alias("total_amount")
        )
        .agg(spark_sum("total_amount").alias("total_revenue"))
        .first()["total_revenue"]
        or Decimal("0.00")
    )

    for period_type, summary in period_summaries.items():
        if summary["total_orders"] != expected_order_count:
            raise RuntimeError(
                f"{period_type} trend order count does not reconcile: "
                f"expected={expected_order_count:,}, "
                f"actual={summary['total_orders']:,}."
            )
        if summary["total_revenue"] != expected_revenue:
            raise RuntimeError(
                f"{period_type} trend revenue does not reconcile: "
                f"expected={expected_revenue}, "
                f"actual={summary['total_revenue']}."
            )

    print(
        f"{DAILY_WEEKLY_TRENDS}: rows={row_count:,}, "
        f"qualifying_orders={expected_order_count:,}, "
        f"qualifying_revenue={expected_revenue}"
    )


def create_gold_tables() -> None:
    """Create Gold tables in dependency order and validate their grains."""
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {GOLD_SCHEMA}")

    _execute_sql_file("01_sales_by_product.sql")
    _execute_sql_file("02_revenue_by_customer.sql")
    _execute_sql_file("03_daily_weekly_trends.sql")
    _execute_sql_file("04_customer_segmentation.sql")

    product_count = _validate_unique_grain(SALES_BY_PRODUCT, "product_id")
    customer_count = _validate_unique_grain(REVENUE_BY_CUSTOMER, "customer_id")
    segment_count = _validate_unique_grain(
        CUSTOMER_SEGMENTATION,
        "segment_type",
    )

    _validate_source_population(
        SALES_BY_PRODUCT,
        SILVER_PRODUCTS,
        product_count,
    )
    _validate_source_population(
        REVENUE_BY_CUSTOMER,
        SILVER_CUSTOMERS,
        customer_count,
    )
    if segment_count != len(REQUIRED_SEGMENTS):
        raise RuntimeError(
            f"Expected {len(REQUIRED_SEGMENTS)} segmentation rows; "
            f"found {segment_count}."
        )
    _validate_daily_weekly_trends()
    _validate_segmentation(customer_count)


if __name__ == "__main__":
    create_gold_tables()
