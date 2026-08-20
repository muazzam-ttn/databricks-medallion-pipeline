"""Compose approved quality modules and persist the final Silver tables."""

from importlib import import_module

from pyspark.sql import Column, DataFrame
from pyspark.sql.functions import (
    array,
    array_compact,
    coalesce,
    col,
    count,
    current_date,
    lit,
    sum as spark_sum,
    when,
)

# The approved module filenames start with numbers, so regular Python import
# syntax cannot reference them. import_module keeps the existing file names.
completeness = import_module("01_quality_completeness")
uniqueness = import_module("02_quality_uniqueness")
type_validation = import_module("03_quality_type_validation")
referential_integrity = import_module("04_quality_referential_integrity")
business_logic = import_module("05_quality_business_logic")

BRONZE_CUSTOMERS = "ecommerce_sales.bronze.customers"
BRONZE_ORDERS = "ecommerce_sales.bronze.orders"
BRONZE_PRODUCTS = "ecommerce_sales.bronze.products"

SILVER_SCHEMA = "ecommerce_sales.silver"
SILVER_CUSTOMERS = f"{SILVER_SCHEMA}.customers"
SILVER_ORDERS = f"{SILVER_SCHEMA}.orders"
SILVER_PRODUCTS = f"{SILVER_SCHEMA}.products"

EXPECTED_ROW_COUNTS = {
    "customers": 10_000,
    "orders": 100_000,
    "products": 500,
}

QUALITY_DIMENSION_COLUMNS = (
    "completeness_pass",
    "uniqueness_pass",
    "type_validation_pass",
    "referential_integrity_pass",
    "business_logic_pass",
)

CUSTOMER_SEGMENTS = ("Premium", "Standard", "Basic")
ORDER_STATUSES = ("Pending", "Completed", "Cancelled")


def _all_dimensions_pass() -> Column:
    """Return the conjunction of all required quality dimensions."""
    result = lit(True)
    for quality_column in QUALITY_DIMENSION_COLUMNS:
        result = result & coalesce(col(quality_column), lit(False))
    return result


def _add_quality_outcome(
    source_df: DataFrame,
    reason_conditions: list[tuple[Column, str]],
) -> DataFrame:
    """Add final PASS/FAIL and a compact array of specific failure reasons."""
    failure_reasons = array_compact(
        array(
            *[
                when(condition, lit(reason))
                for condition, reason in reason_conditions
            ]
        )
    )
    return source_df.withColumn(
        "quality_check_result",
        when(_all_dimensions_pass(), lit("PASS")).otherwise(lit("FAIL")),
    ).withColumn("quality_failure_reasons", failure_reasons)


def _with_order_reference_detail(
    orders_df: DataFrame,
    customers_df: DataFrame,
    products_df: DataFrame,
) -> DataFrame:
    """Add temporary per-reference flags using unique parent-key sets."""
    customer_keys = (
        customers_df.select(col("customer_id").alias("_reason_customer_id"))
        .where(col("_reason_customer_id").isNotNull())
        .distinct()
        .withColumn("_customer_reference_found", lit(True))
    )
    product_keys = (
        products_df.select(col("product_id").alias("_reason_product_id"))
        .where(col("_reason_product_id").isNotNull())
        .distinct()
        .withColumn("_product_reference_found", lit(True))
    )

    with_customer_detail = orders_df.join(
        customer_keys,
        orders_df["customer_id"] == customer_keys["_reason_customer_id"],
        "left",
    )
    with_reference_detail = with_customer_detail.join(
        product_keys,
        with_customer_detail["product_id"] == product_keys["_reason_product_id"],
        "left",
    )

    return (
        with_reference_detail.withColumn(
            "_customer_reference_pass",
            col("customer_id").isNull()
            | coalesce(col("_customer_reference_found"), lit(False)),
        )
        .withColumn(
            "_product_reference_pass",
            col("product_id").isNull()
            | coalesce(col("_product_reference_found"), lit(False)),
        )
        .drop(
            "_reason_customer_id",
            "_customer_reference_found",
            "_reason_product_id",
            "_product_reference_found",
        )
    )


