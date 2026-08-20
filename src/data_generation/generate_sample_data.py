"""Generate deterministic synthetic e-commerce CSV source data."""

from __future__ import annotations

import argparse
import random
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pandas as pd
from faker import Faker

RANDOM_SEED = 20260820
FAKER_SEED = 20260821

CUSTOMER_COUNT = 10_000
ORDER_COUNT = 100_000
PRODUCT_COUNT = 500

CUSTOMER_NULL_EMAIL_COUNT = 50
CUSTOMER_DUPLICATE_ROW_COUNT = 10

ORDER_NULL_CUSTOMER_COUNT = 100
ORDER_NULL_PRODUCT_COUNT = 200
ORDER_INVALID_CUSTOMER_COUNT = 50
ORDER_INVALID_PRODUCT_COUNT = 30
ORDER_DUPLICATE_ROW_COUNT = 20

CUSTOMER_COLUMNS = [
    "customer_id",
    "customer_name",
    "email",
    "country",
    "signup_date",
    "customer_segment",
    "lifetime_value",
]
PRODUCT_COLUMNS = [
    "product_id",
    "product_name",
    "category",
    "price",
    "cost",
    "stock_quantity",
    "reorder_level",
]
ORDER_COLUMNS = [
    "order_id",
    "customer_id",
    "order_date",
    "product_id",
    "quantity",
    "unit_price",
    "total_amount",
    "order_status",
    "payment_date",
]

CUSTOMER_SEGMENTS = ("Premium", "Standard", "Basic")
ORDER_STATUSES = ("Pending", "Completed", "Cancelled")
PRODUCTS_BY_CATEGORY = {
    "Electronics": ("Headphones", "Keyboard", "Monitor", "Speaker", "Webcam"),
    "Home": ("Lamp", "Storage Box", "Cookware Set", "Towel Set", "Vase"),
    "Office": ("Notebook", "Desk Organizer", "Stapler", "Pen Set", "Planner"),
    "Sports": ("Yoga Mat", "Water Bottle", "Resistance Band", "Gym Bag", "Towel"),
    "Books": ("Data Handbook", "Business Guide", "Cookbook", "Travel Guide", "Novel"),
}
PRODUCT_ADJECTIVES = ("Essential", "Classic", "Modern", "Compact", "Premium")

DATA_START_DATE = date(2020, 1, 1)
DATA_END_DATE = date(2025, 12, 31)


def money(cents: int) -> Decimal:
    """Convert integer cents to a two-decimal monetary value."""
    return (Decimal(cents) / Decimal(100)).quantize(Decimal("0.01"))


def require(condition: bool, message: str) -> None:
    """Raise a clear validation error when a generation invariant fails."""
    if not condition:
        raise ValueError(f"Data generation validation failed: {message}")


