"""Reusable referential-integrity checks for Bronze DataFrames."""

from pyspark.sql import DataFrame
from pyspark.sql.functions import coalesce, col, lit


def validate_customer_referential_integrity(
    customers_df: DataFrame,
) -> DataFrame:
    """Mark the non-applicable customer parent-reference check as passing."""
    return customers_df.withColumn("referential_integrity_pass", lit(True))


def validate_product_referential_integrity(products_df: DataFrame) -> DataFrame:
    """Mark the non-applicable product parent-reference check as passing."""
    return products_df.withColumn("referential_integrity_pass", lit(True))


def validate_order_referential_integrity(
    orders_df: DataFrame,
    customers_df: DataFrame,
    products_df: DataFrame,
) -> DataFrame:
    """Validate non-null order foreign keys without multiplying order rows."""
    customer_keys = (
        customers_df.select(col("customer_id").alias("_valid_customer_id"))
        .where(col("_valid_customer_id").isNotNull())
        .distinct()
        .withColumn("_customer_reference_exists", lit(True))
    )
    product_keys = (
        products_df.select(col("product_id").alias("_valid_product_id"))
        .where(col("_valid_product_id").isNotNull())
        .distinct()
        .withColumn("_product_reference_exists", lit(True))
    )

    with_customer_reference = orders_df.join(
        customer_keys,
        orders_df["customer_id"] == customer_keys["_valid_customer_id"],
        "left",
    )
    with_parent_references = with_customer_reference.join(
        product_keys,
        with_customer_reference["product_id"] == product_keys["_valid_product_id"],
        "left",
    )

    # NULL foreign keys pass RI because completeness owns missing-reference failures.
    customer_reference_pass = col("customer_id").isNull() | coalesce(
        col("_customer_reference_exists"), lit(False)
    )
    product_reference_pass = col("product_id").isNull() | coalesce(
        col("_product_reference_exists"), lit(False)
    )

    return with_parent_references.withColumn(
        "referential_integrity_pass",
        customer_reference_pass & product_reference_pass,
    ).drop(
        "_valid_customer_id",
        "_customer_reference_exists",
        "_valid_product_id",
        "_product_reference_exists",
    )
