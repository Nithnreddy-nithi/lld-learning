# CRUD Operations in Django ORM — Complete Notes

CRUD means:

~~~text
C = Create
R = Read
U = Update
D = Delete
~~~

At SQL level:

~~~text
Create → INSERT
Read   → SELECT
Update → UPDATE
Delete → DELETE
~~~

---

# 1. CREATE — objects.create()

~~~python
user = User.objects.create(
    name="Nithin",
    email="nithin@example.com",
)
~~~

Conceptually:

~~~sql
INSERT INTO user (
    name,
    email
)
VALUES (
    'Nithin',
    'nithin@example.com'
);
~~~

It creates a Python model instance, saves it, and returns the saved model instance.

---

# 2. CREATE — Model(...) + save()

~~~python
user = User(
    name="Nithin",
    email="nithin@example.com",
)
~~~

At this point:

~~~text
Python object exists
Database row does not yet exist
~~~

Then:

~~~python
user.save()
~~~

persists the object.

For a normal new object, Django performs an INSERT.

---

# 3. create() vs Model()+save()

Simple creation:

~~~python
User.objects.create(
    name="Nithin"
)
~~~

is roughly the convenient version of:

~~~python
user = User(
    name="Nithin"
)
user.save()
~~~

The two-step style lets you modify/prepare the object before saving.

Example:

~~~python
user = User(
    name="  Nithin  "
)

user.name = user.name.strip()

user.save()
~~~

---

# 4. Python object vs database row

After:

~~~python
user = User(
    name="Nithin"
)
~~~

conceptually:

~~~text
Django process heap
  ↓
User Python object
~~~

but the database has no new row yet.

After:

~~~python
user.save()
~~~

you now have:

~~~text
Python User object
+
database User row
~~~

They are different representations of the same logical entity.

---

# 5. save() on new vs existing object

New:

~~~python
user = User(
    name="Nithin"
)

user.save()
~~~

normally:

~~~text
INSERT
~~~

Existing:

~~~python
user = User.objects.get(
    id=1
)

user.name = "Nithin Kumar"

user.save()
~~~

normally:

~~~text
UPDATE
~~~

---

# 6. Custom save()

Suppose:

~~~python
class Squad(models.Model):
    name = models.CharField(
        max_length=120
    )

    def save(
        self,
        *args,
        **kwargs,
    ):
        self.name = self.name.strip()

        return super().save(
            *args,
            **kwargs,
        )
~~~

Then normal instance saving:

~~~python
Squad.objects.create(
    name="   India Squad   "
)
~~~

goes through model save logic and stores the stripped value.

This matters later when comparing save() with QuerySet.update().

---

# 7. Authentication users

Do not normally do:

~~~python
User.objects.create(
    email="a@gmail.com",
    password="123456",
)
~~~

because a raw password must not be stored directly.

Use:

~~~python
User.objects.create_user(
    email="a@gmail.com",
    password="123456",
)
~~~

so your custom manager can call:

~~~python
user.set_password(password)
~~~

and store a hash.

---

# 8. READ — all()

~~~python
users = User.objects.all()
~~~

Returns a QuerySet.

Conceptually:

~~~sql
SELECT *
FROM user;
~~~

QuerySets are lazy, so creating the QuerySet does not necessarily execute SQL immediately.

---

# 9. READ — get()

~~~python
user = User.objects.get(
    id=1
)
~~~

Use get() when you expect exactly one result.

Possible outcomes:

~~~text
1 match
→ model instance

0 matches
→ User.DoesNotExist

more than 1 match
→ User.MultipleObjectsReturned
~~~

Example handling:

~~~python
try:
    user = User.objects.get(
        id=1
    )
except User.DoesNotExist:
    print("User not found")
~~~

For potentially non-unique criteria:

~~~python
try:
    user = User.objects.get(
        name="John"
    )
except User.DoesNotExist:
    ...
except User.MultipleObjectsReturned:
    ...
~~~

Use get() naturally with unique fields:

~~~python
User.objects.get(pk=1)
User.objects.get(email="a@gmail.com")
Product.objects.get(slug="iphone-17")
~~~

