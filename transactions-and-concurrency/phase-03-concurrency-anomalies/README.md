# Phase 03 — Read phenomena and write anomalies

**Read phenomena** are observable situations where concurrent changes cause reads to return potentially unexpected or unsafe results.

They matter because applications make decisions using what they read. Temporary data, changing data, or values from incompatible moments can produce wrong decisions.

Read one section at a time:

| Order | Phenomenon | Meaning |
|---|---|---|
| 1 | Dirty read | Read another transaction's uncommitted changes |
| 2 | Non-repeatable read | Read the same row again and see a committed change |
| 3 | Phantom read | Repeat a search and see changed result membership |
| 4 | Read skew | Combine related values from incompatible moments |
| 5 | Lost update | One write overwrites another's change |
| 6 | Write skew | Different writes together break an invariant |

The last two are write anomalies rather than just read phenomena.

## 1. Dirty read

**A dirty read is reading another transaction's change before it commits.**

### Example

Committed balance: ₹1,000.

~~~sql
-- Transaction A
BEGIN;
UPDATE accounts SET balance = balance + 500 WHERE id = 1;
-- Not committed.
~~~

Transaction B, under isolation permitting dirty reads:

~~~sql
-- Transaction B
BEGIN;
SELECT balance FROM accounts WHERE id = 1;
-- May return 1500.
~~~

Then A rolls back:

~~~sql
-- Transaction A
ROLLBACK;
~~~

| Step | A | B |
|---|---|---|
| 1 | Starts from committed 1000 | |
| 2 | Changes balance to 1500, uncommitted | |
| 3 | | Reads 1500 |
| 4 | Rolls back; committed balance remains 1000 | |
| 5 | | Already used a value that never committed |

### Why bad?

A voucher requires a balance of at least ₹1,200. B grants it based on ₹1,500, but that deposit is cancelled. The committed balance never qualified.

Other harm: showing unavailable money, reports including cancelled work, downstream actions based on failed operations.

### Prevention

Read Committed or stronger prevents dirty reads. B may read the previous committed value or wait, depending on implementation.

Reading your own uncommitted changes is normal and is not a dirty read.

## 2. Non-repeatable read

**Within one transaction, reading the same row twice returns different results because another transaction updated or deleted it and committed between reads.**

### Example

~~~sql
-- A
BEGIN;
SELECT price FROM products WHERE id = 10;
-- 1000

-- B, on a different connection
BEGIN;
UPDATE products SET price = 1200 WHERE id = 10;
COMMIT;

-- A again
SELECT price FROM products WHERE id = 10;
-- May return 1200.
COMMIT;
~~~

| Step | A | B |
|---|---|---|
| 1 | Reads 1000 | |
| 2 | | Updates to 1200 |
| 3 | | Commits |
| 4 | Reads 1200 | |

A committed deletion can also cause the second read not to find the row.

### Why bad?

A reads ₹1,000 and calculates a two-item charge: 2 × 1000 = ₹2,000.

A later reads ₹1,200 and calculates the invoice: 2 × 1200 = ₹2,400.

The charge and invoice disagree.

Newer data is not inherently bad; the problem is relying on stable data when the isolation level does not guarantee it.

### Compare dirty read

| Dirty read | Non-repeatable read |
|---|---|
| Other transaction has not committed | Other transaction committed between reads |
| Data may never become permanent | Both reads can be of committed data |

Read Committed stops dirty reads but permits non-repeatable reads.

### Prevention

- Repeatable Read or stronger, subject to implementation details.
- Appropriate row locking.
- For purchase pricing, store the agreed unit price in the order item and consistently use it for charge and invoice.

Capturing a purchase price solves that business requirement; it does not change isolation guarantees.

## 3. Phantom read

**A repeated search within one transaction returns a changed set of matching rows because another transaction committed a change.**

Inserts, deletes, or updates can change membership.

### Example

| Product | Price |
|---|---:|
| Mouse | ₹500 |
| Keyboard | ₹800 |
| Headphones | ₹1,500 |

~~~sql
-- A
BEGIN;
SELECT id, name, price FROM products WHERE price < 1000;
-- Mouse and Keyboard: 2 rows.

-- B
BEGIN;
INSERT INTO products (id, name, price)
VALUES (4, 'USB cable', 300);
COMMIT;

-- A
SELECT id, name, price FROM products WHERE price < 1000;
-- May now include USB cable: 3 rows.
~~~

| Step | A | B |
|---|---|---|
| 1 | Finds 2 rows below 1000 | |
| 2 | | Inserts matching row |
| 3 | | Commits |
| 4 | Same search finds 3 rows | |

Changing Headphones from ₹1,500 to ₹900 can also make a row enter the result. A deletion or price increase can remove a matching row.

### Why bad?

A report performs:

~~~sql
SELECT COUNT(*) FROM products WHERE price < 1000;
-- 2

-- Another transaction commits a matching insert.

SELECT name, price FROM products WHERE price < 1000;
-- 3 products
~~~

It displays “Number of affordable products: 2” alongside three products.

### Compare non-repeatable read

- Non-repeatable: “This previously read row changed or disappeared.”
- Phantom: “The set matching this condition changed.”

Descriptions can overlap for some updates and deletes.

### Prevention

- Serializable prevents unsafe phantom outcomes; retries may be needed.
- A stable transaction snapshot can preserve result membership for ordinary reads.
- Supported range or predicate protection can cover conflicting changes to a search condition.

Locking only existing result rows may not prevent a new matching insert. There is no existing row representing that future insert.

The standard Repeatable Read level does not universally forbid phantoms, though some implementations prevent them for ordinary snapshot reads.

## 4. Read skew

**Related values read from incompatible moments combine into an inconsistent picture.**

### Example

