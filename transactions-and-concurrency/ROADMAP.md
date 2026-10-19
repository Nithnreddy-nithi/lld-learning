# Complete SDE1 transactions and concurrency roadmap

Priority: **Essential** means study in the first pass. **Later** means learn after the essentials.

The numbered roadmap below preserves the original scope. The folder phases group the completed teaching material into a convenient reading order; their numbers are not a claim that all 19 roadmap areas have already been taught.

## 1. Foundations — Essential

- What a database transaction is.
- Why a single business operation can require multiple queries.
- Problems caused by partially completed operations.
- Transaction boundaries: where a transaction starts and ends.
- BEGIN, COMMIT, ROLLBACK.
- Autocommit and explicit transactions.
- Successful versus failed transactions.
- Transactions involving one row, many rows, or multiple tables.

Example: transfer ₹500 between accounts without losing or creating money.

## 2. ACID properties — Essential

- Atomicity: changes commit together or none commit.
- Consistency: preserve database rules and business invariants.
- Isolation: control interactions between concurrent transactions.
- Durability: preserve committed changes after covered failures.
- What ACID guarantees and what application code must handle.
- Database consistency versus distributed-system consistency.
- Why ACID does not automatically prevent every concurrency bug.

## 3. Transaction control and failure handling — Essential

- Commit only after the complete operation succeeds.
- Roll back on failure; handle exceptions correctly.
- Connection closure before commit.
- Transaction state after query errors: engine-specific behavior.
- Savepoints and partial rollback.
- Why a savepoint is not an independently committed nested transaction.
- Transaction timeouts.
- Short transactions; avoid slow work and network calls inside them.
- Why rollback cannot undo an external email or payment API call.

## 4. Concurrency fundamentals — Essential

- Concurrency versus parallelism.
- Multiple requests accessing shared mutable state.
- Race conditions, critical sections, interleaving.
- Unsafe read → check → write sequences.
- Why sequentially correct code can fail concurrently.
- Application memory versus shared database state.
- Why one process's lock does not coordinate every server.

Examples: last seat, last item, simultaneous withdrawals, counter increments.

## 5. Concurrency anomalies — Essential

- Lost update.
- Dirty read.
- Non-repeatable read.
- Phantom read.
- Write skew.
- Inconsistent reads, including read skew.

For each: construct an interleaving, explain the harm, determine whether a transaction alone helps, and identify a suitable isolation level, lock, constraint, or query change.

## 6. Isolation levels — Essential

- Read Uncommitted, Read Committed, Repeatable Read, Serializable.
- Anomalies each level addresses.
- Stronger isolation, concurrency costs, and retries.
- Statement-level versus transaction-level snapshots.
- Database-specific behavior, especially Repeatable Read.
- Serializable failures and whole-transaction retries.
- Choose protection based on the business invariant.

Later: snapshot isolation in detail, dependency graphs, formal anomaly definitions.

## 7. Database locking — Essential

- Shared/read and exclusive/write locks.
- Row and table locks; compatibility.
- Acquisition, release, waiting, lock wait timeouts.
- Lock lifetime.
- Blocking versus deadlock.
- Indexes and query plans can affect lock scope.

Later: intention locks, supported lock escalation, range/gap/predicate protection, advisory locks.

## 8. Pessimistic concurrency control — Essential

Lock relevant data before deciding and changing it.

- SELECT ... FOR UPDATE.
- Read and update in the same transaction.
- Recheck conditions using an appropriate current view after obtaining protection.
- Consistent lock order.
- Waiting for conflicting locks.
- Why an absent row cannot generally be protected merely by locking existing rows.
- When pessimistic locking fits.

Later: NOWAIT, SKIP LOCKED, claiming background jobs.

Practice: prevent two users from booking one seat.

## 9. Optimistic concurrency control — Essential

Reject an update if the record changed after it was read.

- Version columns and expected-version conditions.
- Affected-row count.
- Conflict detection.
- Retry versus return a conflict.
- Optimistic versus pessimistic locking.
- Timestamp-check limitations.

~~~sql
UPDATE products
SET price = 120,
    version = version + 1
WHERE id = 10
  AND version = 3;
~~~

