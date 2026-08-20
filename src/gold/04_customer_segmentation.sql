CREATE OR REPLACE TABLE ecommerce_sales.gold.customer_segmentation
USING DELTA
AS
WITH ranked_customers AS (
    SELECT
        customer_id,
        total_orders,
        lifetime_value_actual,
        NTILE(5) OVER (
            ORDER BY lifetime_value_actual DESC, customer_id ASC
        ) AS value_quintile
    FROM ecommerce_sales.gold.revenue_by_customer
),
classified_customers AS (
    SELECT
        customer_id,
        total_orders,
        lifetime_value_actual,
        CASE
            WHEN value_quintile = 1 AND total_orders > 0 THEN 'High-Value'
            WHEN total_orders > 1 THEN 'Repeat'
            WHEN total_orders = 1 THEN 'One-Time'
            ELSE 'Inactive'
        END AS segment_type
    FROM ranked_customers
),
segment_summary AS (
    SELECT
        segment_type,
        COUNT(*) AS customer_count,
        CAST(AVG(lifetime_value_actual) AS DECIMAL(20, 2)) AS avg_revenue,
        CAST(SUM(lifetime_value_actual) AS DECIMAL(20, 2)) AS total_revenue
    FROM classified_customers
    GROUP BY segment_type
),
required_segments AS (
    SELECT segment_type
    FROM VALUES
        ('High-Value'),
        ('Repeat'),
        ('One-Time'),
        ('Inactive')
    AS segments(segment_type)
)
SELECT
    segments.segment_type,
    COALESCE(summary.customer_count, CAST(0 AS BIGINT)) AS customer_count,
    COALESCE(
        summary.avg_revenue,
        CAST(0 AS DECIMAL(20, 2))
    ) AS avg_revenue,
    COALESCE(
        summary.total_revenue,
        CAST(0 AS DECIMAL(20, 2))
    ) AS total_revenue
FROM required_segments AS segments
LEFT JOIN segment_summary AS summary
    ON segments.segment_type = summary.segment_type;
