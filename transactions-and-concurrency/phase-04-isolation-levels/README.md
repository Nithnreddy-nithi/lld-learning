# Phase 04 — Isolation levels

An **isolation level** specifies guarantees about how concurrent transactions interact. It does not replace business rules, constraints, or correct queries.

## 1. Read Uncommitted

The weakest standard level. **It permits reading another transaction's uncommitted changes.** It allows dirty reads but does not require every read to be dirty.

### Example

~~~sql
-- A
BEGIN;
UPDATE accounts SET balance = balance + 500 WHERE id = 1;
-- Committed balance was 1000. No commit yet.

-- B, at isolation permitting dirty reads
SELECT balance FROM accounts WHERE id = 1;
-- May see 1500.

-- A
ROLLBACK;
~~~

B might use ₹1,500 although the committed balance remains ₹1,000.

### Guarantees and limitations

Dirty, non-repeatable, and phantom reads are not prevented by the standard level. There is no general guarantee against read skew, lost updates, or write skew.

This does not disable transactions or atomicity. Writes may still use locks; it does not mean every write can freely overwrite another's uncommitted work.

### Why use it?

Some implementations reduce read/write waiting at the cost of unreliable reads. But fast reads do not require dirty reads: MVCC can often serve committed versions while writers work.

Implementation matters. PostgreSQL treats a requested Read Uncommitted level as Read Committed, so dirty reads do not actually become available there.

Interview answer: distinguish the standard's minimum guarantee from the chosen engine's implementation.

## 2. Read Committed

**You cannot read another transaction's uncommitted changes. But subsequent queries can see newer committed data.**

### Preventing dirty reads

~~~sql
-- A
BEGIN;
UPDATE accounts SET balance = balance + 500 WHERE id = 1;
-- No commit.

-- B
SELECT balance FROM accounts WHERE id = 1;
~~~

B cannot read A's unfinished ₹1,500. Depending on implementation, B reads the previous committed ₹1,000 or waits for A and reads an appropriate committed value.

Reading your own writes is allowed.

### Data can change between queries

| Step | A | B |
|---|---|---|
| 1 | | Begins; reads 1000 |
| 2 | Adds 500 | |
| 3 | Commits | |
| 4 | | Reads 1500 |
| 5 | | Commits |

Both reads use committed data. This is a non-repeatable read.

### Statement-level snapshots

A snapshot is a view of data from a particular point in time.

In an implementation using statement snapshots:

1. Query 1 gets the committed view at its start.
2. Another transaction commits.
3. Query 2 gets a newer committed view.

One query's view can be stable without the entire transaction having one stable view.

Other engines use locking or configurable behavior, so “Read Committed” does not specify every internal detail.

### Remaining anomalies

| Phenomenon | Can occur? |
|---|---|
| Dirty read | No |
| Non-repeatable read | Yes |
| Phantom read | Yes |
| Read skew across statements | Yes |
| Unsafe read–modify–write lost update | Yes |
| Write skew | Yes |

Queries, locks, and engine specifics affect actual outcomes.

Read Committed can suit operations that tolerate newer values between statements. Stronger requirements can use conditional updates, constraints, explicit locks, or stronger isolation.

## 3. Repeatable Read

**A row you previously read cannot change or disappear on a repeated read because another transaction committed a change.**

It prevents dirty and non-repeatable reads.

### Product price example

~~~sql
-- A, configured for Repeatable Read
BEGIN;
SELECT price FROM products WHERE id = 10;
-- 1000

-- B
BEGIN;
UPDATE products SET price = 1200 WHERE id = 10;
COMMIT;

-- A
SELECT price FROM products WHERE id = 10;
-- 1000 in the stable snapshot example.
~~~

This sequence assumes snapshot behavior; in a lock-based implementation B may wait instead.

### Snapshot implementation

A establishes a snapshot and ordinary reads continue using it. B can commit ₹1,200, while A still sees ₹1,000. A new transaction can see the newer price.

Snapshot establishment timing varies. Do not assume every engine establishes it at BEGIN.

### Lock-based implementation

