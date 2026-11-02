-- Optional Postgres implementation. Import CSVs from data/powerbi in this order:
-- dim_date, dim_region, dim_service, fact_orders (with headers).
CREATE SCHEMA IF NOT EXISTS dwh;
CREATE TABLE IF NOT EXISTS dwh.dim_date(date_key INTEGER PRIMARY KEY,calendar_date DATE UNIQUE NOT NULL,year INTEGER,month INTEGER,year_month TEXT,weekday_name TEXT);
CREATE TABLE IF NOT EXISTS dwh.dim_region(region_key INTEGER PRIMARY KEY,state TEXT UNIQUE NOT NULL,macro_region TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS dwh.dim_service(service_key INTEGER PRIMARY KEY,service_type TEXT UNIQUE NOT NULL);
CREATE TABLE IF NOT EXISTS dwh.fact_orders(
 order_id TEXT PRIMARY KEY,
 order_date_key INTEGER REFERENCES dwh.dim_date(date_key),
 region_key INTEGER REFERENCES dwh.dim_region(region_key),
 service_key INTEGER REFERENCES dwh.dim_service(service_key),
 customer_id TEXT NOT NULL,
 status TEXT NOT NULL,
 promised_date DATE NOT NULL,
 delivered_date DATE,
 items_qty INTEGER NOT NULL,
 merchandise_value NUMERIC(14,2) NOT NULL,
 freight_value NUMERIC(14,2) NOT NULL,
 order_value NUMERIC(14,2) NOT NULL,
 days_to_deliver INTEGER,
 delay_days INTEGER,
 is_late INTEGER
);
CREATE INDEX IF NOT EXISTS ix_fact_date ON dwh.fact_orders(order_date_key);
