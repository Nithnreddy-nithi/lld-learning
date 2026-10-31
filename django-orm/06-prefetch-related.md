# prefetch_related() — Deep Dive

`prefetch_related()` is mainly used for **multi-valued relationships**:

- reverse ForeignKey
- ManyToMany
- nested relation paths that contain multi-valued hops

It performs separate SQL queries and then associates related objects with parent objects in Python.

## N+1 without prefetch_related()

```python
departments = Department.objects.all()

for department in departments:
    for employee in department.employees.all():
        print(employee.name)
```

For 100 departments this can become:

```text
1 query → Departments
100 queries → Employees per Department
101 total
```

## With prefetch_related()

```python
departments = Department.objects.prefetch_related(
    "employees"
)
```

Django typically does:

```text
Query 1:
SELECT departments

Query 2:
SELECT employees
WHERE department_id IN (...)
```

Then it associates Employee objects to Department objects in Python.

## Mental model

```text
Department rows
  ↓
Employee rows for all selected Department IDs
  ↓
Python mapping by foreign key
  ↓
Department 1 → [Employee, Employee]
Department 2 → [Employee]
```

## Why not select_related()?

A reverse FK or M2M can return many rows.

A direct SQL join would repeat the parent row:

```text
IT | John
IT | Alice
IT | Peter
HR | David
```

For multi-valued relations, Django therefore prefers separate queries plus Python-side matching.

## ManyToMany example

```python
students = Student.objects.prefetch_related(
    "courses"
)
```

The DB may use the M2M junction table in the secondary query, and Django builds the Student → Courses associations in memory.

## Prefetch()

For custom filtering or optimization:

```python
from django.db.models import Prefetch

departments = Department.objects.prefetch_related(
    Prefetch(
        "employees",
        queryset=Employee.objects.filter(
            active=True
        ),
    )
)
```

This prefetches only active employees.

### to_attr

```python
departments = Department.objects.prefetch_related(
    Prefetch(
        "employees",
        queryset=Employee.objects.filter(
            active=True
        ),
        to_attr="active_employees",
    )
)
```

Then:

```python
for department in departments:
    for employee in department.active_employees:
        ...
```

`to_attr` keeps the custom subset clearly separate from the normal related manager.

## Important cache trap

If you prefetch:

```python
Department.objects.prefetch_related(
    "employees"
)
```

then:

```python
department.employees.all()
```

can use the prefetched cache.

But:

```python
department.employees.filter(active=True)
```

can execute a new query because that is a different QuerySet.

If you know the filtered subset in advance, use `Prefetch(..., queryset=...)`.

## Combine prefetch_related() and select_related()

Suppose:

```text
Department
  ↓ MANY
Employee
  ↓ ONE
Manager
```

Use:

```python
Department.objects.prefetch_related(
    Prefetch(
        "employees",
        queryset=Employee.objects.select_related(
            "manager"
        ),
    )
)
```

This can become:

```text
Query 1:
Departments

Query 2:
Employees JOIN Manager
```

## E-commerce pattern

```text
Order
 ├── User        ONE
 └── Items       MANY
       └── Product ONE
```

Good strategy:

```python
orders = (
    Order.objects
    .select_related("user")
    .prefetch_related(
        Prefetch(
            "items",
            queryset=OrderItem.objects.select_related(
                "product"
            ),
        )
    )
)
```

## Your Squad model

Relationship:

```text
Squad
 ├── Team           ONE
 └── Memberships    MANY
       └── Player   ONE
```

A strong roster query:

```python
squads = (
    Squad.objects
    .select_related("team")
    .prefetch_related(
        Prefetch(
            "memberships",
            queryset=SquadMembership.objects.select_related(
                "player"
            ),
        )
    )
)
```

Conceptually:

```text
Query 1:
Squad JOIN Team

Query 2:
SquadMembership JOIN Player
WHERE squad_id IN (...)
```

Then Django matches memberships to Squads in Python.

## Squad.players vs Squad.memberships

```python
Squad.objects.prefetch_related("players")
```

is useful if you only need Player objects.

But if you need relationship metadata:

```text
squad_role
jersey_number
joined_on
left_on
is_active
```

prefer prefetching memberships with `select_related("player")`.

## Process memory

`prefetch_related()` creates related Python model objects in the Django worker process.

Conceptually:

```text
Department object
  ↓ prefetch cache
Employee object
Employee object
Employee object
...
```

This reduces database round trips but can increase Python memory usage.

Important:

```text
fewer DB queries
≠
lower memory automatically
```

## prefetch_related() vs annotate()

If you need the related objects themselves:

```python
department.employees.all()
```

use `prefetch_related()`.

If you only need calculated information:

```text
employee count
average salary
total salary
min/max salary
```

use `annotate()` so the database calculates the result without loading all related Employee objects.

Example:

```python
Department.objects.annotate(
    employee_count=Count("employees")
)
```

Mental model:

```text
prefetch_related()
→ "Give me the related rows as Python objects."

annotate()
→ "Database, calculate something about those rows and give me the result."
```

## Do not prefetch blindly

If a relation contains huge numbers of rows, prefetching can create:

- large secondary queries;
- large `IN (...)` clauses;
- many Python objects;
- significant worker memory use.

Filter the parent QuerySet, paginate APIs, and prefetch only relations that will actually be used.

## Strong interview answer

> `prefetch_related()` is a Django QuerySet optimization used mainly for multi-valued relationships such as reverse ForeignKey and ManyToMany. Django executes separate queries for the parent and related objects and then associates those related objects in Python, which helps avoid N+1 queries.
