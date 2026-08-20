CREATE OR REPLACE TABLE ecommerce_sales.gold.revenue_by_customer
USING DELTA
AS
WITH valid_customers AS (
    SELECT
        customer_id,
        customer_name,
        customer_segment
    FROM ecommerce_sales.silver.customers
    WHERE quality_check_result = 'PASS'
),
qualifying_orders AS (
    SELECT
        order_id,
        customer_id,
        CAST(total_amount AS DECIMAL(20, 2)) AS total_amount
    FROM ecommerce_sales.silver.orders
    WHERE quality_check_result = 'PASS'
      AND order_status = 'Completed'
),
customer_revenue AS (
    SELECT
        customer_id,
        COUNT(DISTINCT order_id) AS total_orders,
        CAST(SUM(total_amount) AS DECIMAL(20, 2)) AS total_revenue,
        CAST(AVG(total_amount) AS DECIMAL(20, 2)) AS avg_order_value
    FROM qualifying_orders
    GROUP BY customer_id
)
SELECT
    customers.customer_id,
    customers.customer_name,
    customers.customer_segment,
    COALESCE(revenue.total_orders, CAST(0 AS BIGINT)) AS total_orders,
    COALESCE(
        revenue.total_revenue,
        CAST(0 AS DECIMAL(20, 2))
    ) AS total_revenue,
    COALESCE(
        revenue.avg_order_value,
        CAST(0 AS DECIMAL(20, 2))
    ) AS avg_order_value,
    COALESCE(
        revenue.total_revenue,
        CAST(0 AS DECIMAL(20, 2))
    ) AS lifetime_value_actual
FROM valid_customers AS customers
LEFT JOIN customer_revenue AS revenue
    ON customers.customer_id = revenue.customer_id;