def build_silver_customers(customers_df: DataFrame) -> DataFrame:
    """Compose all customer validations and detailed failure reasons."""
    validated_df = completeness.validate_customer_completeness(customers_df)
    validated_df = uniqueness.validate_customer_uniqueness(validated_df)
    validated_df = type_validation.validate_customer_types(validated_df)
    validated_df = (
        referential_integrity.validate_customer_referential_integrity(validated_df)
    )
    validated_df = business_logic.validate_customer_business_logic(validated_df)

    reason_conditions = [
        (col("email").isNull(), "NULL_EMAIL"),
        (
            ~coalesce(col("uniqueness_pass"), lit(False)),
            "DUPLICATE_CUSTOMER_ID",
        ),
        (
            ~coalesce(col("type_validation_pass"), lit(False)),
            "TYPE_VALIDATION_FAILED",
        ),
        (
            ~coalesce(col("customer_segment").isin(*CUSTOMER_SEGMENTS), lit(False)),
            "INVALID_CUSTOMER_SEGMENT",
        ),
        (col("lifetime_value") < 0, "NEGATIVE_LIFETIME_VALUE"),
        (col("signup_date") > current_date(), "FUTURE_SIGNUP_DATE"),
    ]
    return _add_quality_outcome(validated_df, reason_conditions)


def build_silver_orders(
    orders_df: DataFrame,
    customers_df: DataFrame,
    products_df: DataFrame,
) -> DataFrame:
    """Compose all order validations and detailed failure reasons."""
    validated_df = completeness.validate_order_completeness(orders_df)
    validated_df = uniqueness.validate_order_uniqueness(validated_df)
    validated_df = type_validation.validate_order_types(validated_df)
    validated_df = referential_integrity.validate_order_referential_integrity(
        validated_df,
        customers_df,
        products_df,
    )
    validated_df = business_logic.validate_order_business_logic(validated_df)
    validated_df = _with_order_reference_detail(
        validated_df,
        customers_df,
        products_df,
    )

    actual_total = col("total_amount").cast(business_logic.MONEY_TYPE)
    calculated_total = (
        col("quantity").cast(business_logic.QUANTITY_TYPE)
        * col("unit_price").cast(business_logic.MONEY_TYPE)
    ).cast(business_logic.MONEY_TYPE)

    reason_conditions = [
        (col("customer_id").isNull(), "NULL_CUSTOMER_ID"),
        (col("product_id").isNull(), "NULL_PRODUCT_ID"),
        (~coalesce(col("uniqueness_pass"), lit(False)), "DUPLICATE_ORDER_ID"),
        (
            ~coalesce(col("type_validation_pass"), lit(False)),
            "TYPE_VALIDATION_FAILED",
        ),
        (
            col("customer_id").isNotNull()
            & ~coalesce(col("_customer_reference_pass"), lit(False)),
            "INVALID_CUSTOMER_REFERENCE",
        ),
        (
            col("product_id").isNotNull()
            & ~coalesce(col("_product_reference_pass"), lit(False)),
            "INVALID_PRODUCT_REFERENCE",
        ),
        (col("quantity") <= 0, "INVALID_QUANTITY"),
        (col("unit_price") < 0, "NEGATIVE_UNIT_PRICE"),
        (col("total_amount") < 0, "NEGATIVE_TOTAL_AMOUNT"),
        (
            ~coalesce(col("order_status").isin(*ORDER_STATUSES), lit(False)),
            "INVALID_ORDER_STATUS",
        ),
        (
            ~coalesce(actual_total == calculated_total, lit(False)),
            "TOTAL_AMOUNT_MISMATCH",
        ),
    ]
    return _add_quality_outcome(validated_df, reason_conditions).drop(
        "_customer_reference_pass",
        "_product_reference_pass",
    )


