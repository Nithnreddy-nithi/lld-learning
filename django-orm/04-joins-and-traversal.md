# JOINs and Relationship Traversal

Django model relationships become SQL joins when a query needs columns from related tables.

```text
Model relationships
  ↓
ForeignKey / OneToOne / ManyToMany
  ↓
ORM traversal with __
  ↓
SQL JOIN
```

## Forward traversal

Models:

```python
class Department(models.Model):
    name = models.CharField(max_length=100)

class Employee(models.Model):
    name = models.CharField(max_length=100)
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name="employees",
    )
```

Query:

```python
Employee.objects.filter(
    department__name="Engineering"
)
```

Conceptual SQL:

```sql
SELECT employee.*
FROM employee
INNER JOIN department
    ON employee.department_id = department.id
WHERE department.name = 'Engineering';
```

`department__name` means:

```text
Employee
  ↓ department relation
Department
  ↓ name field
```

The foreign key existing does not mean every Employee query always joins Department. Django adds joins when the query actually needs them.

## Field lookups after traversal

```python
Employee.objects.filter(
    department__name__icontains="engine"
)
```

Break it into:

```text
department = relationship
name       = related field
icontains  = lookup
```

## Reverse traversal

Because:

```python
department = models.ForeignKey(
    Department,
    related_name="employees",
    ...
)
```

you can query backward:

```python
Department.objects.filter(
    employees__name="John"
)
```

Conceptually:

```sql
SELECT department.*
FROM department
INNER JOIN employee
    ON employee.department_id = department.id
WHERE employee.name = 'John';
```

## Multi-level joins

Suppose:

```text
Employee
  ↓
Department
  ↓
Location
```

Then:

```python
Employee.objects.filter(
    department__location__city="Bangalore"
)
```

means:

```text
Employee
→ Department
→ Location
→ city = Bangalore
```

Conceptually:

```sql
SELECT employee.*
FROM employee
JOIN department
    ON employee.department_id = department.id
JOIN location
    ON department.location_id = location.id
WHERE location.city = 'Bangalore';
```

## Many-to-many joins

For:

```python
class Student(models.Model):
    courses = models.ManyToManyField(
        Course,
        related_name="students",
    )
```

query:

```python
Student.objects.filter(
    courses__name="Python"
)
```

conceptually joins:

```text
Student
→ junction table
→ Course
```

## Squad through-model join

For:

```text
Squad
→ SquadMembership
→ Player
```

you can write:

```python
Squad.objects.filter(
    players__full_name="Virat Kohli"
)
```

Django knows that `Squad.players` uses `SquadMembership` as its through table.

Conceptual SQL:

```sql
SELECT squad.*
FROM squad
JOIN squad_membership
    ON squad_membership.squad_id = squad.id
JOIN player
    ON squad_membership.player_id = player.id
WHERE player.full_name = 'Virat Kohli';
```

If you need relationship metadata:

```python
Squad.objects.filter(
    memberships__player__full_name="Virat Kohli",
    memberships__squad_role=SquadRole.CAPTAIN,
)
```

## Query Players belonging to Team India

```python
Player.objects.filter(
    squads__team__name="India"
).distinct()
```

A Player may belong to multiple India Squads, so the join can produce duplicate Player rows. `.distinct()` removes duplicate parent rows.

## Why duplicates happen

Suppose Engineering has two matching employees:

```text
Engineering | John
Engineering | Alice
```

A reverse one-to-many join can therefore produce Engineering twice.

Typical fix:

```python
Department.objects.filter(
    employees__salary__gt=50000
).distinct()
```

The same issue can happen with many-to-many joins.

## isnull

Forward nullable FK:

```python
Employee.objects.filter(
    department__isnull=True
)
```

may be satisfied directly from `employee.department_id IS NULL` without a join.

Reverse “no children” query:

```python
Department.objects.filter(
    employees__isnull=True
)
```

conceptually uses an outer join and keeps departments for which no employee row matched.

## Relationship traversal is not only for filter()

You can traverse relations in:

```text
filter()
exclude()
order_by()
values()
values_list()
annotate()
aggregate()
```

Examples:

```python
Employee.objects.order_by("department__name")

Employee.objects.values(
    "name",
    "department__name",
)
```

## Filter JOIN vs select_related JOIN

```python
Employee.objects.filter(
    department__name="Engineering"
)
```

uses the relation to decide which Employee rows match.

That does not automatically mean the Department object is eagerly populated for later Python access.

If you also need the Department object:

```python
Employee.objects.filter(
    department__name="Engineering"
).select_related(
    "department"
)
```

Think:

```text
filter/relation traversal
→ query logic

select_related
→ eager loading optimization

prefetch_related
→ separate-query eager loading for multi-valued relations
```

## Multi-valued filter subtlety

Across multi-valued relationships, putting multiple conditions in one `.filter()` can require the same related row to satisfy both conditions, while splitting conditions into separate filter calls can result in different join semantics. Always inspect generated SQL for complex multi-valued filters.

## Inspect SQL

```python
qs = Employee.objects.filter(
    department__location__city="Bangalore"
)

print(qs.query)
```

For every `__` path, ask:

```text
What table am I starting from?
What relationship does this hop follow?
What foreign key connects the tables?
Could the join multiply rows?
Do I need distinct()?
```
