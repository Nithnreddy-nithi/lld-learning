# only(), defer(), values(), values_list() — Complete Notes

These tools reduce or reshape what Django retrieves.

Core distinction:

~~~text
only() / defer()
→ model instances
→ unselected fields can be deferred

values() / values_list()
→ raw selected field data
→ no model instance
~~~

---

# 1. Why load fewer fields?

Suppose:

~~~python
class Employee(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    bio = models.TextField()
    profile_json = models.JSONField()
    salary = models.IntegerField()
    active = models.BooleanField(default=True)
~~~

If an endpoint only needs id and name, fetching large bio/JSON columns can waste:

~~~text
database I/O
network transfer
Python memory
model construction work
~~~

---

# 2. only()

~~~python
employees = Employee.objects.only(
    "id",
    "name",
)
~~~

Conceptually:

~~~sql
SELECT id, name
FROM employee;
~~~

Django still returns Employee model instances.

Loaded now:

~~~text
id
name
~~~

Deferred:

~~~text
email
bio
profile_json
salary
active
~~~

If later:

~~~python
employee.salary
~~~

Django may run another SELECT for the deferred field.

---

# 3. only() can accidentally create N+1

~~~python
employees = Employee.objects.only(
    "id",
    "name",
)

for employee in employees:
    print(employee.name)
    print(employee.salary)
~~~

salary was deferred.

Potential result:

~~~text
Query 1:
fetch id + name for all Employees

Then N additional queries:
fetch salary for each Employee
~~~

So only() is useful only when you really will not access the omitted fields.

---

# 4. When only() helps

Good case:

~~~python
class Article(models.Model):
    title = models.CharField(...)
    body = models.TextField()
    raw_html = models.TextField()
    metadata = models.JSONField(...)
~~~

A list page needs only:

~~~text
id
title
~~~

Then:

~~~python
Article.objects.only(
    "id",
    "title",
)
~~~

can avoid loading huge body/raw_html/metadata fields.

For a tiny model containing only small IDs, booleans, timestamps, and short strings, only() may add complexity without meaningful benefit.

---

# 5. defer()

defer() expresses the opposite intention:

~~~python
Employee.objects.defer(
    "bio",
    "profile_json",
)
~~~

Think:

~~~text
load everything
except bio and profile_json
~~~

Rule:

~~~text
Need very few fields?
→ only()

Need almost everything except a few expensive fields?
→ defer()
~~~

Deferred fields can also trigger later queries when accessed.

---

# 6. Inspect deferred fields

~~~python
employee = Employee.objects.only(
    "id",
    "name",
).first()

print(
    employee.get_deferred_fields()
)
~~~

You may see:

~~~python
{
    "email",
    "salary",
    "bio",
    "profile_json",
    "active",
}
~~~

---

# 7. values()

values() selects fields and returns dictionary rows instead of model instances.

~~~python
employees = Employee.objects.values(
    "id",
    "name",
    "salary",
)
~~~

Rows look like:

~~~python
{
    "id": 1,
    "name": "John",
    "salary": 50000,
}
~~~

Use:

~~~python
employee["name"]
~~~

not:

~~~python
employee.name
~~~

Because the row is a dictionary, this does not work:

~~~python
employee.save()
~~~

There is no Employee model instance.

---

# 8. values() SQL

~~~python
Employee.objects.values(
    "id",
    "name",
)
~~~

conceptually:

~~~sql
SELECT id, name
FROM employee;
~~~

If you call:

~~~python
Employee.objects.values()
~~~

Django returns dictionaries containing the model's concrete database fields.

---

# 9. values() is still lazy

~~~python
qs = Employee.objects.values(
    "id",
    "name",
)
~~~

qs is still a QuerySet.

SQL is typically executed when evaluated:

~~~python
list(qs)

for row in qs:
    ...

qs.first()
~~~

---

# 10. Missing field with values()

~~~python
employee = Employee.objects.values(
    "id",
    "name",
).get(id=1)
~~~

Result:

~~~python
{
    "id": 1,
    "name": "John",
}
~~~

Then:

~~~python
employee["salary"]
~~~

fails because salary is not present.

Unlike only(), Django does not perform a deferred fetch because there is no model instance.

Mental model:

~~~text
only()
→ missing field is deferred
→ later access may query DB

values()
→ missing field is absent
→ no lazy fetch exists
~~~

---

# 11. filter() vs values()

~~~python
Employee.objects.filter(
    is_active=True
).values(
    "id",
    "name",
)
~~~

Think:

~~~text
filter()
→ which rows

values()
→ which fields and how rows are represented
~~~

Conceptual SQL:

~~~sql
SELECT id, name
FROM employee
WHERE is_active = TRUE;
~~~

A field can participate in filtering without being returned in the selected output.

---

# 12. values() with ForeignKey IDs

Suppose:

~~~python
class Employee(models.Model):
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="employees",
    )
