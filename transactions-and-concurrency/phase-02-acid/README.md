# Phase 02 — ACID

ACID names four properties: **Atomicity, Consistency, Isolation, Durability**. Each addresses a different question.

## Lesson 1: atomicity

**Atomicity means a transaction's changes commit as one unit or none of them commit.**

“Indivisible” means no permanently committed half-transaction.

### Transfer example

| Account | Before | After successful transfer |
|---|---:|---:|
| Nithin | ₹1,000 | ₹800 |
| Ravi | ₹500 | ₹700 |
| Total | ₹1,500 | ₹1,500 |

~~~sql
BEGIN;
UPDATE accounts SET balance = balance - 200 WHERE id = 1;
UPDATE accounts SET balance = balance + 200 WHERE id = 2;
COMMIT;
~~~

If the application detects failure after the deduction and rolls back, the original balances are restored.

**Executing a change is different from committing it.**

### Atomicity does not detect every business failure

~~~sql
UPDATE accounts
SET balance = balance + 200
WHERE id = 999;
~~~

If account 999 does not exist, the statement can affect zero rows. Committing after that may permanently save only a real deduction and no real credit. Atomicity was not violated: the database committed exactly the successful changes the application instructed it to commit.

~~~python
# Pseudocode
with database.transaction():
    deduct_money(sender_id, amount)
    updated_rows = credit_money(receiver_id, amount)

    if updated_rows != 1:
        raise TransferFailed("Receiver account not found")
~~~

The application detects the business failure and the helper rolls back when the exception escapes.

### Failure cases

- Connection closes before commit: unfinished transaction is normally aborted.
- Database crashes: recovery must not leave an unfinished transaction partially committed.
- Commit succeeds but confirmation is lost: the transaction may already be committed. This is an uncertain outcome for the client, not permission to assume rollback.

### External side effects

~~~text
BEGIN
    Create order in database
    Send email through external service
ROLLBACK
~~~

The database order is undone; the sent email remains. It did not participate in the database transaction. External payments, messages, and emails need their own coordination and duplicate-handling designs.

## Lesson 2: consistency

A **state** is stored data at a particular moment.

**Consistency means a correct transaction moves the database from one valid state to another, preserving required rules.**

An **invariant** is a rule that must remain true.

### Non-negative balance

Nithin has ₹1,000 and requests ₹1,200:

~~~text
1000 - 1200 = -200
~~~

If negative balances are forbidden, that result is invalid.

A **constraint** is a database-enforced rule:

~~~sql
CREATE TABLE accounts (
    id INTEGER PRIMARY KEY,
    balance INTEGER NOT NULL CHECK (balance >= 0)
);
~~~

| Definition | Rule |
|---|---|
| PRIMARY KEY | Unique, non-missing account identifier |
| NOT NULL | Balance must be present |
| CHECK | Balance cannot be negative |

The database rejects a violating update. The application handles the error and rolls back appropriately.

### Some rules require correct application logic

~~~sql
BEGIN;
UPDATE accounts SET balance = balance - 200 WHERE id = 1;
UPDATE accounts SET balance = balance + 100 WHERE id = 2;
COMMIT;
~~~

Final balances are ₹800 and ₹600, total ₹1,400 instead of ₹1,500.

The non-negative constraints accept both balances. The transaction is atomic, but incorrect transfer logic broke money conservation.

Use the same amount for debit and credit, verify the intended records, and apply appropriate concurrency protection.

| Application | Invariant |
|---|---|
| Inventory | Stock cannot be negative |
| Users | Unique username/email where required |
| Orders | Each item refers to an existing order |
| Booking | No duplicate active booking for one seat and show |

These rules may require constraints, application logic, and concurrency handling together.

ACID consistency is about preserving invariants. Distributed-system consistency often concerns how different copies or readers observe writes; the terms should not be treated as interchangeable.

## Lesson 3: isolation

**Isolation controls how concurrent transactions observe and affect each other.**

**Concurrent** means operations overlap in time; they do not need to execute at precisely the same instant.

### Two withdrawals

Balance: ₹1,000. A withdraws ₹700. B withdraws ₹500.

~~~python
# Pseudocode
begin_transaction()
balance = read_balance(account_id)
if balance >= withdrawal_amount:
    set_balance(account_id, balance - withdrawal_amount)
commit()
~~~

At isolation permitting this interaction:

| Step | A | B |
|---|---|---|
| 1 | Reads 1000 | |
| 2 | | Reads 1000 |
| 3 | Checks 1000 >= 700 | |
| 4 | | Checks 1000 >= 500 |
| 5 | Writes 300; commits | |
| 6 | | Writes 500; commits |

Both report success, but the final balance reflects only B's withdrawal. This is a **lost update**.

A write lock might make B wait without recalculating B's stale application-side value.

A safe sequential outcome is A succeeds, leaving ₹300, then B is rejected. If B succeeds first, A is rejected instead.

### Isolation does not require no overlap

Databases can use:

- Locks: conflicting operations wait.
- Versions: reads use an appropriate stored version.
- Conflict detection: unsafe concurrent work is rejected.

Isolation levels choose permitted interactions. The standard levels are Read Uncommitted, Read Committed, Repeatable Read, and Serializable.

**Atomicity groups one transaction's changes. Isolation controls interactions between transactions.**

The anomalies and isolation phases explain these in depth.

## Lesson 4: durability

**Once a durable commit is confirmed, its changes survive failures covered by the database's guarantee, such as process crash and restart.**

After a confirmed ₹200 transfer, a restart must preserve ₹800 for Nithin and ₹700 for Ravi.

### Why memory is insufficient

**RAM** is temporary working storage. Power loss can erase it.

**Persistent storage**, such as an SSD, retains data without power. The database must persist enough recovery information before acknowledging a durable commit.

A common technique is **write-ahead logging (WAL)**:

1. Generate recovery records.
2. Persist required log records, including the commit.
3. Confirm success.
4. Write changed data pages to final locations as needed.

A **page** is a block of database storage. Recovery can restore committed changes from logs if some pages were not yet written.

### Commit acknowledgement can be lost

1. Application sends COMMIT.
2. Database commits durably.
3. Connection fails before the response arrives.

The operation may already have succeeded. Retrying blindly can duplicate it. Idempotency keys and operation-status lookup address this later.

### Limits

Durability depends on settings and storage. An unsafe flush setting can allow acknowledged commits to be lost. Destruction of the only disk may destroy both logs and data. Replication and backups cover additional failures.

## Compare the four properties

| Property | Core question |
|---|---|
| Atomicity | Did all changes commit together or none commit? |
| Consistency | Were required invariants preserved? |
| Isolation | Were concurrent interactions adequately controlled? |
| Durability | Does a confirmed commit survive covered failures? |

Transactions are powerful, but they do not invent business checks, include arbitrary external services, or make every retry safe.

Next: [Read phenomena and write anomalies](../phase-03-concurrency-anomalies/README.md). Durability is expanded into [ten lessons](../phase-05-durability/README.md).