def generate_products(rng: random.Random) -> pd.DataFrame:
    """Generate a valid product catalog."""
    categories = tuple(PRODUCTS_BY_CATEGORY)
    records = []

    for product_id in range(1, PRODUCT_COUNT + 1):
        category = rng.choice(categories)
        product_type = rng.choice(PRODUCTS_BY_CATEGORY[category])
        price_cents = rng.randint(500, 50_000)
        cost_cents = rng.randint(max(100, price_cents // 4), price_cents)
        records.append(
            {
                "product_id": product_id,
                "product_name": (
                    f"{rng.choice(PRODUCT_ADJECTIVES)} {product_type} {product_id:03d}"
                ),
                "category": category,
                "price": money(price_cents),
                "cost": money(cost_cents),
                "stock_quantity": rng.randint(0, 1_000),
                "reorder_level": rng.randint(0, 100),
            }
        )

    products = pd.DataFrame(records, columns=PRODUCT_COLUMNS)
    validate_products(products)
    return products


def generate_customers(rng: random.Random, fake: Faker) -> pd.DataFrame:
    """Generate a valid customer baseline."""
    records = []

    for customer_id in range(1, CUSTOMER_COUNT + 1):
        records.append(
            {
                "customer_id": customer_id,
                "customer_name": fake.name(),
                "email": fake.email(),
                "country": fake.country(),
                "signup_date": fake.date_between(
                    start_date=DATA_START_DATE, end_date=DATA_END_DATE
                ),
                "customer_segment": rng.choices(
                    CUSTOMER_SEGMENTS, weights=(20, 50, 30), k=1
                )[0],
                "lifetime_value": money(rng.randint(0, 1_000_000)),
            }
        )

    customers = pd.DataFrame(records, columns=CUSTOMER_COLUMNS)
    validate_customer_baseline(customers)
    return customers


def inject_customer_defects(
    customers: pd.DataFrame, rng: random.Random
) -> pd.DataFrame:
    """Inject exact customer defects without changing the physical row count."""
    customers = customers.copy()

    duplicate_source_indexes = list(range(CUSTOMER_DUPLICATE_ROW_COUNT))
    duplicate_target_indexes = list(
        range(
            CUSTOMER_COUNT - CUSTOMER_DUPLICATE_ROW_COUNT,
            CUSTOMER_COUNT,
        )
    )
    for source_index, target_index in zip(
        duplicate_source_indexes, duplicate_target_indexes
    ):
        customers.at[target_index, "customer_id"] = customers.at[
            source_index, "customer_id"
        ]

    duplicate_member_indexes = set(
        duplicate_source_indexes + duplicate_target_indexes
    )
    email_candidates = [
        index
        for index in customers.index
        if index not in duplicate_member_indexes
    ]
    null_email_indexes = rng.sample(email_candidates, CUSTOMER_NULL_EMAIL_COUNT)
    customers.loc[null_email_indexes, "email"] = None

    validate_customers(customers)
    return customers


def generate_orders(
    products: pd.DataFrame,
    valid_customer_ids: list[int],
    rng: random.Random,
) -> pd.DataFrame:
    """Generate a valid order baseline referencing existing parent IDs."""
    product_price_by_id = products.set_index("product_id")["price"].to_dict()
    product_ids = list(product_price_by_id)
    records = []

    for order_id in range(1, ORDER_COUNT + 1):
        product_id = rng.choice(product_ids)
        order_date = DATA_START_DATE + timedelta(
            days=rng.randint(0, (DATA_END_DATE - DATA_START_DATE).days)
        )
        quantity = rng.randint(1, 5)
        unit_price = product_price_by_id[product_id]
        order_status = rng.choices(
            ORDER_STATUSES, weights=(15, 75, 10), k=1
        )[0]
        payment_date = (
            min(order_date + timedelta(days=rng.randint(0, 3)), DATA_END_DATE)
            if order_status == "Completed"
            else None
        )
        records.append(
            {
                "order_id": order_id,
                "customer_id": rng.choice(valid_customer_ids),
                "order_date": order_date,
                "product_id": product_id,
                "quantity": quantity,
                "unit_price": unit_price,
                "total_amount": (unit_price * quantity).quantize(
                    Decimal("0.01")
                ),
                "order_status": order_status,
                "payment_date": payment_date,
            }
        )

    orders = pd.DataFrame(records, columns=ORDER_COLUMNS)
    validate_order_baseline(
        orders, set(valid_customer_ids), set(product_ids)
    )
    return orders


def inject_order_defects(
    orders: pd.DataFrame,
    valid_customer_ids: set[int],
    valid_product_ids: set[int],
    rng: random.Random,
) -> pd.DataFrame:
    """Inject exact, non-overlapping order defects at fixed row count."""
    orders = orders.copy()

    duplicate_source_indexes = list(range(ORDER_DUPLICATE_ROW_COUNT))
    duplicate_target_indexes = list(
        range(ORDER_COUNT - ORDER_DUPLICATE_ROW_COUNT, ORDER_COUNT)
    )
    for source_index, target_index in zip(
        duplicate_source_indexes, duplicate_target_indexes
    ):
        orders.at[target_index, "order_id"] = orders.at[
            source_index, "order_id"
        ]

    reserved_indexes = set(
        duplicate_source_indexes + duplicate_target_indexes
    )
    defect_counts = (
        ORDER_NULL_CUSTOMER_COUNT,
        ORDER_NULL_PRODUCT_COUNT,
        ORDER_INVALID_CUSTOMER_COUNT,
        ORDER_INVALID_PRODUCT_COUNT,
    )
    selected_indexes = rng.sample(
        [index for index in orders.index if index not in reserved_indexes],
        sum(defect_counts),
    )
    boundaries = []
    start = 0
    for count in defect_counts:
        boundaries.append(selected_indexes[start : start + count])
        start += count

    (
        null_customer_indexes,
        null_product_indexes,
        invalid_customer_indexes,
        invalid_product_indexes,
    ) = boundaries

    orders.loc[null_customer_indexes, "customer_id"] = pd.NA
    orders.loc[null_product_indexes, "product_id"] = pd.NA

    first_invalid_customer_id = max(valid_customer_ids) + 1
    orders.loc[invalid_customer_indexes, "customer_id"] = range(
        first_invalid_customer_id,
        first_invalid_customer_id + ORDER_INVALID_CUSTOMER_COUNT,
    )
    first_invalid_product_id = max(valid_product_ids) + 1
    orders.loc[invalid_product_indexes, "product_id"] = range(
        first_invalid_product_id,
        first_invalid_product_id + ORDER_INVALID_PRODUCT_COUNT,
    )

    orders["customer_id"] = orders["customer_id"].astype("Int64")
    orders["product_id"] = orders["product_id"].astype("Int64")

    validate_orders(orders, valid_customer_ids, valid_product_ids)
    return orders


def validate_required_columns(
    frame: pd.DataFrame, expected_columns: list[str], dataset_name: str
) -> None:
    require(
        list(frame.columns) == expected_columns,
        f"{dataset_name} columns must be exactly {expected_columns}",
    )


def validate_products(products: pd.DataFrame) -> None:
    """Validate the product baseline and final product output."""
    validate_required_columns(products, PRODUCT_COLUMNS, "products")
    require(len(products) == PRODUCT_COUNT, "products must contain 500 rows")
    require(
        products["product_id"].nunique() == PRODUCT_COUNT,
        "product_id values must be unique",
    )
    require(
        not products[PRODUCT_COLUMNS].isna().any().any(),
        "products must not contain NULL values",
    )
    require(
        (products["price"] >= 0).all() and (products["cost"] >= 0).all(),
        "product monetary values must be non-negative",
    )
    require(
        (products["stock_quantity"] >= 0).all()
        and (products["reorder_level"] >= 0).all(),
        "product inventory values must be non-negative",
    )


def validate_customer_baseline(customers: pd.DataFrame) -> None:
    """Validate customers before intentional defects are injected."""
    validate_required_columns(customers, CUSTOMER_COLUMNS, "customers")
    require(len(customers) == CUSTOMER_COUNT, "customers must contain 10,000 rows")
    require(customers["customer_id"].is_unique, "baseline customer IDs must be unique")
    require(
        not customers[CUSTOMER_COLUMNS].isna().any().any(),
        "customer baseline must not contain NULL values",
    )
    require(
        customers["customer_segment"].isin(CUSTOMER_SEGMENTS).all(),
        "customer segments must use the approved values",
    )
    require(
        (customers["lifetime_value"] >= 0).all(),
        "customer lifetime values must be non-negative",
    )


def validate_customers(customers: pd.DataFrame) -> None:
    """Validate exact customer output conditions."""
    validate_required_columns(customers, CUSTOMER_COLUMNS, "customers")
    require(len(customers) == CUSTOMER_COUNT, "customers must contain 10,000 rows")
    require(
        customers["email"].isna().sum() == CUSTOMER_NULL_EMAIL_COUNT,
        "customers must contain exactly 50 NULL emails",
    )
    require(
        customers.drop(columns=["email"]).isna().sum().sum() == 0,
        "customers contain an unintended NULL outside email",
    )

    duplicate_mask = customers["customer_id"].duplicated(keep=False)
    duplicate_groups = customers.loc[duplicate_mask].groupby("customer_id").size()
    require(
        CUSTOMER_COUNT - customers["customer_id"].nunique()
        == CUSTOMER_DUPLICATE_ROW_COUNT,
        "exactly 10 customer rows must reuse existing IDs",
    )
    require(
        len(duplicate_groups) == CUSTOMER_DUPLICATE_ROW_COUNT
        and (duplicate_groups == 2).all()
        and duplicate_mask.sum() == 2 * CUSTOMER_DUPLICATE_ROW_COUNT,
        "customers must have 10 two-row duplicate-key groups",
    )
    require(
        customers["customer_segment"].isin(CUSTOMER_SEGMENTS).all(),
        "customer segments must use the approved values",
    )
    require(
        (customers["lifetime_value"] >= 0).all(),
        "customer lifetime values must be non-negative",
    )


def validate_order_baseline(
    orders: pd.DataFrame,
    valid_customer_ids: set[int],
    valid_product_ids: set[int],
) -> None:
    """Validate orders before intentional defects are injected."""
    validate_required_columns(orders, ORDER_COLUMNS, "orders")
    require(len(orders) == ORDER_COUNT, "orders must contain 100,000 rows")
    require(orders["order_id"].is_unique, "baseline order IDs must be unique")
    require(
        orders["customer_id"].isin(valid_customer_ids).all(),
        "baseline orders contain an invalid customer reference",
    )
    require(
        orders["product_id"].isin(valid_product_ids).all(),
        "baseline orders contain an invalid product reference",
    )
    require(
        not orders[[column for column in ORDER_COLUMNS if column != "payment_date"]]
        .isna()
        .any()
        .any(),
        "order baseline contains an unexpected NULL",
    )
    require((orders["quantity"] > 0).all(), "order quantity must be positive")
    require(
        orders["order_status"].isin(ORDER_STATUSES).all(),
        "order statuses must use the approved values",
    )
    expected_totals = orders.apply(
        lambda row: (row["unit_price"] * row["quantity"]).quantize(
            Decimal("0.01")
        ),
        axis=1,
    )
    require(
        expected_totals.equals(orders["total_amount"]),
        "order totals must equal quantity multiplied by unit price",
    )


def validate_orders(
    orders: pd.DataFrame,
    valid_customer_ids: set[int],
    valid_product_ids: set[int],
) -> None:
    """Validate exact order output conditions and reject accidental defects."""
    validate_required_columns(orders, ORDER_COLUMNS, "orders")
    require(len(orders) == ORDER_COUNT, "orders must contain 100,000 rows")
    require(
        orders["customer_id"].isna().sum() == ORDER_NULL_CUSTOMER_COUNT,
        "orders must contain exactly 100 NULL customer IDs",
    )
    require(
        orders["product_id"].isna().sum() == ORDER_NULL_PRODUCT_COUNT,
        "orders must contain exactly 200 NULL product IDs",
    )
    required_non_fk_columns = [
        column
        for column in ORDER_COLUMNS
        if column not in ("customer_id", "product_id", "payment_date")
    ]
    require(
        orders[required_non_fk_columns].isna().sum().sum() == 0,
        "orders contain an unintended NULL in a required non-FK column",
    )

    invalid_customer_mask = orders["customer_id"].notna() & ~orders[
        "customer_id"
    ].isin(valid_customer_ids)
    invalid_product_mask = orders["product_id"].notna() & ~orders[
        "product_id"
    ].isin(valid_product_ids)
    require(
        invalid_customer_mask.sum() == ORDER_INVALID_CUSTOMER_COUNT,
        "orders must contain exactly 50 non-null invalid customer references",
    )
    require(
        invalid_product_mask.sum() == ORDER_INVALID_PRODUCT_COUNT,
        "orders must contain exactly 30 non-null invalid product references",
    )

    duplicate_mask = orders["order_id"].duplicated(keep=False)
    duplicate_groups = orders.loc[duplicate_mask].groupby("order_id").size()
    require(
        ORDER_COUNT - orders["order_id"].nunique() == ORDER_DUPLICATE_ROW_COUNT,
        "exactly 20 order rows must reuse existing IDs",
    )
    require(
        len(duplicate_groups) == ORDER_DUPLICATE_ROW_COUNT
        and (duplicate_groups == 2).all()
        and duplicate_mask.sum() == 2 * ORDER_DUPLICATE_ROW_COUNT,
        "orders must have 20 two-row duplicate-key groups",
    )

    issue_masks = [
        orders["customer_id"].isna(),
        orders["product_id"].isna(),
        invalid_customer_mask,
        invalid_product_mask,
        duplicate_mask,
    ]
    issue_membership_count = sum(mask.astype(int) for mask in issue_masks)
    require(
        (issue_membership_count <= 1).all(),
        "intentional order issue groups must not overlap",
    )
    require((orders["quantity"] > 0).all(), "order quantity must be positive")
    require(
        orders["order_status"].isin(ORDER_STATUSES).all(),
        "order statuses must use the approved values",
    )
    expected_totals = orders.apply(
        lambda row: (row["unit_price"] * row["quantity"]).quantize(
            Decimal("0.01")
        ),
        axis=1,
    )
    require(
        expected_totals.equals(orders["total_amount"]),
        "order totals must equal quantity multiplied by unit price",
    )


def write_outputs(
    customers: pd.DataFrame,
    orders: pd.DataFrame,
    products: pd.DataFrame,
    output_dir: Path,
) -> None:
    """Write validated dataframes to the required CSV files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    customers.to_csv(output_dir / "customers.csv", index=False)
    orders.to_csv(output_dir / "orders.csv", index=False)
    products.to_csv(output_dir / "products.csv", index=False)


def generate_all(output_dir: Path) -> None:
    """Generate, validate, and write all three source datasets."""
    rng = random.Random(RANDOM_SEED)
    fake = Faker("en_US")
    fake.seed_instance(FAKER_SEED)

    products = generate_products(rng)
    customers = inject_customer_defects(generate_customers(rng, fake), rng)
    valid_customer_ids = set(customers["customer_id"])
    valid_product_ids = set(products["product_id"])
    orders = inject_order_defects(
        generate_orders(products, sorted(valid_customer_ids), rng),
        valid_customer_ids,
        valid_product_ids,
        rng,
    )

    # Final validation runs immediately before output is accepted and written.
    validate_products(products)
    validate_customers(customers)
    validate_orders(orders, valid_customer_ids, valid_product_ids)
    write_outputs(customers, orders, products, output_dir)

    print(f"Generated and validated {len(customers):,} customer rows")
    print(f"Generated and validated {len(orders):,} order rows")
    print(f"Generated and validated {len(products):,} product rows")
    print(f"Output directory: {output_dir.resolve()}")


def parse_args() -> argparse.Namespace:
    default_output_dir = Path(__file__).resolve().parents[2] / "data"
    parser = argparse.ArgumentParser(
        description="Generate deterministic synthetic e-commerce CSV data."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=default_output_dir,
        help=f"CSV output directory (default: {default_output_dir})",
    )
    return parser.parse_args()


if __name__ == "__main__":
    generate_all(parse_args().output_dir)
