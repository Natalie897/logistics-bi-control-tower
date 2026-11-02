-- Q1: SLA: only delivered orders are eligible.
SELECT COUNT(*) AS delivered_orders,
 SUM(is_late) AS late_orders,
 ROUND(100.0*SUM(CASE WHEN is_late=0 THEN 1 ELSE 0 END)/COUNT(*),2) AS on_time_pct
FROM fact_orders WHERE status='delivered';

-- Q2: Monthly on-time rate using JOIN with date dimension.
SELECT d.year_month,COUNT(*) AS delivered_orders,
 ROUND(100.0*SUM(CASE WHEN f.is_late=0 THEN 1 ELSE 0 END)/COUNT(*),2) AS on_time_pct
FROM fact_orders f JOIN dim_date d ON f.order_date_key=d.date_key
WHERE f.status='delivered' GROUP BY d.year_month ORDER BY d.year_month;

-- Q3: Regional contribution, safe one-to-many dimension join.
SELECT r.macro_region, COUNT(*) AS order_count,
 ROUND(SUM(f.order_value),2) AS gross_order_value,
 ROUND(AVG(CASE WHEN f.status='delivered' THEN f.delay_days END),2) AS avg_delay_days
FROM fact_orders f JOIN dim_region r ON f.region_key=r.region_key
GROUP BY r.macro_region ORDER BY gross_order_value DESC;

-- Q4: CTE for risk segmentation.
WITH grouped AS (
 SELECT s.service_type,COUNT(*) AS delivered_orders,SUM(CASE WHEN f.is_late=1 THEN 1 ELSE 0 END) AS late_orders
 FROM fact_orders f JOIN dim_service s ON s.service_key=f.service_key
 WHERE f.status='delivered' GROUP BY s.service_type)
SELECT service_type,delivered_orders,late_orders,
 ROUND(100.0*late_orders/delivered_orders,1) AS late_pct,
 CASE WHEN 1.0*late_orders/delivered_orders>=0.35 THEN 'High' ELSE 'Monitor' END AS risk_band
FROM grouped ORDER BY late_pct DESC;

-- Q5: ROW_NUMBER ranks states by their on-time rate (min 30 delivered).
WITH state_sla AS (
 SELECT r.state,COUNT(*) AS n,AVG(1.0-CAST(f.is_late AS REAL)) AS on_time_rate
 FROM fact_orders f JOIN dim_region r ON f.region_key=r.region_key
 WHERE f.status='delivered' GROUP BY r.state HAVING COUNT(*)>=30)
SELECT state,n,ROUND(100*on_time_rate,2) AS on_time_pct,
 ROW_NUMBER() OVER (ORDER BY on_time_rate DESC,state) AS rank_sla
FROM state_sla ORDER BY rank_sla;

-- Q6: LAG year-month delta in order value.
WITH months AS (
 SELECT d.year_month,ROUND(SUM(f.order_value),2) AS gross_value
 FROM fact_orders f JOIN dim_date d ON f.order_date_key=d.date_key
 GROUP BY d.year_month), changes AS (
 SELECT year_month,gross_value,LAG(gross_value) OVER (ORDER BY year_month) AS previous_value FROM months)
SELECT year_month,gross_value,previous_value,
 ROUND(100.0*(gross_value-previous_value)/NULLIF(previous_value,0),2) AS mom_pct
FROM changes;

-- Q7: Quality monitoring, nulls are deliberate only for canceled delivery dates.
SELECT
 SUM(CASE WHEN f.status='delivered' AND f.delivered_date IS NULL THEN 1 ELSE 0 END) AS delivered_missing_date,
 SUM(CASE WHEN f.status='canceled' AND f.is_late IS NOT NULL THEN 1 ELSE 0 END) AS canceled_wrong_sla,
 SUM(CASE WHEN f.order_value<0 THEN 1 ELSE 0 END) AS negative_order_value
FROM fact_orders f;

-- Q8: One customer may place many orders. Do not count order rows as customers.
SELECT r.macro_region,COUNT(*) AS orders_count,
 COUNT(DISTINCT f.customer_id) AS unique_customers,
 ROUND(1.0*COUNT(*)/COUNT(DISTINCT f.customer_id),2) AS orders_per_customer
FROM fact_orders f JOIN dim_region r ON r.region_key=f.region_key
GROUP BY r.macro_region ORDER BY orders_count DESC;
