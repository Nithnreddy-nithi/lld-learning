# 1. Files, pages, and records

## Start with a table

~~~sql
CREATE TABLE users (
    id BIGINT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(200)
);
~~~

| id | name | email |
|---|---|---|
| 10 | Anu | anu@example.com |
| 42 | Nithin | nithin@example.com |
| 75 | Ravi | ravi@example.com |

The displayed grid is logical. Physical storage contains binary records, metadata, and other structures, not an Excel-like rectangle.

## Files and pages

A database maps a table to files or tablespace structures. A **tablespace** is a storage container whose details depend on the engine.

A table is not universally exactly one file. There can be segments, partitions, metadata files, overflow storage, and indexes.

For PostgreSQL's ordinary heap:
- Tables and indexes have separate physical storage.
- Large relations can be split into file segments.
- Additional forks support free-space and visibility information.
- Catalogs map SQL objects to storage.

A **catalog** stores metadata such as object identifiers, columns, and types.

~~~mermaid
flowchart TD
    T["Logical users table"] --> C["Catalog maps object to storage"]
    C --> F["Table files or segments"]
    F --> P0["Page 0"]
    F --> P1["Page 1"]
    F --> PN["Other pages"]
    P1 --> R["Several stored row versions"]
~~~

## Why pages?

Pages group bytes into useful storage and cache units. Reading tiny fields separately would create excessive I/O bookkeeping.

Suppose a page is **8 KiB = 8,192 bytes**. PostgreSQL usually uses this size; it is not universal.

If a row takes roughly 200 bytes, ignoring overhead:

~~~text
8192 / 200 = 40 whole rows, with some space left
~~~

Actual capacity depends on headers, slot entries, alignment, free space, variable-sized fields, and versions. This estimate is not an exact row-count formula.

Reading a page brings several records into RAM even if only one is requested.

## Inside a page

A common slotted-page design has:

| Region | Purpose |
|---|---|
| Header | Status, free-space boundaries, recovery metadata |
| Slot directory | Locations of records inside the page |
| Free space | Room for changes |
| Record area | Encoded row versions |
| Optional special area | Access-method-specific metadata |

A **slot** identifies where a record is located within the page.

~~~mermaid
flowchart TD
    H["Page header"] --> S["Slot directory"]
    S --> FREE["Free space"]
    FREE --> DATA["Record area"]
    S -. "Slot 3 identifies offset and length" .-> ROW["One row version"]
    DATA --> ROW
~~~

This is conceptual, not a byte-accurate universal layout. PostgreSQL calls its directory entries item identifiers.

Records can move within a page during compaction while directory entries track their new offsets.

## Physical locator versus business key

An illustrative PostgreSQL heap locator is **(7,3)**:

1. Locate heap block 7.
2. Use item identifier 3.
3. Follow its offset to the record bytes.

The business key id = 42 is not the same as physical location (7,3). Neither is a permanent RAM address.

Do not use PostgreSQL ctid as a permanent business ID: updates and table rewrites can change row-version locations.

## Page addressing

For a simplified single-file layout with no extra file header:

~~~text
Page size = 8192 bytes
Block number = 7
Starting offset = 7 × 8192 = 57344 bytes
~~~

Real engines account for segments and their own layout. The filesystem and SSD translate logical file requests further; this formula does not identify a flash cell.

## Row encoding

A row commonly contains:
- A row/version header.
- NULL information.
- Type-specific binary values.
- Variable-length information and alignment padding.
- MVCC metadata used for visibility.

The engine uses the schema to decode bytes; each row need not repeat column names before its values.

Large values may be compressed or stored out of line with references in the main row. PostgreSQL uses TOAST; other engines have their own overflow mechanisms.

Fetching a small row does not necessarily read an entire large document. Requesting an out-of-line value can require more pages.

## Is a table stored in primary-key order?

Not universally:
- PostgreSQL heap storage is not continuously sorted by primary key.
- InnoDB clustered-index leaves contain row records in logical clustered-key order.

Logical order does not guarantee physical adjacency of all bytes on a device.

Next: [Indexes](02-index-pages-and-bplus-trees.md).