~~~

If you only need the FK value:

~~~python
Employee.objects.values(
    "department_id"
)
~~~

No Department object is needed.

The foreign-key ID already lives on Employee.

---

# 13. values() across relationships

~~~python
Employee.objects.values(
    "name",
    "department__name",
)
~~~

Django performs a JOIN because the Department name is needed.

Result:

~~~python
{
    "name": "John",
    "department__name": "Engineering",
}
~~~

Multi-level:

~~~python
Employee.objects.values(
    "name",
    "department__name",
    "department__location__city",
)
~~~

Path:

~~~text
Employee
→ Department
→ Location
~~~

---

# 14. Alias values() fields with expressions

~~~python
from django.db.models import F

employees = Employee.objects.values(
    "id",
    "name",
    department_name=F(
        "department__name"
    ),
)
~~~

Result:

~~~python
{
    "id": 1,
    "name": "John",
    "department_name": "Engineering",
}
~~~

This is useful for reports and exports.

---

# 15. values() and select_related()

This is generally enough:

~~~python
Employee.objects.values(
    "name",
    "department__name",
)
~~~

You normally do not need select_related("department") merely to get department__name.

Why?

values() already tells Django to select the related column, so Django generates the required JOIN directly.

select_related() is mainly valuable when Django is building related model instances for later object access.

---

# 16. values_list()

values_list() is similar to values(), but returns tuple rows.

~~~python
Employee.objects.values_list(
    "id",
    "name",
)
~~~

Rows:

~~~python
(1, "John")
(2, "Alice")
(3, "David")
~~~

Tuple unpacking is clean:

~~~python
for employee_id, name in employees:
    print(
        employee_id,
        name,
    )
~~~

---

# 17. values_list() is still a QuerySet

~~~python
employees = Employee.objects.values_list(
    "id",
    "name",
)
~~~

employees is a lazy QuerySet.

To create a real Python list:

~~~python
rows = list(
    Employee.objects.values_list(
        "id",
        "name",
    )
)
~~~

Result:

~~~python
[
    (1, "John"),
    (2, "Alice"),
]
~~~

---

# 18. flat=True

Selecting one field normally gives one-element tuples:

~~~python
Employee.objects.values_list(
    "id"
)
~~~

Rows:

~~~python
(1,)
(2,)
(3,)
~~~

Use:

~~~python
Employee.objects.values_list(
    "id",
    flat=True,
)
~~~

Rows become:

~~~python
1
2
3
~~~

flat=True works only when exactly one field is selected.

Invalid:

~~~python
Employee.objects.values_list(
    "id",
    "name",
    flat=True,
)
~~~

---

# 19. Common flat=True use case

~~~python
employee_ids = (
    Employee.objects
    .filter(is_active=True)
    .values_list(
        "id",
        flat=True,
    )
)
~~~

Then:

~~~python
Order.objects.filter(
    employee_id__in=employee_ids
)
~~~

Another common example:

~~~python
emails = Employee.objects.filter(
    is_active=True
).values_list(
    "email",
    flat=True,
)
~~~

---

# 20. named=True

~~~python
row = Employee.objects.values_list(
    "id",
    "name",
    named=True,
).first()
~~~

Then:

~~~python
row.id
row.name
~~~

works.

It is a named tuple, not an Employee model instance.

So:

~~~python
row.save()
~~~

is invalid.

flat=True and named=True are not used together.

---

# 21. values_list() with get()/first()

One email value:

~~~python
email = Employee.objects.values_list(
    "email",
    flat=True,
).get(id=1)
~~~

Result:

~~~python
"john@example.com"
~~~

First active email or None:

~~~python
email = (
    Employee.objects
    .filter(is_active=True)
    .order_by("id")
    .values_list(
        "email",
        flat=True,
    )
    .first()
)
~~~

Multiple fields with get():

~~~python
row = Employee.objects.values_list(
    "id",
    "name",
).get(id=1)
~~~

Result:

~~~python
(1, "John")
~~~

---

# 22. values_list() across relationships

