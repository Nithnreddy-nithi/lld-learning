\set ON_ERROR_STOP on
SET search_path TO index_lab, public;
-- This is a teaching projection from the table, NOT a dump of index pages.
SELECT email, ctid AS current_physical_row_location
FROM customers
WHERE email IN ('customer10@example.com', 'customer100@example.com', 'customer2@example.com')
ORDER BY email;
-- A normal (non-unique) email index allows duplicates. Changes are rolled back.
BEGIN;
INSERT INTO customers (id, full_name, email, city, created_at, profile_notes)
VALUES (1000001, 'Duplicate email demo', 'customer987654@example.com',
        'Bangalore', timestamp '2026-01-01', 'Temporary demonstration');
SELECT id, full_name, email FROM customers WHERE email = 'customer987654@example.com';
ROLLBACK;
-- Existing primary-key index on id does not provide an email search index.
EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM customers WHERE id = 987654;
