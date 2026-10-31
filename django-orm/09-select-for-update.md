# select_for_update() — Complete Concurrency Deep Dive

`select_for_update()` performs a database row lock for rows selected inside a transaction.

Core idea:

~~~text
BEGIN
  ↓
SELECT ... FOR UPDATE
  ↓
lock matching row(s)
  ↓
read / validate / modify safely
  ↓
COMMIT or ROLLBACK
  ↓
lock released
~~~

It is a **pessimistic locking** technique used to protect multi-step database workflows from race conditions.

---

# 1. Inventory race condition

Suppose:

~~~text
Product #1
stock = 1
~~~

Two users buy at the same time.

Without locking:

~~~text
Transaction A reads stock = 1
Transaction B reads stock = 1

A checks stock > 0 → True
B checks stock > 0 → True

A creates purchase
B creates purchase
~~~

Both decisions were made from the same old state.

That is a race condition.

---

# 2. Lock the row

~~~python
from django.db import transaction

with transaction.atomic():
    product = (
        Product.objects
        .select_for_update()
        .get(id=1)
    )

    if product.stock <= 0:
        raise ValueError(
            "Out of stock"
        )

    product.stock -= 1
    product.save(
        update_fields=["stock"]
    )
~~~

Conceptual SQL:

~~~sql
BEGIN;

SELECT *
FROM product
WHERE id = 1
FOR UPDATE;

UPDATE product
SET stock = 0
WHERE id = 1;

COMMIT;
~~~

---

# 3. Timeline with two transactions

~~~text
Initial stock = 1
~~~

Transaction A:

~~~text
SELECT FOR UPDATE
→ gets lock
→ reads stock = 1
~~~

Transaction B:

~~~text
SELECT FOR UPDATE
→ same row already locked
→ waits
~~~

Transaction A:

~~~text
stock = 0
UPDATE
COMMIT
→ lock released
~~~

Transaction B:

~~~text
lock acquired
→ sees stock = 0
→ rejects purchase
~~~

Correct behavior.

---

# 4. transaction.atomic() and select_for_update() solve different things

~~~text
transaction.atomic()
→ transaction boundary
→ commit/rollback unit

select_for_update()
→ row-level locking
→ protects selected rows from conflicting writes/locks
~~~

A plain SELECT inside atomic() does not automatically create the same row lock.

---

# 5. Banking example

Account:

~~~text
balance = 1000
~~~

Two withdrawals:

~~~text
A wants 800
B wants 800
~~~

Without locking:

~~~text
A reads 1000
B reads 1000

A checks 1000 >= 800 → yes
B checks 1000 >= 800 → yes
~~~

With locking:

~~~python
def withdraw(account_id, amount):
    with transaction.atomic():
        account = (
            Account.objects
            .select_for_update()
            .get(id=account_id)
        )

        if account.balance < amount:
            raise ValueError(
                "Insufficient funds"
            )

        account.balance -= amount
        account.save(
            update_fields=["balance"]
        )
~~~

The second transaction sees the balance after the first transaction completes.

---

# 6. Seat booking example

~~~python
with transaction.atomic():
    seat = (
        Seat.objects
        .select_for_update()
        .get(id=10)
    )

    if seat.is_booked:
        raise ValueError(
            "Seat already booked"
        )

    seat.is_booked = True
    seat.save(
        update_fields=["is_booked"]
    )
~~~

This prevents two concurrent requests from both seeing the seat as available.

---

# 7. Row-level lock vs table lock

~~~python
Product.objects.select_for_update().get(
    id=10
)
~~~

targets the matching row(s).

Other rows such as Product 11/12 can normally still be modified independently.

This is much more targeted than locking the whole table.

---

# 8. The lock is database-side, not Python-side

Suppose:

~~~text
Server A
  ├── Worker 1
  └── Worker 2

Server B
  ├── Worker 1
  └── Worker 2

          ↓
      PostgreSQL
~~~

A Python threading.Lock() exists only inside a process/threading context.

select_for_update() is enforced by PostgreSQL/MySQL/etc., so all app workers that use the same DB coordinate through the same row lock.

The Python model object is in process memory.

The lock state is in the database transaction system.

---

# 9. Lock lifetime

