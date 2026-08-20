CREATE OR REPLACE TABLE ecommerce_sales.gold.daily_weekly_trends
USING DELTA
AS
WITH qualifying_orders AS (
    SELECT
        order_id,
        CAST(order_date AS DATE) AS order_date,
        CAST(total_amount AS DECIMAL(20, 2)) AS total_amount
    FROM ecommerce_sales.silver.orders
    WHERE quality_check_result = 'PASS'
      AND order_status = 'Completed'
),
trend_periods AS (
    SELECT
        'DAILY' AS period_type,
        order_date AS period_start,
        order_id,
        total_amount
    FROM qualifying_orders

    UNION ALL

    SELECT
        'WEEKLY' AS period_type,
        CAST(DATE_TRUNC('WEEK', order_date) AS DATE) AS period_start,
        order_id,
        total_amount
    FROM qualifying_orders
)
SELECT
    period_type,
    period_start,
    COUNT(DISTINCT order_id) AS total_orders,
    CAST(SUM(total_amount) AS DECIMAL(20, 2)) AS total_revenue,
    CAST(AVG(total_amount) AS DECIMAL(20, 2)) AS avg_order_value
FROM trend_periods
GROUP BY
    period_type,
    period_start;
