"""Lightweight schema-aware type checks for inferred Bronze DataFrames."""

from pyspark.sql import DataFrame
from pyspark.sql.functions import lit
from pyspark.sql.types import (
    ByteType,
    DateType,
    DecimalType,
    DoubleType,
    FloatType,
    IntegerType,
    LongType,
    ShortType,
)

INTEGRAL_TYPES = (ByteType, ShortType, IntegerType, LongType)
DECIMAL_COMPATIBLE_TYPES = (DecimalType, DoubleType, FloatType)

CUSTOMER_EXPECTED_TYPES = {
    "customer_id": INTEGRAL_TYPES,
    "signup_date": (DateType,),
    "lifetime_value": DECIMAL_COMPATIBLE_TYPES,
}
ORDER_EXPECTED_TYPES = {
    "order_id": INTEGRAL_TYPES,
    "customer_id": INTEGRAL_TYPES,
    "order_date": (DateType,),
    "product_id": INTEGRAL_TYPES,
    "quantity": INTEGRAL_TYPES,
    "unit_price": DECIMAL_COMPATIBLE_TYPES,
    "total_amount": DECIMAL_COMPATIBLE_TYPES,
    "payment_date": (DateType,),
}
PRODUCT_EXPECTED_TYPES = {
    "product_id": INTEGRAL_TYPES,
    "price": DECIMAL_COMPATIBLE_TYPES,
    "cost": DECIMAL_COMPATIBLE_TYPES,
    "stock_quantity": INTEGRAL_TYPES,
    "reorder_level": INTEGRAL_TYPES,
}


def _schema_matches_expected_types(
    source_df: DataFrame,
    expected_types: dict[str, tuple[type, ...]],
) -> bool:
    """Return whether inferred types match the approved logical type families."""
    actual_types = {field.name: field.dataType for field in source_df.schema.fields}
    missing_columns = sorted(set(expected_types) - set(actual_types))
    if missing_columns:
        raise ValueError(
            f"Columns required for type validation are missing: {missing_columns}"
        )

    return all(
        isinstance(actual_types[column_name], accepted_types)
        for column_name, accepted_types in expected_types.items()
    )


def _with_type_validation_result(
    source_df: DataFrame,
    expected_types: dict[str, tuple[type, ...]],
) -> DataFrame:
    """Add a dataset-wide inferred-schema result to every preserved row."""
    schema_is_valid = _schema_matches_expected_types(source_df, expected_types)
    return source_df.withColumn("type_validation_pass", lit(schema_is_valid))


def validate_customer_types(customers_df: DataFrame) -> DataFrame:
    """Validate relevant inferred customer column types."""
    return _with_type_validation_result(customers_df, CUSTOMER_EXPECTED_TYPES)


def validate_order_types(orders_df: DataFrame) -> DataFrame:
    """Validate relevant inferred order column types."""
    return _with_type_validation_result(orders_df, ORDER_EXPECTED_TYPES)


def validate_product_types(products_df: DataFrame) -> DataFrame:
    """Validate relevant inferred product column types."""
    return _with_type_validation_result(products_df, PRODUCT_EXPECTED_TYPES)