when the schema guarantees uniqueness.

---

# 10. READ — filter()

~~~python
users = User.objects.filter(
    is_active=True
)
~~~

Always returns a QuerySet.

Even if there are:

~~~text
0 rows
1 row
100 rows
~~~

An empty filter result is an empty QuerySet, not DoesNotExist.

---

# 11. get() vs filter()

~~~text
get()
→ exactly one expected
→ returns object
→ raises if 0 or >1

filter()
→ 0/1/many allowed
→ returns QuerySet
→ empty result is okay
~~~

Example:

~~~python
user = User.objects.get(
    id=1
)
~~~

is a User model instance.

~~~python
users = User.objects.filter(
    id=1
)
~~~

is a QuerySet.

---

# 12. filter() chaining

~~~python
users = (
    User.objects
    .filter(
        is_active=True
    )
    .filter(
        is_staff=False
    )
)
~~~

Conceptually:

~~~sql
SELECT *
FROM user
WHERE is_active = TRUE
  AND is_staff = FALSE;
~~~

Because QuerySets are lazy, chaining filters does not normally mean one SQL query per filter call.

---

# 13. Multiple conditions in one filter()

~~~python
User.objects.filter(
    is_active=True,
    is_staff=False,
)
~~~

also expresses AND conditions.

---

# 14. first() and last()

~~~python
user = User.objects.filter(
    is_active=True
).first()
~~~

Returns:

~~~text
User instance
or
None
~~~

No DoesNotExist exception for an empty QuerySet.

Similarly:

~~~python
user = (
    User.objects
    .order_by("id")
    .last()
)
~~~

returns the last row under the ordering or None.

---

# 15. filter().first() vs get()

~~~python
User.objects.filter(
    email="a@gmail.com"
).first()
~~~

is convenient if not-found is normal.

But if email is required to be unique:

~~~python
User.objects.get(
    email="a@gmail.com"
)
~~~

can be safer because unexpected duplicates are exposed rather than silently ignored.

---

# 16. QuerySet evaluation

This is lazy:

~~~python
qs = User.objects.filter(
    is_active=True
)
~~~

Typical evaluations:

~~~python
list(qs)

for user in qs:
    ...

qs.first()
qs.count()
qs.exists()
~~~

These need DB results and therefore execute queries.

---

# 17. UPDATE — instance save()

~~~python
user = User.objects.get(
    id=1
)

user.name = "Nithin"

user.save()
~~~

Flow:

~~~text
SELECT
  ↓
User Python object
  ↓
change attribute
  ↓
save()
  ↓
UPDATE
~~~

---

# 18. save(update_fields=...)

If only one field changed:

~~~python
user.name = "Nithin"

user.save(
    update_fields=[
        "name"
    ]
)
~~~

This narrows the UPDATE columns.

---

# 19. Why instance save() matters

Normal instance save goes through model save behavior.

If:

~~~python
def save(self, *args, **kwargs):
    self.name = self.name.strip()
    return super().save(
        *args,
        **kwargs,
    )
~~~

then:

~~~python
user.name = "  Nithin  "
user.save()
~~~

runs that logic.

Normal save lifecycle signals such as pre_save/post_save also participate.

---

# 20. UPDATE — QuerySet.update()

~~~python
count = (
    User.objects
    .filter(
        is_active=False
    )
    .update(
        is_active=True
    )
)
~~~

Conceptually:

~~~sql
UPDATE user
SET is_active = TRUE
WHERE is_active = FALSE;
~~~

This is a set-based direct SQL update.

Django does not instantiate every matching User object first.

---

# 21. Why update() is faster for bulk changes

Bad bulk pattern:

~~~python
users = User.objects.filter(
    is_active=False
)

for user in users:
    user.is_active = True
    user.save()
~~~

Potentially:

~~~text
1 SELECT
+
N UPDATE statements
~~~

Better:

~~~python
User.objects.filter(
    is_active=False
).update(
    is_active=True
)
~~~

can perform one SQL UPDATE statement.

---

# 22. update() bypasses model save()

Suppose model save strips name.