| Account | Initial | After ₹200 transfer |
|---|---:|---:|
| Savings | ₹1,000 | ₹800 |
| Wallet | ₹500 | ₹700 |
| Total | ₹1,500 | ₹1,500 |

~~~sql
-- A
BEGIN;
SELECT balance FROM accounts WHERE id = 1;
-- Savings: 1000

-- B
BEGIN;
UPDATE accounts SET balance = balance - 200 WHERE id = 1;
UPDATE accounts SET balance = balance + 200 WHERE id = 2;
COMMIT;

-- A
SELECT balance FROM accounts WHERE id = 2;
-- Wallet: 700, if this read sees B's commit.
COMMIT;
~~~

| Step | A: calculate total | B: transfer |
|---|---|---|
| 1 | Reads old Savings: 1000 | |
| 2 | | Deducts 200 |
| 3 | | Credits Wallet 200 |
| 4 | | Commits both |
| 5 | Reads new Wallet: 700 | |
| 6 | Calculates 1700 | |

₹1,700 never existed as the combined committed total.

Reading old Wallet ₹500 and new Savings ₹800 instead gives ₹1,300. That total is also wrong.

### Why bad?

Financial reports, balance eligibility checks, and exports can contain related data that never existed together.

This is not a dirty read: B committed before the second read.

Unlike non-repeatable read, no row needs to be read twice.

### Prevention

Use an appropriate consistent transaction snapshot for related reads.

For this specific calculation:

~~~sql
SELECT SUM(balance)
FROM accounts
WHERE id IN (1, 2);
~~~

SUM adds the values. On an engine providing a consistent statement snapshot, this single query computes from one view.

Suitable locking can also work if it covers required data and is acquired correctly.

## 5. Lost update

**Concurrent operations read the same old value, calculate separately, and one writes a value that overwrites the other's change.**

### Example: likes

Initial count: 10. Two users each add one. Required result: 12.

~~~python
# Unsafe pseudocode
likes = read_likes(post_id)
new_likes = likes + 1
save_likes(post_id, new_likes)
~~~

This is read–modify–write: read, calculate, write.

| Step | A | B |
|---|---|---|
| 1 | Reads 10 | |
| 2 | | Reads 10 |
| 3 | Calculates 11 | |
| 4 | | Calculates 11 |
| 5 | Writes 11; commits | |
| 6 | | Writes 11; commits |

Final result: 11. One increment disappeared.

### Transactions alone are insufficient

~~~sql
BEGIN;
SELECT likes FROM posts WHERE id = 1;
-- Application calculates 11.
UPDATE posts SET likes = 11 WHERE id = 1;
COMMIT;
~~~

At isolation permitting this outcome, both can commit. Waiting for a write lock does not automatically recalculate the application's stale value.

Some implementations detect the conflict and reject a transaction, requiring a retry.

### Why bad?

- Counters undercount.
- Stock deductions disappear.
- Deposits or withdrawals are overwritten.
- Profile edits overwrite another person's changes.

Both requests can report success.

### Direct SQL increment

~~~sql
UPDATE posts
SET likes = likes + 1
WHERE id = 1;
~~~

The database performs the increment. With normal transactional write handling, two successful increments produce 10 → 11 → 12. If stronger isolation rejects a conflict, retry the transaction.

Other protection: lock before reading, version-based optimistic checks, Serializable with retries.

One-like-per-user is a separate rule, usually enforced by unique user/post membership.

## 6. Write skew

**Concurrent transactions make decisions from an earlier shared state, then update different rows in a combination that breaks a rule.**

### Doctors example

Rule: at least one doctor must remain on duty.

| Doctor | Initially on duty |
|---|---|
| Anu | Yes |
| Ravi | Yes |

~~~python
# Pseudocode
with database.transaction():
    count = count_doctors_on_duty()
    if count >= 2:
        mark_me_off_duty()
    else:
        reject_request()
~~~

| Step | A: Anu leaves | B: Ravi leaves |
|---|---|---|
| 1 | Counts 2 | |
| 2 | | Counts 2 |
| 3 | Decides leave is safe | |
| 4 | | Decides leave is safe |
| 5 | Marks Anu off duty | |
| 6 | | Marks Ravi off duty |
| 7 | Commits | |
| 8 | | Commits |

Final state: both off duty, violating the invariant.

### Compare lost update

| Lost update | Write skew |
|---|---|
| A change is overwritten | Both changes survive |
| Often conflict on the same row | Can update different rows |
| Counter loses increment | Shared staffing rule breaks |

### Why a snapshot is insufficient

Each transaction can consistently see both doctors on duty in its snapshot. Their different-row writes can still both commit under snapshot isolation.

Consistent reads do not automatically make concurrent decisions safe.

### Why locking only my row is insufficient

A locks Anu. B locks Ravi. The locks do not conflict, but the rule depends on both doctors.

### Prevention

1. **Serializable:** reject an unsafe combination. Retry the aborted transaction, which then sees only one doctor and refuses the leave.
2. **A shared locking protocol:** all relevant changes first lock the same shift record, then check staffing using a view that includes prior committed changes, then update.

~~~text
BEGIN
    Lock shared shift record
    Read relevant current staffing
    Decide whether leave is permitted
    Update doctor if permitted
COMMIT
~~~

Exact implementation depends on isolation and engine. Every operation that can break the rule must follow the protocol; an unrelated writer that skips it defeats the design.

Other cases: last administrators independently remove themselves, different purchases exceed a common budget, or separate records create overlapping bookings after both see no conflict.

## Practice

For each anomaly, identify:
1. What was read?
2. What changed concurrently?
3. Which commit occurred between operations?
4. Which business assumption failed?
5. Which protection addresses that assumption?

Next: [Isolation levels](../phase-04-isolation-levels/README.md).