def build_silver_products(products_df: DataFrame) -> DataFrame:
    """Compose all product validations and detailed failure reasons."""
    validated_df = completeness.validate_product_completeness(products_df)
    validated_df = uniqueness.validate_product_uniqueness(validated_df)
    validated_df = type_validation.validate_product_types(validated_df)
    validated_df = (
        referential_integrity.validate_product_referential_integrity(validated_df)
    )
    validated_df = business_logic.validate_product_business_logic(validated_df)

    reason_conditions = [
        (col("product_id").isNull(), "NULL_PRODUCT_ID"),
        (col("product_name").isNull(), "NULL_PRODUCT_NAME"),
        (
            ~coalesce(col("uniqueness_pass"), lit(False)),
            "DUPLICATE_PRODUCT_ID",
        ),
        (
            ~coalesce(col("type_validation_pass"), lit(False)),
            "TYPE_VALIDATION_FAILED",
        ),
        (col("price") < 0, "NEGATIVE_PRODUCT_PRICE"),
        (col("cost") < 0, "NEGATIVE_PRODUCT_COST"),
        (col("stock_quantity") < 0, "NEGATIVE_STOCK_QUANTITY"),
        (col("reorder_level") < 0, "NEGATIVE_REORDER_LEVEL"),
    ]
    return _add_quality_outcome(validated_df, reason_conditions)


def _print_runtime_summary(dataset_name: str, silver_df: DataFrame) -> None:
    """Print overall and dimension-level pass/fail counts."""
    aggregations = [
        count(lit(1)).alias("total_rows"),
        spark_sum(
            when(col("quality_check_result") == "PASS", lit(1)).otherwise(lit(0))
        ).alias("pass_rows"),
        spark_sum(
            when(col("quality_check_result") == "FAIL", lit(1)).otherwise(lit(0))
        ).alias("fail_rows"),
    ]
    for quality_column in QUALITY_DIMENSION_COLUMNS:
        aggregations.extend(
            [
                spark_sum(
                    when(
                        coalesce(col(quality_column), lit(False)),
                        lit(1),
                    ).otherwise(lit(0))
                ).alias(f"{quality_column}_rows"),
                spark_sum(
                    when(
                        ~coalesce(col(quality_column), lit(False)),
                        lit(1),
                    ).otherwise(lit(0))
                ).alias(f"{quality_column}_failed_rows"),
            ]
        )

    summary = silver_df.agg(*aggregations).first().asDict()
    print(
        f"{dataset_name}: total_rows={summary['total_rows']:,}, "
        f"PASS={summary['pass_rows']:,}, FAIL={summary['fail_rows']:,}"
    )
    for quality_column in QUALITY_DIMENSION_COLUMNS:
        print(
            f"  {quality_column}: "
            f"pass={summary[f'{quality_column}_rows']:,}, "
            f"fail={summary[f'{quality_column}_failed_rows']:,}"
        )


def _write_and_validate_silver_table(
    dataset_name: str,
    bronze_df: DataFrame,
    silver_df: DataFrame,
    target_table: str,
) -> None:
    """Overwrite one Silver table and prove physical row preservation."""
    bronze_count = bronze_df.count()
    expected_count = EXPECTED_ROW_COUNTS[dataset_name]
    if bronze_count != expected_count:
        raise ValueError(
            f"Unexpected Bronze {dataset_name} count: "
            f"expected={expected_count:,}, actual={bronze_count:,}."
        )

    (
        silver_df.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(target_table)
    )

    persisted_df = spark.table(target_table)
    silver_count = persisted_df.count()
    if silver_count != bronze_count:
        raise RuntimeError(
            f"Silver row preservation failed for {dataset_name}: "
            f"bronze={bronze_count:,}, silver={silver_count:,}."
        )

    _print_runtime_summary(dataset_name, persisted_df)


def create_silver_tables() -> None:
    """Read Bronze, compose quality checks, and overwrite all Silver tables."""
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {SILVER_SCHEMA}")

    bronze_customers = spark.table(BRONZE_CUSTOMERS)
    bronze_orders = spark.table(BRONZE_ORDERS)
    bronze_products = spark.table(BRONZE_PRODUCTS)

    silver_customers = build_silver_customers(bronze_customers)
    silver_orders = build_silver_orders(
        bronze_orders,
        bronze_customers,
        bronze_products,
    )
    silver_products = build_silver_products(bronze_products)

    _write_and_validate_silver_table(
        "customers",
        bronze_customers,
        silver_customers,
        SILVER_CUSTOMERS,
    )
    _write_and_validate_silver_table(
        "orders",
        bronze_orders,
        silver_orders,
        SILVER_ORDERS,
    )
    _write_and_validate_silver_table(
        "products",
        bronze_products,
        silver_products,
        SILVER_PRODUCTS,
    )


if __name__ == "__main__":
    create_silver_tables()
