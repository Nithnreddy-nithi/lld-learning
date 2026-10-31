# select_for_update() and Concurrency

`select_for_update()` is used to lock selected database rows while a transaction is running.

Core idea:

```text
BEGIN
  ↓
SELECT ... FOR UPDATE
  ↓
lock matching row(s)
  ↓
read/check/update safely
  ↓
COMMIT or ROLLBACK
  ↓
lock released
```

It is mainly used to prevent race conditions in concurrent write workflows.

## Inventory race condition

Suppose:

```text
Product stock = 1
```

Two requests run at nearly the same time:

```text
A reads stock = 1
B reads stock = 1

A decides purchase is allowed
B decides purchase is allowed
```

Without coordination, both can act on the same stale state.

## Locking solution

```python
from django.db import transaction

with transaction.atomic():
    product = (
        Product.objects
        .select_for_update()
        .get(id=1)
    )

    if product.stock <= 0:
        raise ValueError("Out of stock")

    product.stock -= 1
    product.save(
        update_fields=["stock"]
    )
```

Conceptual SQL:

```sql
BEGIN;

SELECT *
FROM product
WHERE id = 1
FOR UPDATE;

UPDATE product
SET stock = 0
WHERE id = 1;

COMMIT;
```

If Transaction A owns the row lock, Transaction B trying to acquire a conflicting lock on the same row normally waits until A commits/rolls back.

Then B sees the new state.

## transaction.atomic() vs select_for_update()

```text
transaction.atomic()
→ defines the transaction boundary

select_for_update()
→ explicitly locks selected rows
```

A plain SELECT inside `atomic()` does not automatically mean the row is locked for update.

## Row-level lock

```python
Product.objects.select_for_update().get(id=10)
```

targets the matching row(s), not the entire database.

Other rows can usually still be modified independently.

## Lock lives in the database

The Python Product object lives in the Django worker process memory.

The concurrency lock is enforced by the database.

This is why database row locking works across:

```text
Gunicorn Worker 1
Gunicorn Worker 2
different app servers
multiple processes
```

All of them coordinate through the shared database.

A Python `threading.Lock()` would not provide the same cross-process/cross-server protection.

## Keep locked transactions short

Bad pattern:

```python
with transaction.atomic():
    account = (
        Account.objects
        .select_for_update()
        .get(id=1)
    )

    call_slow_external_api()
    send_email()
    do_large_computation()

    account.balance -= 100
    account.save()
```

The row remains locked during all of that work.

Long transactions increase contention.

Keep critical locked DB sections as short as reasonably possible.

## Lock contention

If many requests want the same row:

```text
Request 1 → gets lock
Request 2 → waits
Request 3 → waits
Request 4 → waits
```

Correctness improves, but throughput can drop.

## Deadlocks

Example:

```text
Transaction A:
lock Account 1
then waits for Account 2

Transaction B:
lock Account 2
then waits for Account 1
```

This creates a deadlock.

A common mitigation is consistent lock ordering:

```python
account_ids = sorted(
    [from_account_id, to_account_id]
)

accounts = (
    Account.objects
    .select_for_update()
    .filter(id__in=account_ids)
    .order_by("id")
)
```

All transactions lock rows in the same order.

## nowait=True

```python
Product.objects.select_for_update(
    nowait=True
).get(id=1)
```

If the row is already locked by a conflicting transaction, fail immediately instead of waiting.

## skip_locked=True

```python
Job.objects     .select_for_update(
        skip_locked=True
    )     .filter(status="pending")     .order_by("id")     .first()
```

If Job 1 is already locked, another worker can skip it and claim Job 2.

Useful for DB-backed worker queues.

Mental model:

```text
default
→ locked row: wait

nowait=True
→ locked row: error/fail immediately

skip_locked=True
→ locked row: skip it
```

Support depends on database backend.

## of=("self",)

When a query joins multiple tables, advanced locking control may be useful:

```python
Order.objects     .select_related("customer")     .select_for_update(
        of=("self",)
    )
```

This expresses that the primary model's rows are the intended lock target.

Backend support varies.

## no_key=True

On PostgreSQL, Django exposes a weaker row-locking mode with:

```python
select_for_update(
    no_key=True
)
```

This is advanced and useful only when you specifically need weaker lock semantics.

## QuerySet laziness

```python
qs = Product.objects.select_for_update()
```

does not acquire a lock merely by constructing the QuerySet.

The lock is acquired when the query is evaluated within the transaction:

```python
product = qs.get(id=1)
```

or through iteration/list evaluation.

## Lock release

The lock remains until the transaction ends.

```text
SELECT FOR UPDATE
  ↓
lock held
  ↓
save()
  ↓
lock still held
  ↓
COMMIT / ROLLBACK
  ↓
lock released
```

## Plain reads and MVCC

On PostgreSQL, a plain SELECT can typically still read a row while another transaction holds a FOR UPDATE lock due to MVCC.

Conflicting writes/locks are what normally wait.

Do not think of `select_for_update()` as making the row invisible.

## F() vs select_for_update()

For a simple atomic decrement:

```python
Product.objects.filter(
    id=product_id,
    stock__gte=quantity,
).update(
    stock=F("stock") - quantity
)
```

can be enough and may scale better.

Use `select_for_update()` when the workflow requires a multi-step read/check/decision/write sequence that must be serialized.

Think:

```text
F()
→ atomic DB-side expression

select_for_update()
→ pessimistic row locking around a multi-step decision
```

## Good use cases

- inventory reservation;
- seat booking;
- wallet/bank balance changes;
- order state transitions;
- coupon usage limits;
- limited-capacity resources;
- DB-backed job claiming.

## Strong interview answer

> `select_for_update()` performs a database row-level lock on selected rows within a transaction. It is commonly used with `transaction.atomic()` to prevent race conditions when concurrent transactions read and update the same data. Conflicting transactions usually wait until the lock-owning transaction commits or rolls back.
