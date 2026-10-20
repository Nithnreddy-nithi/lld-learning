\set ON_ERROR_STOP on
\timing on
-- Only this lab schema is replaced when you rerun setup.
DROP SCHEMA IF EXISTS index_lab CASCADE;
CREATE SCHEMA index_lab;
SET search_path TO index_lab, public;
CREATE TABLE customers (
    id bigint PRIMARY KEY,
    full_name text NOT NULL,
    email text NOT NULL,
    city text NOT NULL,
    created_at timestamp NOT NULL,
    profile_notes text NOT NULL
);
INSERT INTO customers (id, full_name, email, city, created_at, profile_notes)
SELECT n,
       'Customer ' || n,
       'customer' || n || '@example.com',
       (ARRAY['Bangalore','Hyderabad','Chennai','Pune','Delhi'])[1 + ((n - 1) % 5)::int],
       timestamp '2026-01-01' + (n % 365) * interval '1 day',
       repeat('Example customer profile. ', 4)
FROM generate_series(1, 1000000) AS series(n);
ANALYZE customers;
DO $$
BEGIN
    IF (SELECT count(*) FROM customers) <> 1000000 THEN
        RAISE EXCEPTION 'Expected exactly one million rows';
    END IF;
    IF (SELECT count(*) FROM customers WHERE email = 'customer987654@example.com') <> 1 THEN
        RAISE EXCEPTION 'Expected exactly one target customer';
    END IF;
END $$;
SELECT count(*) AS total_rows FROM customers;
SELECT id, full_name, email, city FROM customers ORDER BY id LIMIT 5;
SELECT indexname, indexdef FROM pg_indexes WHERE schemaname = 'index_lab';
