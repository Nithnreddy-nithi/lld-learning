# Loading Only Required Fields

Main tools:

```text
only()
defer()
values()
values_list()
```

Core difference:

```text
only() / defer()
→ return model instances

values() / values_list()
→ return selected raw field data
```

## only()

```python
employees = Employee.objects.only(
    "id",
    "name",
)
```

Django returns Employee model instances but initially loads only the selected fields.

Other fields are deferred.

If later:

```python
employee.salary
```

and salary was deferred, Django may execute another query for that instance.

### N+1 danger

```python
employees = Employee.objects.only(
    "id",
    "name",
)

for employee in employees:
    print(employee.salary)
```

can cause one initial query plus one deferred-field query per employee.

Use `only()` when large unused fields are genuinely expensive and you still need model instances.

Typical candidates:

- large TextField;
- large JSONField;
- BinaryField;
- large serialized payloads.

## defer()

`defer()` is the opposite style:

```python
employees = Employee.objects.defer(
    "bio",
    "profile_json",
)
```

Load most fields but skip the named expensive ones initially.

Rule:

```text
Need only a few fields?
→ only()

Need almost everything except a few expensive fields?
→ defer()
```

Deferred fields can still trigger later queries if accessed.

You can inspect them:

```python
employee.get_deferred_fields()
```

## values()

```python
employees = Employee.objects.values(
    "id",
    "name",
    "salary",
)
```

This returns a lazy QuerySet whose rows are dictionaries:

```python
{
    "id": 1,
    "name": "John",
    "salary": 50000,
}
```

There are no Employee model instances.

Use dictionary access:

```python
employee["name"]
```

not:

```python
employee.name
```

Because the result is not a model instance, you cannot call:

```python
employee.save()
```

### SQL shape

```python
Employee.objects.values(
    "id",
    "name",
)
```

conceptually:

```sql
SELECT id, name
FROM employee;
```

### Missing fields

If salary was not selected:

```python
employee["salary"]
```

raises a key error; Django does not lazily fetch it because there is no deferred model object.

### values() with filter()

```python
Employee.objects.filter(
    is_active=True
).values(
    "id",
    "name",
)
```

Think:

```text
filter()
→ which rows

values()
→ which columns and representation
```

### values() and relationships

```python
Employee.objects.values(
    "name",
    "department__name",
)
```

Django performs the necessary JOIN and returns keys like:

```python
{
    "name": "John",
    "department__name": "Engineering",
}
```

If you need only the FK value:

```python
Employee.objects.values(
    "department_id"
)
```

does not require loading the Department object.

### Alias related fields

```python
from django.db.models import F

Employee.objects.values(
    "id",
    "name",
    department_name=F("department__name"),
)
```

returns:

```python
{
    "id": 1,
    "name": "John",
    "department_name": "Engineering",
}
```

### values() + select_related()

If you already use:

```python
Employee.objects.values(
    "name",
    "department__name",
)
```

Django already knows it needs the related table to select the field. `select_related()` is generally unnecessary for the purpose of constructing related model instances because `values()` is not constructing them.

## values_list()

```python
Employee.objects.values_list(
    "id",
    "name",
)
```

returns tuple rows:

```python
(1, "John")
(2, "Alice")
```

It is still a lazy QuerySet until evaluated.

Tuple unpacking:

```python
for employee_id, name in employees:
    print(employee_id, name)
```

### flat=True

Selecting one field normally returns one-element tuples:

```python
Employee.objects.values_list("id")
```

yields:

```python
(1,)
(2,)
```

Use:

```python
Employee.objects.values_list(
    "id",
    flat=True,
)
```

to yield:

```python
1
2
```

`flat=True` works only when one field is selected.

### named=True

```python
row = Employee.objects.values_list(
    "id",
    "name",
    named=True,
).first()
```

Then:

```python
row.id
row.name
```

works because the row is a named tuple, but it is still not an Employee model instance.

### Common use: ID list

```python
employee_ids = Employee.objects.filter(
    is_active=True
).values_list(
    "id",
    flat=True,
)
```

Useful with:

```python
Order.objects.filter(
    employee_id__in=employee_ids
)
```

## only() vs values()

```text
only()
→ Employee model instance
→ missing fields are deferred
→ later access may query DB
→ model methods available

values()
→ dictionary
→ missing fields simply absent
→ no deferred fetch
→ no model methods
```

## values() vs values_list()

```text
values()
→ dictionaries
→ readable named keys

values_list()
→ tuples
→ compact rows
→ great for IDs/emails/simple report columns
```

## Process-memory angle

Normal model QuerySets construct model instances and model state.

`values()` / `values_list()` can avoid full model-instance construction when only raw data is needed.

For large reports/exports this may reduce Python-side overhead.

But do not over-optimize tiny datasets or tiny models without measurement.

## Good use cases

`only()`:
- model instance needed;
- only a few columns needed;
- omitted columns are expensive.

`defer()`:
- model instance needed;
- most columns needed;
- one or two expensive fields not needed.

`values()`:
- reports;
- analytics;
- exports;
- grouped/aggregate data;
- named raw rows.

`values_list()`:
- ID lists;
- email lists;
- compact exports;
- subquery/input sets.

## Summary table

| Method | Returns | Model methods | Missing fields |
|---|---|---|---|
| `only()` | model instances | Yes | deferred |
| `defer()` | model instances | Yes | deferred |
| `values()` | dictionaries | No | absent |
| `values_list()` | tuples | No | absent |
