# Phase 06 — How tables and indexes live on disk, and how rows reach memory

## The question

When you execute SELECT name FROM users WHERE id = 42, where is the row, how does an index find it, and what moves from storage to RAM?

**The database commonly reads and caches pages, then finds and interprets records inside them. It does not normally issue one device read per column or load the entire table for every query.**

## Reading order

| Lesson | Topic |
|---|---|
| [01 — Files, pages, and records](01-files-pages-and-records.md) | Physical storage, page layout, addresses, large values |
| [02 — Index pages and B+ trees](02-index-pages-and-bplus-trees.md) | Tree pages, heap pointers, clustered storage |
| [03 — Buffer pool and storage reads](03-buffer-pool-and-io.md) | Cache hits/misses, OS cache, eviction, visibility, dirty pages |
| [04 — Complete query walkthrough](04-query-walkthrough-and-diagrams.md) | Point lookup, sequential scan, range scan, covering index |
| [05 — PostgreSQL practice](05-postgresql-observation-lab.md) | Inspection SQL and EXPLAIN buffer interpretation |

Diagrams are Mermaid and render on GitHub. Example page locations and I/O counts are illustrative, not measurements from a running database.

## Vocabulary

| Word | Meaning |
|---|---|
| Storage/disk | Persistent storage, including SSDs |
| RAM | Memory used while programs run |
| File | Sequence of bytes managed by the operating system |
| Page/block | Database-sized storage/cache unit |
| Record/tuple | Stored row or row-version representation |
| Offset | Position measured from a starting point |
| Heap table | Storage with no maintained search-key order |
| Buffer frame | RAM location holding one cached database page |
| Index key | Value used for an index search |
| Locator | Information identifying a row/version location |
| Snapshot | Data view applicable to a query or transaction |
| Projection | Selecting requested output columns |
| I/O | Input/output work such as reads and writes |

Heap table is unrelated to the Python memory heap. Database pages differ from OS virtual-memory pages and physical device sectors.

## Two common models

| Model | Row location | Secondary B-tree leaf generally contains |
|---|---|---|
| PostgreSQL built-in heap | Heap pages separate from indexes | Indexed value and heap tuple locator |
| MySQL InnoDB | Clustered-index leaf records | Secondary value and clustered key |

These are common designs, not rules for every database/index type.

## Official references

- [PostgreSQL page layout](https://www.postgresql.org/docs/current/storage-page-layout.html)
- [PostgreSQL file layout](https://www.postgresql.org/docs/current/storage-file-layout.html)
- [PostgreSQL index-only scans](https://www.postgresql.org/docs/current/indexes-index-only-scans.html)
- [PostgreSQL TOAST](https://www.postgresql.org/docs/current/storage-toast.html)
- [PostgreSQL EXPLAIN](https://www.postgresql.org/docs/current/using-explain.html)
- [PostgreSQL buffer manager source](https://github.com/postgres/postgres/blob/master/src/backend/storage/buffer/bufmgr.c)
- [PostgreSQL B-tree notes](https://github.com/postgres/postgres/blob/master/src/backend/access/nbtree/README)
- [InnoDB indexes](https://dev.mysql.com/doc/refman/8.4/en/innodb-index-types.html)
- [InnoDB buffer pool](https://dev.mysql.com/doc/refman/8.4/en/innodb-buffer-pool.html)

The optional lab has not been executed in your database.