~~~python
Employee.objects.values_list(
    "name",
    "department__name",
)
~~~

Rows:

~~~python
("John", "Engineering")
("Alice", "Engineering")
~~~

If you need only department IDs:

~~~python
Employee.objects.values_list(
    "department_id",
    flat=True,
)
~~~

No related model object is required.

---

# 23. values() + annotate()

Very common reporting pattern:

~~~python
from django.db.models import Count

Employee.objects.values(
    "department_id"
).annotate(
    employee_count=Count("id")
)
~~~

Conceptual SQL:

~~~sql
SELECT
    department_id,
    COUNT(id)
FROM employee
GROUP BY department_id;
~~~

Result:

~~~python
[
    {
        "department_id": 1,
        "employee_count": 2,
    },
    {
        "department_id": 2,
        "employee_count": 3,
    },
]
~~~

values() here establishes the grouping key.

---

# 24. only() with select_related()

Suppose you need Employee and Department objects, but both models have expensive unused fields:

~~~python
Employee.objects.select_related(
    "department"
).only(
    "id",
    "name",
    "department__id",
    "department__name",
)
~~~

This combines eager loading with column restriction.

Be careful: overly aggressive only()/defer() combinations with related-object loading can cause errors or unexpected deferred queries if Django later needs omitted fields.

Use this as measured optimization, not default style.

---

# 25. defer() with select_related()

If Department has a huge description:

~~~python
Employee.objects.select_related(
    "department"
).defer(
    "department__description"
)
~~~

Useful when you need Department.name but not the expensive text field.

---

# 26. Saving partially loaded model objects

Example:

~~~python
employee = Employee.objects.only(
    "name"
).get(id=1)

employee.name = "Nithin"
employee.save()
~~~

Django tracks deferred state, but partial-instance updates are more subtle than ordinary fully-loaded model saves.

If you only need a direct update:

~~~python
Employee.objects.filter(
    id=1
).update(
    name="Nithin"
)
~~~

can be clearer.

---

# 27. DRF warning

A ModelSerializer normally expects model instances.

So do not blindly replace:

~~~python
Employee.objects.all()
~~~

with:

~~~python
Employee.objects.values(...)
~~~

and expect every serializer path to work unchanged.

Use values()/values_list() when your data flow actually wants raw row data.

---

# 28. Performance and memory

Normal model QuerySet:

~~~text
database rows
→ Django model construction
→ Employee objects
→ model state
→ QuerySet result cache
~~~

values():

~~~text
database rows
→ dictionaries
~~~

values_list():

~~~text
database rows
→ tuples
~~~

For large reports/exports, avoiding full model instances can reduce Python-side overhead.

But the biggest gain often comes from avoiding large unused columns.

Do not over-optimize a tiny model with 30 rows.

---

# 29. Squad examples

Only a few Squad model fields:

~~~python
Squad.objects.only(
    "id",
    "name",
    "season",
)
~~~

Dictionary rows:

~~~python
Squad.objects.values(
    "id",
    "name",
    "season",
)
~~~

Tuple rows:

~~~python
Squad.objects.values_list(
    "id",
    "name",
    "season",
)
~~~

Squad name + Team name as raw report data:

~~~python
Squad.objects.values(
    "name",
    "team__name",
)
~~~

SquadMembership export:

~~~python
SquadMembership.objects.values(
    "player__full_name",
    "squad__name",
    "squad_role",
    "jersey_number",
)
~~~

Excellent for CSV/report style code because no full SquadMembership/Player/Squad model graph needs to be created.

---

# 30. Decision tree

~~~text
Do I need model instances?
  |
  YES
  |
  +-- Need almost all fields?
  |     → normal QuerySet
  |
  +-- Need only a few fields?
  |     → only()
  |
  +-- Need almost everything except a few expensive fields?
        → defer()


Do I only need raw selected data?
  |
  +-- Want named dictionary keys?
  |     → values()
  |
  +-- Want tuples or one flat column?
        → values_list()
~~~

---

# 31. Final comparison

| Method | Returns | Model methods? | Missing field behavior |
|---|---|---:|---|
| only() | model instances | Yes | deferred; later access may query |
| defer() | model instances | Yes | deferred; later access may query |
| values() | dictionaries | No | absent |
| values_list() | tuples | No | absent |

Strong interview answer:

> only() and defer() still return model instances and can lazily fetch deferred fields later. values() and values_list() return selected raw columns as dictionaries or tuples, so no model-instance behavior or deferred-field loading exists.
