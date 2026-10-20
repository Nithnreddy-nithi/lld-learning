\set ON_ERROR_STOP on
\timing on
SET search_path TO index_lab, public;
-- Makes this experiment repeatable after running the later scripts.
DROP INDEX IF EXISTS idx_customers_email;
-- One worker makes rows-removed easier to understand; no scan is forced.
SET max_parallel_workers_per_gather = 0;
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, full_name, email, city
FROM customers WHERE email = 'customer987654@example.com';
-- Repeat to see the effect of cached pages.
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, full_name, email, city
FROM customers WHERE email = 'customer987654@example.com';
SELECT id, full_name, email, city
FROM customers WHERE email = 'customer987654@example.com';
