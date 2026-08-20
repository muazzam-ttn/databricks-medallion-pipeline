-- Query 1: Top 10 products by completed-order revenue
SELECT
    product_name,
    category,
    total_revenue,
    total_orders
FROM ecommerce_sales.gold.sales_by_product
ORDER BY total_revenue DESC, product_name ASC
LIMIT 10;


-- Query 2: Customer revenue values for a histogram
SELECT
    customer_id,
    customer_name,
    customer_segment,
    total_revenue
FROM ecommerce_sales.gold.revenue_by_customer;


-- Query 3: Customer population by calculated segment
SELECT
    segment_type,
    customer_count,
    avg_revenue,
    total_revenue
FROM ecommerce_sales.gold.customer_segmentation
ORDER BY CASE segment_type
    WHEN 'High-Value' THEN 1
    WHEN 'Repeat' THEN 2
    WHEN 'One-Time' THEN 3
    WHEN 'Inactive' THEN 4
    ELSE 5
END;


-- Query 4 (optional): Weekly completed-order revenue trend
SELECT
    period_start,
    total_revenue,
    total_orders,
    avg_order_value
FROM ecommerce_sales.gold.daily_weekly_trends
WHERE period_type = 'WEEKLY'
ORDER BY period_start ASC;
