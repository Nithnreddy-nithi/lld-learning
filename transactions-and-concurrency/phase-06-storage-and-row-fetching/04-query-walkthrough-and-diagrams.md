# 4. Complete query walkthroughs

## Scenario A: point lookup using a PostgreSQL-style heap index

~~~sql
SELECT name, email
FROM users
WHERE id = 42;
~~~

Assume:
- A primary-key B-tree is available and chosen.
- Its path is root → internal → leaf.
- Leaf entry 42 points to heap locator (7,3).
- The target version is visible.
- No extra overflow data is needed.

These are teaching assumptions, not guarantees about a production plan.

### Step by step

1. **Parse:** check SQL structure.
2. **Resolve:** identify users, its columns, types, and permissions.
3. **Plan:** compare access paths using statistics and cost estimates.
4. **Get root page:** use the buffer manager, reading only if necessary.
5. **Follow the appropriate child:** obtain the internal page.
6. **Get leaf page:** locate key 42 and its tuple locator.
7. **Get heap page 7:** again check the buffer cache first.
8. **Use slot 3:** locate the tuple bytes.
9. **Check visibility:** make sure the version is valid for the snapshot.
10. **Project:** extract name and email.
11. **Return:** encode values for the driver.

The planner does not load every row into memory to decide which plan to use.

~~~mermaid
flowchart TD
    SQL["SELECT name, email WHERE id = 42"] --> PLAN["Planner selects index scan"]
    PLAN --> ROOT["Root page"]
    ROOT --> INTERNAL["Internal page"]
    INTERNAL --> LEAF["Leaf: 42 maps to 7,3"]
    LEAF --> HEAP["Heap page 7"]
    HEAP --> SLOT["Slot 3 locates tuple"]
    SLOT --> VIS{"Visible and conditions pass?"}
    VIS -->|"Yes"| RESULT["Extract columns and send result"]
    VIS -->|"No"| NEXT["Check other candidates or return no row"]
~~~

Every page box goes through the buffer manager. The graph does not mean every arrow is a disk read.

### Illustrative cache accounting

| State | Root | Internal | Leaf | Heap | Storage-layer page requests |
|---|---|---|---|---|---:|
| All four absent | Miss | Miss | Miss | Miss | 4 |
| Upper levels cached | Hit | Hit | Miss | Miss | 2 |
| All four cached | Hit | Hit | Hit | Hit | 0 |

This counts only these four page acquisitions, not catalogs, visibility metadata, prefetch, version chains, or other query work.

Even “4 storage-layer requests” does not prove four physical device reads. OS caching and I/O implementation matter.

A second identical query can reuse pages until they are evicted. It is not guaranteed to be faster because execution, scheduling, locks, and other work also vary.

## Scenario B: no useful index

~~~sql
SELECT name FROM users WHERE email = 'nithin@example.com';
~~~

Assume no useful email index and a sequential scan is chosen.

The executor scans table pages, examines visible rows, tests email, and returns matching names. It need not load the full table at once.

~~~mermaid
flowchart TD
    S["Sequential scan"] --> P["Obtain next heap page"]
    P --> V["Check visible rows and predicate"]
    V --> MATCH["Emit matching projected values"]
    MATCH --> MORE{"More pages needed?"}
    MORE -->|"Yes"| P
    MORE -->|"No"| END["Finish"]
~~~

Without an appropriate stopping condition or a provable uniqueness shortcut, finding one matching row is not universally enough to end the scan.

A primary-key index on id does not automatically make an email-only equality lookup efficient.

## Scenario C: range scan

~~~sql
SELECT id, name
FROM users
WHERE id BETWEEN 40 AND 80
ORDER BY id;
~~~

A suitable index plan can locate the first qualifying key, traverse leaves in order, and fetch corresponding rows.

In the heap model, nearby index entries can point to scattered heap pages. In the clustered model, logical leaf proximity groups rows by the clustered key.

When many heap locations qualify, a bitmap heap scan can collect candidates and visit heap pages in a more organized order. The optimizer might prefer this or a sequential scan.

The presence of an index does not force its use.

## Scenario D: covering and index-only scans

A **covering index** contains the values needed for a particular query.

PostgreSQL example:

~~~sql
CREATE INDEX users_email_cover
ON users (email)
INCLUDE (name);

SELECT name
FROM users
WHERE email = 'nithin@example.com';
~~~

The index contains the search key email and included payload name.

But coverage alone does not guarantee zero heap accesses. PostgreSQL must establish MVCC visibility. Its visibility map can certify an entire heap page as all-visible; otherwise an index-only scan can still fetch the heap to check.

~~~mermaid
flowchart TD
    I["Find covering index entry"] --> VM{"Heap page marked all-visible?"}
    VM -->|"Yes"| OUT["Return indexed values"]
    VM -->|"No"| H["Visit heap for visibility check"]
    H --> CHECK{"Candidate visible?"}
    CHECK -->|"Yes"| OUT
    CHECK -->|"No"| SKIP["Skip candidate"]
~~~

SELECT * often requires columns absent from the index, so a narrow query can enable different plans. Do not add wide payload columns indiscriminately: they enlarge indexes and write work.

## Scenario E: InnoDB secondary lookup

For email search:
1. Traverse secondary email index.
2. Extract clustered key, for example id 42.
3. Traverse clustered tree for 42.
4. Read row from clustered leaf.
5. Apply visibility and remaining conditions.

A covering secondary index can avoid ordinary full-row lookup when its values suffice, subject to engine-specific visibility handling. Do not transfer PostgreSQL visibility-map mechanics to InnoDB.

## When scanning can be cheaper

If most rows qualify, repeatedly retrieving scattered heap pages through an index can cost more than scanning the table.

The optimizer considers estimates influenced by table size, selectivity, ordering, cache assumptions, and statistics.

**Selectivity** describes how much of the table a condition matches; the fewer rows it matches, the more selective it is in the common usage here.

## Interview answer

Tables and indexes are persisted in page-oriented structures. The query plan chooses how to find candidate rows. The buffer manager serves cached pages or reads them through storage. A heap index points toward heap tuple locations; InnoDB secondary entries point through the clustered key. The executor checks visibility, extracts requested columns, and sends values to the driver.

Next: [Observation lab](05-postgresql-observation-lab.md).
