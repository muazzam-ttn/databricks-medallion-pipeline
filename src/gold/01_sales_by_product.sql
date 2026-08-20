CREATE OR REPLACE TABLE ecommerce_sales.gold.sales_by_product
USING DELTA
AS
WITH valid_products AS (
    SELECT
        product_id,
        product_name,
        category
    FROM ecommerce_sales.silver.products
    WHERE quality_check_result = 'PASS'
),
qualifying_orders AS (
    SELECT
        order_id,
        product_id,
        CAST(total_amount AS DECIMAL(20, 2)) AS total_amount
    FROM ecommerce_sales.silver.orders
    WHERE quality_check_result = 'PASS'
      AND order_status = 'Completed'
)
SELECT
    products.product_id,
    products.product_name,
    products.category,
    COUNT(DISTINCT orders.order_id) AS total_orders,
    CAST(
        COALESCE(
            SUM(orders.total_amount),
            CAST(0 AS DECIMAL(20, 2))
        ) AS DECIMAL(20, 2)
    ) AS total_revenue,
    CAST(
        COALESCE(
            AVG(orders.total_amount),
            CAST(0 AS DECIMAL(20, 2))
        ) AS DECIMAL(20, 2)
    ) AS avg_order_value
FROM valid_products AS products
LEFT JOIN qualifying_orders AS orders
    ON products.product_id = orders.product_id
GROUP BY
    products.product_id,
    products.product_name,
    products.category;
