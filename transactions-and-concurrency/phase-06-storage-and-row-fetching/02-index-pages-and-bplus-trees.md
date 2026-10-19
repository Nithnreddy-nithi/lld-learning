# 2. Index pages and B+ trees

## The problem

For SELECT name FROM users WHERE id = 42, a heap without a useful index may need to examine many pages.

An **index** organizes search values so the database can locate candidates efficiently. It uses persistent space, cache space when accessed, and maintenance work on relevant writes.

## Index nodes are pages

A **B+ tree** is a balanced search structure containing many keys per node. Database B-tree implementations are commonly B+ tree-like, with engine-specific variations.

| Page type | Purpose |
|---|---|
| Root | Top-level routing |
| Internal | Separator keys and child-page references |
| Leaf | Search entries and locators or row data |

A **separator** routes a key to a child range.

~~~mermaid
flowchart TD
    ROOT["Root: separator 50"] -->|"below 50"| L["Leaf: 10, 25, 42"]
    ROOT -->|"50 or above"| R["Leaf: 50, 75, 90"]
    L -->|"42 maps to locator"| H["Heap page 7, slot 3"]
    L -. "Next leaf for range scan" .-> R
~~~

This small tree omits an internal level. Each index node and the heap page are separate database pages.

## Heap-model leaves

Conceptually:

| Indexed id | Heap locator |
|---|---|
| 10 | (2,1) |
| 25 | (9,4) |
| 42 | (7,3) |

The locator directs retrieval toward the tuple, after which visibility is checked.

Physical implementations can include duplicate-key posting lists and optimized version-chain behavior. This table simplifies those details.

**An index does not universally contain every column.**

## Why few levels can cover many rows

**Fan-out** is the number of children an internal node can reference.

Illustrative full tree:
- 200 child references per internal node.
- 200 entries per leaf.
- Root → internal → leaf can represent about 200 × 200 × 200 = 8,000,000 entries.

Actual capacity depends on sizes, occupancy, compression, and duplicates. This is an intuition, not a sizing promise.

Three levels do not imply three physical device reads: pages may be cached.

## Equality and ranges

For id = 42, descend to the candidate leaf and find the entry.

For id BETWEEN 25 AND 75:
1. Locate the range beginning.
2. Traverse ordered leaf entries.
3. Follow sibling pages as needed.
4. Stop after the range ends.
5. Fetch visible rows or covered values.

An index does not help every predicate or every ordering requirement.

## PostgreSQL heap model

Rows live in heap pages separate from indexes.

~~~text
Primary-key index → heap tuple
Email index → heap tuple
~~~

A PostgreSQL primary-key index does not turn the ordinary heap into an InnoDB-style clustered table.

## InnoDB clustered model

The clustered-index leaves contain row data. An explicit primary key normally supplies the clustered key.

Secondary entries contain the secondary key plus the clustered key:

~~~text
Email index → primary key → clustered tree → row
~~~

~~~mermaid
flowchart TD
    Q["WHERE email = target"] --> S["Secondary email leaf"]
    S --> K["Clustered key from entry: 42"]
    K --> C["Search clustered tree for 42"]
    C --> ROW["Clustered leaf holds row"]
~~~

The key-value box is explanatory; it is not a separate disk operation.

Without an explicit primary key, InnoDB chooses a suitable unique non-null key or a hidden key according to its rules.

A wide clustered key can make secondary entries larger.

## Inserts and page splits

When a relevant index page becomes full, a **page split** can redistribute entries across pages and require parent-routing updates.

That is one reason additional indexes increase write cost. Inserts and relevant updates maintain both table and index structures.

## Ordering caveat

An index scan can supply useful order to a plan, but SQL output order is guaranteed only with the appropriate ORDER BY.

Next: [Buffer pool and I/O](03-buffer-pool-and-io.md).
