# aggregate() and annotate()

Both ask the database to calculate values, but they answer different questions.

```text
aggregate()
→ one summary for the whole QuerySet

annotate()
→ one calculated value per object/group
```

## aggregate()

Common functions:

```python
from django.db.models import (
    Count,
    Sum,
    Avg,
    Min,
    Max,
)
```

Example:

```python
result = Employee.objects.aggregate(
    total_employees=Count("id"),
    total_salary=Sum("salary"),
    average_salary=Avg("salary"),
    minimum_salary=Min("salary"),
    maximum_salary=Max("salary"),
)
```

Possible result:

```python
{
    "total_employees": 4,
    "total_salary": 240000,
    "average_salary": 60000.0,
    "minimum_salary": 40000,
    "maximum_salary": 80000,
}
```

Conceptual SQL:

```sql
SELECT
    COUNT(id),
    SUM(salary),
    AVG(salary),
    MIN(salary),
    MAX(salary)
FROM employee;
```

The database performs the calculation.

### aggregate() is terminal

```python
result = Employee.objects.aggregate(
    total_salary=Sum("salary")
)
```

`result` is a dictionary, not a QuerySet.

So filter first:

```python
Employee.objects.filter(
    is_active=True
).aggregate(
    total_salary=Sum("salary")
)
```

### count() vs Count()

For simple total row count:

```python
Employee.objects.count()
```

returns an integer directly.

`Count()` is particularly useful inside `aggregate()` or `annotate()`.

### Related manager aggregate

```python
department.employees.aggregate(
    total_salary=Sum("salary")
)
```

calculates over employees related to that Department.

## annotate()

`annotate()` attaches a calculated value to every row/object in the QuerySet.

Example:

```python
departments = Department.objects.annotate(
    employee_count=Count("employees")
)
```

Then:

```python
for department in departments:
    print(
        department.name,
        department.employee_count,
    )
```

The annotation is temporary query data; it is not a real model field stored in the table.

Conceptual SQL:

```sql
SELECT
    department.id,
    department.name,
    COUNT(employee.id) AS employee_count
FROM department
LEFT OUTER JOIN employee
    ON employee.department_id = department.id
GROUP BY
    department.id,
    department.name;
```

## Why GROUP BY?

Joined rows may look like:

```text
Engineering | John
Engineering | Alice
HR          | David
HR          | Peter
HR          | Sam
```

Grouping by Department lets SQL calculate:

```text
Engineering → 2
HR          → 3
```

## annotate() remains chainable

```python
departments = (
    Department.objects
    .annotate(
        employee_count=Count("employees")
    )
    .filter(
        employee_count__gt=10
    )
    .order_by(
        "-employee_count"
    )
)
```

Filtering on an aggregate annotation often maps conceptually to SQL `HAVING`.

Think:

```text
WHERE
→ filter rows before aggregation

HAVING
→ filter groups after aggregation
```

## Sum/Avg/Min/Max per object

```python
Department.objects.annotate(
    total_salary=Sum("employees__salary"),
    average_salary=Avg("employees__salary"),
    lowest_salary=Min("employees__salary"),
    highest_salary=Max("employees__salary"),
)
```

Each Department gets those calculated attributes.

## Conditional aggregation

```python
from django.db.models import Count, Q

departments = Department.objects.annotate(
    employee_count=Count("employees"),
    active_employee_count=Count(
        "employees",
        filter=Q(
            employees__is_active=True
        ),
    ),
)
```

One query can calculate total and active counts.

## distinct=True

Joins across multi-valued relationships can duplicate counted rows.

Use when needed:

```python
Count(
    "employees",
    distinct=True,
)
```

Conceptually:

```sql
COUNT(DISTINCT employee.id)
```

Do not add it blindly; use it when the join shape would otherwise duplicate the entity being counted.

## Empty groups

`Count()` returns 0 for no related rows.

Functions such as `Sum()` can return `None` when no values exist.

Use `Coalesce` if you need a fallback:

```python
from django.db.models import Sum, Value
from django.db.models.functions import Coalesce

Department.objects.annotate(
    total_salary=Coalesce(
        Sum("employees__salary"),
        Value(0),
    )
)
```

## values() + annotate()

Very important reporting pattern:

```python
Employee.objects.values(
    "department_id"
).annotate(
    employee_count=Count("id")
)
```

Result:

```python
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
```

Conceptual SQL:

```sql
SELECT department_id, COUNT(id)
FROM employee
GROUP BY department_id;
```

A useful pattern:

```python
Model.objects.values(
    "group_field"
).annotate(
    result=AggregateFunction("field")
)
```

## Method order matters

With aggregation, these are not always equivalent:

```python
filter(...).annotate(...)
```

and:

```python
annotate(...).filter(...)
```

Likewise, `values()` before `annotate()` can establish grouping keys.

Always ask:

```text
Am I filtering source rows before the calculation?
Or am I filtering calculated groups/results afterward?
```

## annotate() can use expressions too

Example:

```python
from django.db.models import F

products = Product.objects.annotate(
    inventory_value=F("price") * F("quantity")
)
```

Then:

```python
product.inventory_value
```

is a database-calculated temporary attribute.

## Squad examples

Count memberships per Squad:

```python
squads = Squad.objects.annotate(
    member_count=Count("memberships")
)
```

Count active members:

```python
squads = Squad.objects.annotate(
    active_member_count=Count(
        "memberships",
        filter=Q(
            memberships__is_active=True
        ),
    )
)
```

Find Squads with at least 15 active memberships:

```python
squads = (
    Squad.objects
    .annotate(
        active_member_count=Count(
            "memberships",
            filter=Q(
                memberships__is_active=True
            ),
        )
    )
    .filter(
        active_member_count__gte=15
    )
)
```

## annotate() vs prefetch_related()

Bad if you only need a count:

```python
Department.objects.prefetch_related(
    "employees"
)
```

This loads Employee objects into Python.

Better:

```python
Department.objects.annotate(
    employee_count=Count("employees")
)
```

The database calculates the count and returns only the value with each Department row.

Mental model:

```text
prefetch_related()
→ need related objects

annotate()
→ need calculated information about related rows
```

## Strong interview answer

> `aggregate()` summarizes an entire QuerySet and returns a dictionary. `annotate()` adds a calculated database value to each object or group and returns a chainable QuerySet.