~~~python
with transaction.atomic():
    product = (
        Product.objects
        .select_for_update()
        .get(id=1)
    )

    # lock held

    product.stock -= 1
    product.save()

    # lock still held

# COMMIT
# lock released
~~~

The lock does not disappear after save().

It remains until the transaction ends.

---

# 10. Rollback releases the lock

~~~python
try:
    with transaction.atomic():
        product = (
            Product.objects
            .select_for_update()
            .get(id=1)
        )

        product.stock -= 1
        product.save()

        raise RuntimeError(
            "Something failed"
        )
except RuntimeError:
    pass
~~~

Django/database rolls back the transaction.

Effects:

~~~text
UPDATE rolled back
+
row lock released
~~~

---

# 11. Keep transactions short

Bad:

~~~python
with transaction.atomic():
    account = (
        Account.objects
        .select_for_update()
        .get(id=1)
    )

    call_payment_provider()
    send_email()
    do_slow_processing()

    account.balance -= 100
    account.save()
~~~

The row stays locked while external I/O is happening.

This increases:

~~~text
waiting requests
lock contention
latency
deadlock exposure
~~~

Better:

- do non-critical external work outside the locked section where safe;
- keep the DB transaction focused on the smallest consistency-critical unit.

---

# 12. Lock contention

If 100 requests try to update the same account:

~~~text
Request 1 → lock acquired
Request 2 → wait
Request 3 → wait
Request 4 → wait
...
~~~

Correctness improves, but throughput for that hot row decreases.

This is called lock contention.

---

# 13. Deadlock

Transaction A:

~~~text
locks Account 1
then wants Account 2
~~~

Transaction B:

~~~text
locks Account 2
then wants Account 1
~~~

Now:

~~~text
A waits for B
B waits for A
~~~

Deadlock.

The database detects the deadlock and aborts one transaction.

---

# 14. Consistent lock ordering

For transfers between two accounts:

~~~python
account_ids = sorted(
    [
        from_account_id,
        to_account_id,
    ]
)

accounts = (
    Account.objects
    .select_for_update()
    .filter(
        id__in=account_ids
    )
    .order_by("id")
)
~~~

Every transaction locks lower ID first, then higher ID.

Consistent ordering greatly reduces deadlock risk.

---

# 15. nowait=True

Default behavior on a conflicting lock is often to wait.

Sometimes you prefer immediate failure:

~~~python
with transaction.atomic():
    product = (
        Product.objects
        .select_for_update(
            nowait=True
        )
        .get(id=1)
    )
~~~

Mental model:

~~~text
lock available
→ acquire

already locked
→ fail immediately
~~~

Useful for fast-fail workflows or retry logic.

Backend support varies.

---

# 16. skip_locked=True

~~~python
with transaction.atomic():
    job = (
        Job.objects
        .select_for_update(
            skip_locked=True
        )
        .filter(
            status="pending"
        )
        .order_by("id")
        .first()
    )
~~~

If Job 1 is locked by Worker A, Worker B can skip it and take Job 2.

This is useful for database-backed job queues.

---

# 17. Worker queue example

~~~python
from django.db import transaction

def claim_next_job():
    with transaction.atomic():
        job = (
            Job.objects
            .select_for_update(
                skip_locked=True
            )
            .filter(
                status="pending"
            )
            .order_by("id")
            .first()
        )

        if job is None:
            return None

        job.status = "processing"
        job.save(
            update_fields=["status"]
        )

        return job
~~~

Three concurrent workers can claim different jobs:

~~~text
Worker 1 → Job 1
Worker 2 → Job 2
Worker 3 → Job 3
~~~

instead of all racing for Job 1.

---

# 18. Default vs nowait vs skip_locked

~~~text
default:
locked row
→ wait

nowait=True:
locked row
→ error immediately

skip_locked=True:
locked row
→ skip and continue
~~~

These options depend on database capabilities.

---

# 19. of=("self",)

If your query includes joins:

~~~python
orders = (
    Order.objects
    .select_related("customer")
    .select_for_update(
        of=("self",)
    )
)
~~~

"self" refers to the primary model of the QuerySet.

The goal is to restrict which joined table rows are selected for locking where supported.

Advanced feature; backend support varies.

---

# 20. no_key=True

PostgreSQL supports a weaker row-lock mode exposed by Django:

~~~python
select_for_update(
    no_key=True
)
~~~

This can allow some foreign-key-related operations that a stronger lock would block.

Treat this as an advanced PostgreSQL-specific optimization.

---

# 21. QuerySet laziness still applies

~~~python
qs = Product.objects.select_for_update()
~~~

This does not acquire a lock yet.

The lock is acquired when the SQL query executes, e.g.:

~~~python
with transaction.atomic():
    product = qs.get(id=1)
~~~

or:

~~~python
with transaction.atomic():
    products = list(qs)
~~~

---

# 22. Plain readers and MVCC

On PostgreSQL, a plain SELECT can usually still read a row while another transaction holds FOR UPDATE.

Conflicting operations such as:

~~~text
UPDATE
DELETE
SELECT ... FOR UPDATE
~~~

are the operations that typically wait or otherwise conflict.

So do not think:

~~~text
select_for_update()
→ row becomes invisible
~~~

It is a write/concurrency lock, not a visibility cloak.

---

# 23. F() expression vs select_for_update()

For a simple atomic decrement:

~~~python
from django.db.models import F

updated = (
    Product.objects
    .filter(
        id=product_id,
        stock__gte=quantity,
    )
    .update(
        stock=F("stock") - quantity
    )
)
~~~

If:

~~~python
updated == 1
~~~

the update succeeded.

If:

~~~python
updated == 0
~~~

the condition was not satisfied.

This can solve some inventory cases without explicit row locking.

---

# 24. When F() may be enough

Simple rule:

~~~text
single atomic arithmetic/update condition
→ F()/conditional UPDATE may be enough
~~~

Example:

~~~python
Product.objects.filter(
    id=product_id,
    stock__gte=1,
).update(
    stock=F("stock") - 1
)
~~~

The DB evaluates and modifies atomically.

---

# 25. When select_for_update() is more appropriate

Suppose business flow is:

~~~text
read account
check balance
check account status
check withdrawal limit
create ledger entry
update balance
update withdrawal record
~~~

This is a multi-step decision based on current state.

A locked transaction can be more appropriate:

~~~text
read
→ validate several rules
→ write several related rows
~~~

---

# 26. Squad captain example

Suppose you want one active captain per Squad and two admins may change captain concurrently.

One possible serialization strategy:

~~~python
with transaction.atomic():
    squad = (
        Squad.objects
        .select_for_update()
        .get(id=squad_id)
    )

    SquadMembership.objects.filter(
        squad=squad,
        squad_role=SquadRole.CAPTAIN,
        is_active=True,
    ).update(
        squad_role=SquadRole.PLAYER
    )

    membership = (
        SquadMembership.objects
        .get(
            squad=squad,
            player=player,
        )
    )

    membership.squad_role = (
        SquadRole.CAPTAIN
    )
    membership.save(
        update_fields=[
            "squad_role"
        ]
    )
~~~

Locking the Squad row can serialize captain-change workflows for that Squad.

Where possible, database constraints should also enforce invariants.

---

# 27. Testing concurrency conceptually

You cannot prove concurrency safety merely by running one request.

The race exists only when two transactions overlap.

A proper test needs separate DB transactions/connections and controlled timing.

Conceptually:

~~~text
Transaction A
→ lock row
→ pause

Transaction B
→ attempt same lock
→ should block/fail/skip depending on option
~~~

---

# 28. Good use cases

~~~text
inventory reservation
seat booking
wallet balance
bank transfer
coupon usage limit
order state transition
limited-capacity resources
database job claiming
~~~

Pattern:

~~~text
Read current state
  ↓
Make decision based on state
  ↓
Write new state
~~~

under concurrent requests.

---

# 29. Final mental model

~~~text
Django Worker A
  ↓
BEGIN
  ↓
SELECT row FOR UPDATE
  ↓
DB marks conflicting lock
  ↓
Worker B tries same row
  ↓
WAIT / ERROR / SKIP
  ↓
Worker A updates
  ↓
COMMIT
  ↓
lock released
  ↓
Worker B can continue
~~~

Strong interview answer:

> select_for_update() is Django's ORM interface to database row-level locking. It is normally used inside transaction.atomic() when a multi-step read-check-update workflow must be protected from concurrent transactions. The lock is held until commit or rollback.