Zero affected rows can mean the expected version no longer matches; a missing record can also cause zero rows.

## 10. Atomic SQL operations — Essential

- Direct SQL increments/decrements.
- Conditional updates and affected-row checks.
- Avoid separate application-side read/write calculations.
- Group related records in a transaction.

~~~sql
UPDATE inventory
SET stock = stock - 1
WHERE product_id = 10
  AND stock > 0;
~~~

Explain why this avoids a separate stock-check race, how success is detected, and why creating an order alongside it still needs one transaction.

## 11. Constraints as concurrency protection — Essential

- Primary keys, unique constraints, foreign keys, NOT NULL, CHECK.
- Composite uniqueness.
- Why check-then-insert races.
- Let the database reject invalid writes and handle violations.
- Constraints complement transaction logic.

Rules: unique email, one like per user/post, one active booking per seat/show, non-negative inventory. Some rules need filtered uniqueness or another engine-appropriate design.

## 12. Deadlocks — Essential

- Circular waiting.
- Detection and victim transaction abort.
- Retry the entire transaction.
- Consistent lock order; keep transactions short.
- Deadlock versus slow query versus lock timeout.

Practice: transfers lock the same accounts in opposite orders.

## 13. MVCC basics — Essential

Multi-Version Concurrency Control keeps data versions.

- Row versions and snapshots.
- Readers can often avoid blocking writers.
- Ordinary reads versus locking reads.
- MVCC does not remove write conflicts or deadlocks.
- Long transactions can retain old versions.

Later: vacuum/purge, visibility internals, transaction identifiers.

## 14. Retries and idempotency — Essential

- Retryable failures: deadlocks and serialization failures.
- Retry the whole operation with bounded attempts.
- Backoff and jitter.
- Duplicate side effects.
- Idempotency: repeated requests produce the same intended effect.
- Idempotency keys and database uniqueness.
- Simultaneous requests with the same key.
- Commit succeeds but response is lost.

Practice: retry order creation without creating a second order.

## 15. Application-level concurrency — Essential

- Processes, threads, asynchronous tasks.
- Thread-shared state versus process-local state.
- Mutexes, semaphores, thread-safe structures.
- Compound operations can be unsafe even if individual steps are safe.
- In-memory locks do not coordinate multiple servers.
- Async code can have races.
- Connection pools and correct connection/transaction ownership.

Later: condition variables, read/write locks, starvation, fairness, livelock.

## 16. APIs and background jobs — Essential

- One business operation as one transaction.
- Costs of wrapping every request in a transaction.
- Trigger work requiring committed data after commit.
- Post-commit callbacks and their failure window.
- Duplicate job delivery and idempotent handlers.
- Concurrent workers claiming the same record.
- Stale data; meaningful conflict/retry responses.
- Gap between database commit and message publication.

Later: transactional outbox after understanding that gap.

## 17. Testing concurrency — Essential

- Commit, rollback, and constraint violations.
- Separate connections for concurrent transactions.
- Deliberately reproduce a race.
- Coordinate execution so conflicting steps overlap.
- Simultaneous stock updates and duplicate requests.
- Optimistic conflicts and retry handling.
- Sequential tests miss races.
- Use production-relevant database behavior.

## 18. Debugging and performance — Essential

- Lock contention, blockers, long transactions.
- Basic deadlock reports.
- Transaction duration, lock wait duration, retry/conflict rates.
- Missing indexes can increase work and contention.
- Connection-pool exhaustion from long transactions.
- Stronger isolation or more locks is not automatically the right fix.

## 19. Topics to postpone

- Distributed transactions and two-phase commit.
- Sagas.
- Distributed locks, leases, fencing tokens.
- Consensus algorithms.
- Replication internals and cross-region guarantees.
- Detailed WAL/crash-recovery internals.
- Formal serializability theory.
- Lock-free algorithms and compare-and-swap internals.

The durability phase gives a conceptual expansion of logging and recovery because you specifically requested all durability techniques. It does not require implementing a database engine.

## Practical target

Independently explain and implement safe money transfers, inventory decrements, seat booking, unique creation, version-based updates, and duplicate-request handling—including concurrent execution and failures.