1. A reads and retains an appropriate read lock.
2. B's conflicting write waits.
3. A reads the unchanged value.
4. A finishes, releasing the lock.
5. B updates and commits.

Both approaches protect repeatability through different mechanisms.

### Phantoms

The standard Repeatable Read level does not universally prevent phantom reads.

~~~sql
SELECT price FROM products WHERE id = 10;
SELECT * FROM products WHERE price < 1000;
~~~

Stabilizing an existing row is different from protecting membership of an entire search condition.

A transaction-wide snapshot can also stabilize ordinary search results and prevent phantoms for those reads. Implementations may therefore provide stronger guarantees than the standard minimum.

### Remaining risks

Snapshot-based Repeatable Read can permit write skew: both doctors read the same staffing snapshot and update different rows.

Ordinary reads, locking reads, and writes may follow different visibility rules. Do not assume a stable earlier SELECT makes a later decision-and-write safe.

| Question | Answer |
|---|---|
| Dirty reads? | Prevented |
| Non-repeatable reads? | Prevented |
| Standard guarantee against phantoms? | No |
| Implementations can prevent ordinary-read phantoms? | Yes |
| Equivalent to Serializable? | No |

## 4. Serializable

**Successfully committed transactions must have an outcome equivalent to some execution in which they ran one at a time.**

Execution can overlap; the outcome must be serializable.

### Doctors example

At least one doctor must remain on duty.

If Anu goes first, she leaves and Ravi must stay. If Ravi goes first, he leaves and Anu must stay.

There is no valid sequential order of the correct check-and-update transactions in which both leave.

Therefore, Serializable must prevent both transactions from committing that outcome.

### Possible concurrent execution

| Step | A: Anu | B: Ravi |
|---|---|---|
| 1 | Reads 2 doctors | |
| 2 | | Reads 2 doctors |
| 3 | Marks Anu off duty | |
| 4 | | Tries to mark Ravi off duty |
| 5 | Commits | |
| 6 | | Aborted for serialization conflict |

This is illustrative. Which transaction fails, and when, depends on implementation.

A **serialization failure** means the transaction could not be allowed to finish while maintaining Serializable guarantees.

### Retry the whole transaction

~~~python
# Pseudocode
for attempt in range(3):
    try:
        with database.transaction(isolation="serializable"):
            count = count_on_duty_doctors()

            if count <= 1:
                raise CannotLeave("One doctor must remain")

            mark_off_duty(doctor_id)

        break

    except SerializationFailure:
        if attempt == 2:
            raise
~~~

On retry, a fresh transaction reads current staffing. If only Ravi remains, he cannot leave.

Do not retry only the final UPDATE: that would reuse a decision based on the rejected transaction's reads.

CannotLeave is a business rejection. SerializationFailure is a potentially retryable concurrency failure. Production retries also need bounded attempts, suitable backoff, and careful handling of external side effects.

### Does it lock the entire database?

No. Engines can use locks, snapshots with read/write dependency detection, or combinations. Independent transactions can still progress concurrently.

### Does it fix wrong logic?

No. If the application never checks staffing, sequentially executing its updates can also leave nobody on duty. Serializable preserves interactions; it does not invent the invariant check.

### Costs

Waiting, retained locks or dependency-tracking resources, aborted work, and retries can increase latency or resource use. The exact cost depends on the workload and engine.

## Standard minimum comparison

| Level | Dirty read | Non-repeatable read | Phantom read |
|---|---|---|---|
| Read Uncommitted | Allowed | Allowed | Allowed |
| Read Committed | Prevented | Allowed | Allowed |
| Repeatable Read | Prevented | Prevented | Allowed |
| Serializable | Prevented | Prevented | Prevented |

“Allowed” means the level does not forbid it, not that it must happen. Engines can provide stronger protection.

Serializable also prevents write-skew outcomes that cannot arise in a valid sequential execution of those transactions.

## Interview reasoning

Do not answer every race with “use a transaction.” Identify the invariant, the reads informing the decision, concurrent writes that invalidate it, and the necessary protection.

Next: [Durability techniques](../phase-05-durability/README.md).
