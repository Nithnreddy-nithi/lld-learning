# CRUD Operations in Django ORM

CRUD maps directly to core SQL operations:

```text
Create → INSERT
Read   → SELECT
Update → UPDATE
Delete → DELETE
```

## Create

### objects.create()

```python
user = User.objects.create(
    name="Nithin",
    email="nithin@example.com",
)
```

Conceptually:

```sql
INSERT INTO user (name, email)
VALUES ('Nithin', 'nithin@example.com');
```

It creates the model instance, saves it, and returns the saved instance.

### Model(...) + save()

```python
user = User(
    name="Nithin",
    email="nithin@example.com",
)
```

At this point the Python object exists, but no row has been persisted yet.

```python
user.save()
```

Now Django persists it.

For a new instance, `save()` normally produces an INSERT. For an existing loaded instance, it normally produces an UPDATE.

Custom model `save()` logic is used by normal instance saves and by `objects.create()`.

For authentication users, do not assign raw passwords with plain `objects.create(password=...)`. Use a manager method such as `create_user()` that calls `set_password()`.

## Read

### all()

```python
users = User.objects.all()
```

Returns a lazy QuerySet representing all rows.

### get()

```python
user = User.objects.get(id=1)
```

Expects exactly one object.

Possible outcomes:

- exactly one → returns the model instance;
- zero → raises `User.DoesNotExist`;
- more than one → raises `User.MultipleObjectsReturned`.

Use it for unique identifiers such as primary key or a unique email/slug.

### filter()

```python
users = User.objects.filter(is_active=True)
```

Always returns a QuerySet and can represent zero, one, or many rows.

An empty result is an empty QuerySet, not `DoesNotExist`.

### first() / last()

```python
user = User.objects.filter(is_active=True).first()
last_user = User.objects.order_by("id").last()
```

These return an instance or `None`.

### QuerySet laziness

```python
qs = User.objects.filter(is_active=True)
```

normally builds query state first. SQL is executed when the QuerySet is evaluated, e.g.:

```python
list(qs)

for user in qs:
    ...

qs.first()
qs.count()
```

## Update

### Instance update

```python
user = User.objects.get(id=1)
user.name = "Nithin"
user.save()
```

Flow:

```text
SELECT row
  ↓
Python model instance
  ↓
modify instance
  ↓
save()
  ↓
UPDATE
```

If you know exactly which fields changed:

```python
user.name = "Nithin"
user.save(update_fields=["name"])
```

Normal instance `save()` uses the model save lifecycle, including custom `save()` logic and normal save signals.

### QuerySet.update()

```python
count = User.objects.filter(
    is_active=False,
).update(
    is_active=True,
)
```

Conceptually:

```sql
UPDATE user
SET is_active = TRUE
WHERE is_active = FALSE;
```

This updates matching rows directly without instantiating every model object.

Important:

- does not call each model instance's custom `save()`;
- does not perform the normal per-instance `pre_save` / `post_save` path;
- useful for efficient bulk updates.

### F() update

```python
from django.db.models import F

Product.objects.filter(id=1).update(
    stock=F("stock") - 1
)
```

Conceptual SQL:

```sql
UPDATE product
SET stock = stock - 1
WHERE id = 1;
```

This lets the database update relative to the current value and avoids a separate read-modify-write round trip for simple counters.

### Existing Python instances can become stale

```python
user = User.objects.get(id=1)

User.objects.filter(id=1).update(
    name="New Name"
)
```

The existing `user` object may still contain the old name.

Reload it with:

```python
user.refresh_from_db()
```

## Delete

### Instance delete

```python
user = User.objects.get(id=1)
user.delete()
```

Deletes that object and applies Django's deletion handling.

### QuerySet delete

```python
User.objects.filter(
    is_active=False
).delete()
```

Deletes all matching rows and may also delete related rows depending on `on_delete` rules.

Be careful:

```python
User.objects.all().delete()
```

means delete all User rows.

A safer shell habit is:

```python
qs = User.objects.filter(is_active=False)
print(qs.count())
qs.delete()
```

`delete()` returns a tuple containing the total number of objects deleted and a per-model breakdown.

## Transactions

For multiple dependent operations:

```python
from django.db import transaction

with transaction.atomic():
    squad = Squad.objects.create(...)
    SquadMembership.objects.create(...)
    SquadMembership.objects.create(...)
```

Either all enclosed operations commit, or on failure the transaction is rolled back.

## Important validation note

Calling model `save()` does not automatically mean all model validators are run via `full_clean()`.

Forms/DRF serializers typically perform application-level validation; database constraints provide database-level enforcement.

## Quick comparison

| Operation | Instance level | QuerySet level |
|---|---|---|
| Create | `obj = Model(...); obj.save()` | `Model.objects.create(...)` |
| Read | `get()/first()` returns instance | `filter()/all()` return QuerySet |
| Update | modify + `obj.save()` | `filter(...).update(...)` |
| Delete | `obj.delete()` | `filter(...).delete()` |

Use instance operations when model lifecycle logic matters. Use QuerySet operations when set-based database work is the real goal.
