# Phase 01 — Transaction foundations

## Lesson 1: what is a transaction?

### The concrete problem

Nithin has ₹1,000. Ravi has ₹500. Transfer ₹200 from Nithin to Ravi.

| Account | Before | Required result |
|---|---:|---:|
| Nithin | ₹1,000 | ₹800 |
| Ravi | ₹500 | ₹700 |
| Total | ₹1,500 | ₹1,500 |

The application needs two changes: subtract from one account and add to the other.

~~~sql
UPDATE accounts
SET balance = balance - 200
WHERE id = 1;
~~~

If that deduction is saved permanently and the application crashes before the credit, the balances become ₹800 and ₹500. The total becomes ₹1,300. Money was deducted without being credited.

Each SQL statement can be individually valid while the business operation remains incomplete.

### The solution

A **database transaction** is a group of database operations treated as one unit of work.

Tell the database: “These changes belong together. Save both or cancel both.”

~~~sql
BEGIN;

UPDATE accounts
SET balance = balance - 200
WHERE id = 1;

UPDATE accounts
SET balance = balance + 200
WHERE id = 2;

COMMIT;
~~~

| Command | Meaning |
|---|---|
| BEGIN | Start a transaction |
| COMMIT | Make the transaction's changes permanent |
| ROLLBACK | Cancel this transaction's changes |

If the operation cannot finish, the application issues ROLLBACK instead of COMMIT. The deduction is undone and balances remain ₹1,000 and ₹500.

If the connection closes before commit, the database normally aborts the uncommitted transaction once it detects the disconnect.

### Does BEGIN handle every business failure?

No. An UPDATE against a missing receiver can affect zero rows without raising a SQL error.

Your application must verify that the intended rows were updated and roll back if they were not. It must also check sufficient funds and handle concurrent requests. The simple transfer above illustrates grouping, not every requirement of a production transfer.

### Other operations requiring grouping

| Operation | Related changes |
|---|---|
| Place order | Create order, create items, reduce inventory |
| Book seat | Reserve seat, create booking |
| Transfer money | Debit sender, credit receiver |
| Create invoice | Create invoice and invoice lines |

Transactions can include one statement or many statements, and one row, multiple rows, or multiple tables.

## Lesson 2: transaction boundaries

A **transaction boundary** determines which operations belong in one transaction. It starts at BEGIN and ends at COMMIT or ROLLBACK.

Ask: **Which changes must succeed or fail together for the business operation to be correct?**

### Example: buying two headphones

| Item | Value |
|---|---:|
| Stock before purchase | 5 |
| Requested quantity | 2 |
| Unit price | ₹1,000 |
| Order total | ₹2,000 |
| Stock after success | 3 |

We need an order, an order item, and a stock reduction.

An **order item** records one product, quantity, and purchase price within an order.

~~~sql
BEGIN;

INSERT INTO orders (id, customer_id, total)
VALUES (101, 7, 2000);

INSERT INTO order_items
    (order_id, product_id, quantity, unit_price)
VALUES
    (101, 10, 2, 1000);

UPDATE inventory
SET stock = stock - 2
WHERE product_id = 10
  AND stock >= 2;

-- Application must check: exactly one inventory row changed.
-- Zero rows means roll back instead of committing.

COMMIT;
~~~

Comments describe responsibilities; SQL comments do not implement checks.

If the stock update affects zero rows, the application rolls back. The newly inserted order and item are cancelled too.

### Incorrect boundaries

| Step | Result |
|---|---|
| Create order, commit | Permanently saved |
| Create item, commit | Permanently saved |
| Reduce stock | Fails |

Rolling back the third transaction cannot undo earlier commits.

### Who owns the boundary?

Usually the function coordinating the business operation:

~~~python
# Pseudocode
def place_order(customer_id, product_id, quantity):
    with database.transaction():
        order = create_order(customer_id)
        create_order_item(order, product_id, quantity)
        reduce_stock(product_id, quantity)
~~~

The assumed helper starts a transaction on entry, commits after successful exit, and rolls back if an exception escapes. An **exception** signals failure. Insufficient stock must signal failure.

The helper functions use the same transaction/connection and must not independently commit.

### Keep the scope focused

1. Validate input such as quantity being a positive integer.
2. Begin the transaction.
3. Perform protected reads, checks, and related writes.
4. Commit.
5. Prepare the response.

Checks against changing database state cannot simply be trusted because they were done earlier. Availability can change between an earlier check and your write.

Avoid waiting for user input or a slow external service inside a transaction. Transactions can retain locks, versions, and connections while waiting.

## Lesson 3: autocommit

A **statement** is one SQL command, such as INSERT or UPDATE.

**Autocommit** means each successful statement is automatically committed when no explicit transaction is active.

~~~sql
UPDATE accounts
SET balance = balance - 200
WHERE id = 1;
~~~

With autocommit enabled, this statement runs in its own transaction and commits automatically.

### Two statements are two independent transactions

~~~sql
UPDATE accounts SET balance = balance - 200 WHERE id = 1;
UPDATE accounts SET balance = balance + 200 WHERE id = 2;
~~~

Without an explicit transaction, the first can commit before the second fails. A later ROLLBACK cannot undo the first commit.

With an explicit BEGIN/COMMIT, the statements belong to one transaction rather than being individually committed.

| Mode | Unit of work | Commit |
|---|---|---|
| Autocommit, no explicit transaction | One statement | Automatic |
| Explicit transaction | Grouped statements | Requested by application |

### Are transactions disabled in autocommit?

No. A single statement still has transaction behavior for transactional tables.

~~~sql
UPDATE employees
SET salary = salary + 1000
WHERE department_id = 5;
~~~

This can update many rows atomically within that statement.

Autocommit is convenient for a genuinely independent write:

~~~sql
INSERT INTO feedback (customer_id, message)
VALUES (7, 'Good service');
~~~

Do not assume defaults. A **driver** is the software through which the application communicates with the database. Database, driver, and framework settings can choose different defaults and transaction-start behavior.

## Review questions

1. Why can two individually correct SQL statements create an incorrect transfer?
2. Can rollback undo a previous commit?
3. Why must a zero-row update sometimes count as a business failure?
4. Why should place_order own the transaction rather than each helper committing?
5. Does autocommit mean “no transactions”?

Next: [ACID](../phase-02-acid/README.md).
