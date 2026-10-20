\set ON_ERROR_STOP on
\timing on
SET search_path TO index_lab, public;
SET max_parallel_workers_per_gather = 0;
CREATE INDEX IF NOT EXISTS idx_customers_email ON customers (email);
ANALYZE customers;
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, full_name, email, city
FROM customers WHERE email = 'customer987654@example.com';
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, full_name, email, city
FROM customers WHERE email = 'customer987654@example.com';
SELECT id, full_name, email, city
FROM customers WHERE email = 'customer987654@example.com';
SELECT pg_size_pretty(pg_relation_size('customers')) AS table_main_data,
       pg_size_pretty(pg_relation_size('idx_customers_email')) AS email_index,
       pg_size_pretty(pg_indexes_size('customers')) AS all_indexes,
       pg_size_pretty(pg_total_relation_size('customers')) AS total_with_indexes;
SELECT indexname, indexdef FROM pg_indexes WHERE schemaname = 'index_lab';
