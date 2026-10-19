# 3. Buffer pool, cache hits, and storage I/O

## The problem

Reading storage for every query would waste work when many requests access the same pages.

A **buffer pool** or **database buffer cache** keeps database pages in RAM. PostgreSQL calls its ordinary shared page cache shared buffers; InnoDB calls its cache the buffer pool.

A **buffer frame** is a slot in memory capable of holding a cached page.

Index pages and table pages can both be cached.

## The page request path

The execution code asks the buffer manager for a page identified by its storage object and block number.

The **buffer manager** tracks which pages occupy memory frames and coordinates access.

~~~mermaid
flowchart TD
    Q["Executor requests a page"] --> CHECK{"Page in database cache?"}
    CHECK -->|"Yes: hit"| USE["Use cached page"]
    CHECK -->|"No: miss"| FRAME["Choose an available frame"]
    FRAME --> READ["Read through storage layer"]
    READ --> FILL["Populate frame with page"]
    FILL --> USE
    USE --> ROW["Locate and examine records"]
~~~

On a hit, no page read from the storage layer is needed for that request.

A page can require lightweight coordination even on a hit. Cached does not mean no CPU work.

## Cache miss does not always mean physical SSD access

With buffered operating-system I/O:
1. The database misses its own page cache.
2. It requests file bytes from the operating system.
3. The OS may already have those bytes in its filesystem cache.
4. Only an OS miss requires fetching from underlying storage.

Some database configurations use direct I/O or other mechanisms that alter this path.

~~~mermaid
flowchart TD
    MISS["Database buffer miss"] --> MODE{"I/O path"}
    MODE -->|"Buffered"| OS{"In OS file cache?"}
    OS -->|"Yes"| COPY["Supply cached bytes"]
    OS -->|"No"| DEV["Read storage device"]
    MODE -->|"Direct I/O where configured"| DEV
    DEV --> FRAME["Fill database buffer"]
    COPY --> FRAME
~~~

This is a conceptual path. Asynchronous reads and prefetch can overlap work.

## Why reading one row can read a whole page

For the locator (7,3):
1. Obtain heap page 7.
2. Inspect item 3 in the cached page.
3. Find the stored row version.
4. Check visibility.
5. Decode requested values.

The neighboring records arrive too because page 7 is the caching/I/O unit in this model.

It is not “read only the name's 6 bytes from the SSD.”

Physical device requests may be larger, merged, split, or prefetched. Database page requests and physical storage operations are not always one-to-one.

## Memory access is not the final result

The buffer contains encoded page data, not automatically Python dictionaries.

The engine:
- Locates records.
- Checks MVCC visibility under the query's snapshot.
- Evaluates remaining conditions.
- Extracts requested columns.
- Performs plan operations such as joins or sorts if needed.
- Encodes results in the database wire protocol.

The driver receives the result and converts values into application-language objects. An ORM may then create model instances.

The application does not receive an entire raw database page for an ordinary SELECT.

## Why visibility still matters after an index match

An index identifies candidate versions, not universally the exact committed version the query may return.

A page may contain recently inserted or older updated/deleted versions. The engine uses transaction status, snapshots, and engine-specific version rules.

Depending on engine and situation, it may follow a version chain, reconstruct an older version, reject a candidate, or consult additional metadata.

This connects physical row storage to the isolation lessons.

## What if the buffer pool is full?

The buffer manager chooses replaceable frames according to its policy.

A **pin** is a short-term claim preventing a frame from being repurposed while in use. It is distinct from a transaction's row lock.

For a clean replaceable page, the cached copy can generally be discarded because a valid stored copy exists.

A **dirty page** contains modifications not yet written to its corresponding data-file location. It cannot simply be discarded. Required persistence and recovery ordering must be satisfied before its frame is reused.

Background writers can clean pages ahead of demand. Replacement is not universally a perfect least-recently-used list.

## Where WAL fits

~~~mermaid
flowchart TD
    U["Modify cached page"] --> D["Page becomes dirty"]
    U --> W["Generate WAL records"]
    W --> L["Persist required WAL"]
    D --> WRITE["Write data page later"]
    L -->|"Required before corresponding page write"| WRITE
    L --> ACK["Durable commit may be acknowledged"]
~~~

The acknowledgement node assumes the transaction's commit record and other configured requirements are satisfied.

A clean/dirty state concerns the page's relation to its data-file copy. A committed/uncommitted state concerns transaction outcome. They are different concepts.

A page can contain committed changes that are not yet in the final table file because the durable WAL supports recovery.

## Common misconceptions

| Claim | Correction |
|---|---|
| Every SELECT reads the SSD | Many requests hit cached pages |
| Database cache miss proves physical read | OS cache may serve the request |
| Index is always entirely in RAM | Index pages are cached as capacity and workload allow |
| Fetching one row reads one tiny object | Page acquisition commonly precedes record extraction |
| A buffer pin is a row lock | Their purposes and lifetimes differ |
| Result row memory equals page memory | Execution and protocol layers produce result values |

Next: [Full walkthrough](04-query-walkthrough-and-diagrams.md).