This:

~~~python
user = User.objects.get(id=1)
user.name = "  Nithin  "
user.save()
~~~

runs custom save().

But:

~~~python
User.objects.filter(
    id=1
).update(
    name="  Nithin  "
)
~~~

does not call the model's custom save().

It writes directly at QuerySet/SQL level.

It also does not perform normal per-instance pre_save/post_save processing.

That speed comes with different lifecycle semantics.

---

# 23. update() return value

~~~python
count = User.objects.filter(
    is_active=False
).update(
    is_active=True
)
~~~

count is the number of rows matched/affected according to backend semantics.

Useful for checking whether anything changed.

---

# 24. F() update

~~~python
from django.db.models import F

Product.objects.filter(
    id=1
).update(
    stock=F("stock") - 1
)
~~~

Conceptual SQL:

~~~sql
UPDATE product
SET stock = stock - 1
WHERE id = 1;
~~~

The database performs arithmetic directly using its current row value.

---

# 25. Why F() helps concurrency

Without F():

~~~python
product = Product.objects.get(
    id=1
)

product.stock = (
    product.stock - 1
)

product.save()
~~~

There is a read-then-write window where another transaction can modify stock.

With:

~~~python
Product.objects.filter(
    id=1
).update(
    stock=F("stock") - 1
)
~~~

the arithmetic occurs in the database in one UPDATE statement.

For more complex read-check-write workflows, select_for_update() may still be needed.

---

# 26. DELETE — instance delete()

~~~python
user = User.objects.get(
    id=1
)

user.delete()
~~~

Deletes that specific instance and invokes Django's deletion machinery.

---

# 27. DELETE — QuerySet.delete()

~~~python
User.objects.filter(
    is_active=False
).delete()
~~~

Deletes all matching objects.

Be extremely careful:

~~~python
User.objects.all().delete()
~~~

means delete every User row.

Django does not prompt:

~~~text
"Are you sure?"
~~~

---

# 28. Safer deletion habit

~~~python
qs = User.objects.filter(
    is_active=False
)

print(
    qs.count()
)

qs.delete()
~~~

Inspect the target set before destructive work in shell/management scripts.

---

# 29. delete() return value

~~~python
result = User.objects.filter(
    is_active=False
).delete()
~~~

Django returns a tuple containing:

~~~text
total deleted object count
+
per-model deletion counts
~~~

Cascaded related deletions may contribute to the total.

---

# 30. on_delete affects deletion

CASCADE:

~~~python
squad = models.ForeignKey(
    Squad,
    on_delete=models.CASCADE,
)
~~~

Deleting Squad can delete related SquadMembership rows.

PROTECT:

~~~python
player = models.ForeignKey(
    Player,
    on_delete=models.PROTECT,
)
~~~

Deleting a referenced Player can be blocked.

SET_NULL:

~~~python
department = models.ForeignKey(
    Department,
    null=True,
    on_delete=models.SET_NULL,
)
~~~

Deleting Department can set employee.department_id to NULL.

---

# 31. QuerySet.delete() is not just a loop over obj.delete()

Do not assume:

~~~python
for obj in qs:
    obj.delete()
~~~

is exactly what QuerySet.delete() does internally.

Django can optimize deletion and does not simply call every custom model delete() override in the same way as manually invoking instance delete() one by one.

If critical business behavior lives in custom delete() methods, understand bulk-delete semantics carefully.

---

# 32. Existing Python object can become stale after update()

~~~python
user = User.objects.get(
    id=1
)

User.objects.filter(
    id=1
).update(
    name="New Name"
)

print(
    user.name
)
~~~

user may still hold the old Python-side value because QuerySet.update() changed the DB directly.

Reload:

~~~python
user.refresh_from_db()
~~~

Now the Python object reflects current DB values.

---

# 33. Validation nuance

Suppose:

~~~python
jersey_number = (
    models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(0),
            MaxValueValidator(999),
        ]
    )
)
~~~

Calling:

~~~python
membership.save()
~~~

does not automatically mean Django ran full model validation via full_clean().

Validation commonly happens in:

~~~text
Django Forms
DRF serializers
explicit full_clean()
~~~

Database constraints provide another enforcement layer.

---

# 34. Transactions

Multiple operations that must succeed/fail together:

~~~python
from django.db import transaction

with transaction.atomic():
    squad = Squad.objects.create(
        ...
    )

    SquadMembership.objects.create(
        ...
    )

    SquadMembership.objects.create(
        ...
    )
~~~

If an exception causes rollback:

~~~text
none of the enclosed changes commit
~~~

Transactions are crucial for multi-row consistency.

---

# 35. Squad CRUD examples

Create:

~~~python
squad = Squad.objects.create(
    team=team,
    name="India ODI Squad",
    season="2026",
)
~~~

Read:

~~~python
Squad.objects.all()

Squad.objects.get(
    id=1
)

Squad.objects.filter(
    is_active=True
)

Squad.objects.filter(
    team=team
).first()
~~~

Instance update:

~~~python
squad = Squad.objects.get(
    id=1
)

squad.name = "India ODI Team"

squad.save()
~~~

Bulk update:

~~~python
Squad.objects.filter(
    season="2025"
).update(
    is_active=False
)
~~~

Important: custom Squad.save() does not run in QuerySet.update().

Delete one:

~~~python
squad.delete()
~~~

Delete many:

~~~python
Squad.objects.filter(
    is_active=False
).delete()
~~~

---

# 36. SquadMembership CRUD examples

Create:

~~~python
membership = (
    SquadMembership.objects.create(
        squad=squad,
        player=player,
        squad_role=(
            SquadRole.CAPTAIN
        ),
        jersey_number=45,
    )
)
~~~

Read:

~~~python
SquadMembership.objects.filter(
    squad=squad
)
~~~

Instance update:

~~~python
membership.squad_role = (
    SquadRole.PLAYER
)

membership.save(
    update_fields=[
        "squad_role"
    ]
)
~~~

Bulk update:

~~~python
SquadMembership.objects.filter(
    squad=squad
).update(
    is_active=False
)
~~~

Delete one:

~~~python
membership.delete()
~~~

Delete many:

~~~python
SquadMembership.objects.filter(
    squad=squad
).delete()
~~~

---

# 37. Process-level CRUD mental model

Read:

~~~text
Python/Django
  ↓
SELECT
  ↓
Database
  ↓
row returned
  ↓
Django builds model instance
  ↓
Python heap
~~~

Modify only Python:

~~~python
user.name = "Nithin"
~~~

At this point the DB is unchanged.

Persist:

~~~python
user.save()
~~~

Now:

~~~text
Python object
  ↓
UPDATE
  ↓
Database row changes
~~~

---

# 38. Common mistake: forgetting save()

~~~python
user = User.objects.get(
    id=1
)

user.name = "Nithin"
~~~

If you stop here:

~~~text
Python object changed
Database row unchanged
~~~

The change is lost when the object/request disappears.

---

# 39. Quick comparison

| Operation | Returns/behavior |
|---|---|
| all() | QuerySet |
| filter() | QuerySet |
| get() | exactly one model instance |
| first() | model instance or None |
| last() | model instance or None |
| obj.save() | instance-level INSERT/UPDATE |
| QuerySet.update() | direct set-based UPDATE |
| obj.delete() | delete one instance |
| QuerySet.delete() | delete matching set |

---

# 40. Production decision rules

~~~text
Need exactly one row?
→ get()

Need 0/1/many rows?
→ filter()

Need one without exception?
→ filter(...).first()

Need model lifecycle logic?
→ modify instance + save()

Need efficient bulk update?
→ filter(...).update()

Need atomic relative counter update?
→ F()

Need several DB operations to succeed together?
→ transaction.atomic()
~~~

Strong interview answer:

> Django CRUD maps ORM operations to SQL INSERT, SELECT, UPDATE, and DELETE. Instance save/delete operations work with model objects and their lifecycle, while QuerySet update/delete operations perform set-based database work and have different lifecycle semantics. QuerySets are lazy for reads, while create/update/delete operations execute database changes directly.
