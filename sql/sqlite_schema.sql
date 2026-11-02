PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS stg_customers (customer_id TEXT PRIMARY KEY, state TEXT NOT NULL, macro_region TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS stg_orders (order_id TEXT PRIMARY KEY, customer_id TEXT, order_date TEXT, promised_date TEXT, delivered_date TEXT, status TEXT, service_type TEXT, freight_value REAL);
CREATE TABLE IF NOT EXISTS stg_order_items (order_id TEXT, line_no INTEGER, sku TEXT, unit_price REAL, quantity INTEGER, PRIMARY KEY(order_id,line_no));
CREATE TABLE IF NOT EXISTS dim_date(date_key INTEGER PRIMARY KEY, calendar_date TEXT UNIQUE NOT NULL, year INTEGER, month INTEGER, year_month TEXT, weekday_name TEXT);
CREATE TABLE IF NOT EXISTS dim_region(region_key INTEGER PRIMARY KEY, state TEXT UNIQUE NOT NULL, macro_region TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS dim_service(service_key INTEGER PRIMARY KEY, service_type TEXT UNIQUE NOT NULL);
CREATE TABLE IF NOT EXISTS fact_orders (
 order_id TEXT PRIMARY KEY,
 order_date_key INTEGER NOT NULL REFERENCES dim_date(date_key),
 region_key INTEGER NOT NULL REFERENCES dim_region(region_key),
 service_key INTEGER NOT NULL REFERENCES dim_service(service_key),
 customer_id TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('delivered','canceled')),
 promised_date TEXT NOT NULL,
 delivered_date TEXT,
 items_qty INTEGER NOT NULL CHECK(items_qty>0),
 merchandise_value REAL NOT NULL CHECK(merchandise_value>=0),
 freight_value REAL NOT NULL CHECK(freight_value>=0),
 order_value REAL NOT NULL CHECK(order_value>=0),
 days_to_deliver INTEGER,
 delay_days INTEGER,
 is_late INTEGER CHECK(is_late IN (0,1) OR is_late IS NULL)
);
CREATE INDEX IF NOT EXISTS idx_fact_date ON fact_orders(order_date_key);
CREATE INDEX IF NOT EXISTS idx_fact_region ON fact_orders(region_key);
CREATE INDEX IF NOT EXISTS idx_fact_service ON fact_orders(service_key);
