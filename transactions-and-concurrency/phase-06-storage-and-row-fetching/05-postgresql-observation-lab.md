# 5. PostgreSQL observation lab

This optional lab is for PostgreSQL, not generic SQL. It has not been run against your database. Plan shapes and numbers depend on version, data, statistics, and cache state.

## 1. Create isolated practice data

Use a practice database. This schema has a deliberately specific name to avoid touching application tables.

~~~sql
CREATE SCHEMA storage_learning_demo;

CREATE TABLE storage_learning_demo.users (
    id BIGINT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL
);

INSERT INTO storage_learning_demo.users (id, name, email)
SELECT
    g,
    'User ' || g,
    'user' || g || '@example.com'
FROM generate_series(1, 100000) AS g;

ANALYZE storage_learning_demo.users;
~~~

ANALYZE collects planner statistics. It does not mean executing your example SELECT for timing.

## 2. Inspect page size and relation sizes

~~~sql
SHOW block_size;

SELECT
    pg_relation_size('storage_learning_demo.users') AS heap_bytes,
    pg_indexes_size('storage_learning_demo.users') AS index_bytes,
    pg_total_relation_size('storage_learning_demo.users') AS total_bytes;

SELECT pg_relation_filepath('storage_learning_demo.users');
~~~

The path identifies the first segment of the main relation storage, not every associated file.

The total includes additional associated storage, so it need not equal only the displayed heap-plus-index figures in every case.

## 3. Inspect a physical tuple locator

~~~sql
SELECT ctid, id, name
FROM storage_learning_demo.users
WHERE id = 42;
~~~

An example ctid could be (7,3), but the actual result is not predictable from the ID alone.

ctid is for observation here, not a permanent reference to store in another business table.

## 4. Observe primary-key retrieval

~~~sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT name, email
FROM storage_learning_demo.users
WHERE id = 42;
~~~

EXPLAIN displays a plan. ANALYZE inside EXPLAIN executes the statement and measures it. This statement is a read-only SELECT.

Possible nodes:
- Index Scan.
- Index Only Scan for a sufficiently covered query.
- Bitmap Index Scan plus Bitmap Heap Scan.
- Seq Scan.

Read the actual output; do not assume it must match a predetermined diagram.

### Buffer interpretation

| Output | Meaning |
|---|---|
| shared hit | Access found in PostgreSQL shared buffers |
| shared read | Block read into shared buffers; OS cache may still have served it |
| shared dirtied | Block changed from clean to dirty during execution |
| shared written | Block written by this execution |
| Heap Fetches | Heap visits reported by an index-only scan |

Counts can include repeated accesses, so they are not always counts of distinct pages. Parent plan nodes can include child work; do not simply sum every number in the plan.

## 5. Compare with an email query

~~~sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT name
FROM storage_learning_demo.users
WHERE email = 'user42@example.com';
~~~

Only id has an index so far. A sequential scan is plausible.

Now create an email index:

~~~sql
CREATE INDEX users_email_idx
ON storage_learning_demo.users (email);

EXPLAIN (ANALYZE, BUFFERS)
SELECT name
FROM storage_learning_demo.users
WHERE email = 'user42@example.com';
~~~

Inspect the changed access path and buffers.

Do not interpret differences as a rigorous cold-cache benchmark. Earlier steps and index creation can warm caches.

## 6. Try coverage

~~~sql
CREATE INDEX users_email_cover
ON storage_learning_demo.users (email)
INCLUDE (name);

VACUUM (ANALYZE) storage_learning_demo.users;

EXPLAIN (ANALYZE, BUFFERS)
SELECT name
FROM storage_learning_demo.users
WHERE email = 'user42@example.com';
~~~

Run VACUUM outside an explicit transaction block. It can help establish visibility-map state where eligible; it does not guarantee a particular plan or zero heap fetches under concurrent activity.

The planner may choose among the overlapping indexes. Duplicate indexes are useful for this comparison but are not a production recommendation.

## 7. Repeat a query and inspect caching

Run the same SELECT plan again. Shared hits may replace reads if pages remain cached.

Do not clear OS caches or restart a production database for this exercise. The purpose is understanding counters, not creating a perfectly controlled benchmark.

## 8. Questions to answer from the actual output

1. Which scan was selected?
2. Is the index condition separate from a remaining filter?
3. How many rows were estimated versus returned?
4. Which buffers were hits versus reads?
5. Did the index-only plan report heap fetches?
6. Did repetition change buffer behavior?

An observed result is evidence for this run, not a universal rule for every table or workload.

## Optional cleanup

Only if you want to remove the practice objects, drop the known objects without CASCADE:

~~~sql
DROP TABLE storage_learning_demo.users;
DROP SCHEMA storage_learning_demo;
~~~

The table drop also removes its indexes. These cleanup statements are presented for you to run deliberately; they have not been executed.
