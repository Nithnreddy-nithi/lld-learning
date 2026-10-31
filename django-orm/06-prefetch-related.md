# prefetch_related() — Complete Deep Dive

`prefetch_related()` is Django ORM eager loading mainly for **multi-valued relationships**.

Typical cases:

- reverse ForeignKey
- ManyToMany
- Generic/multi-valued relation paths
- relation graphs where a multi-valued hop exists

Unlike select_related(), prefetch_related() normally executes separate SQL queries and then combines the results in Python.

---

# 1. Reverse ForeignKey N+1

Models:

~~~python
class Department(models.Model):
    name = models.CharField(max_length=100)

class Employee(models.Model):
    name = models.CharField(max_length=100)
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="employees",
    )
~~~

Naive:

~~~python
departments = Department.objects.all()

for department in departments:
    for employee in department.employees.all():
        print(employee.name)
~~~

Potentially:

~~~text
1 query
→ Departments

N queries
→ Employees for each Department
~~~

For 100 Departments:

~~~text
101 queries
~~~

---

# 2. Basic prefetch_related()

~~~python
departments = Department.objects.prefetch_related(
    "employees"
)
~~~

Django typically performs:

~~~sql
SELECT *
FROM department;
~~~

then:

~~~sql
SELECT *
FROM employee
WHERE department_id IN (...);
~~~

Then Django matches Employee objects to their Department objects in Python.

---

# 3. Python-side mapping mental model

Imagine:

~~~text
Departments:
1 Engineering
2 HR

Employees:
John  department_id=1
Alice department_id=1
David department_id=2
~~~

Django creates:

~~~text
Department #1
  ↓
[John, Alice]

Department #2
  ↓
[David]
~~~

This mapping happens in the Django worker process memory.

---

# 4. Why separate queries?

If SQL JOIN were used directly for a multi-valued relation:

~~~text
Engineering | John
Engineering | Alice
Engineering | Peter
HR          | David
HR          | Sam
~~~

the Department row is repeated.

prefetch_related() instead fetches parent rows once, related rows separately, then associates them.

---

# 5. ManyToMany

Suppose:

~~~python
class Student(models.Model):
    courses = models.ManyToManyField(
        Course,
        related_name="students",
    )
~~~

Use:

~~~python
students = Student.objects.prefetch_related(
    "courses"
)
~~~

Django uses the M2M junction table in the secondary query and builds Student → Course collections in memory.

---

# 6. Prefetch object

Import:

~~~python
from django.db.models import Prefetch
~~~

Custom filtering:

~~~python
departments = Department.objects.prefetch_related(
    Prefetch(
        "employees",
        queryset=Employee.objects.filter(
            is_active=True
        ),
    )
)
~~~

Now the prefetched relation contains only active Employees.

---

# 7. to_attr

A clearer pattern for filtered subsets:

~~~python
departments = Department.objects.prefetch_related(
    Prefetch(
        "employees",
        queryset=Employee.objects.filter(
            is_active=True
        ),
        to_attr="active_employees",
    )
)
~~~

Usage:

~~~python
for department in departments:
    for employee in department.active_employees:
        print(employee.name)
~~~

With to_attr, Django stores the prefetched result as a normal Python list attribute.

This avoids confusing a filtered subset with the full related manager.

---

# 8. Important cache trap

Suppose:

~~~python
departments = Department.objects.prefetch_related(
    "employees"
)
~~~

Then:

~~~python
department.employees.all()
~~~

can use the prefetch cache.

But:

~~~python
department.employees.filter(
    is_active=True
)
~~~

is a new QuerySet with a new filter condition, so Django can query the DB again.

If you know the filtered subset in advance:

~~~python
Prefetch(
    "employees",
    queryset=Employee.objects.filter(
        is_active=True
    ),
    to_attr="active_employees",
)
~~~

---

# 9. Nested prefetch

Suppose:

~~~text
Department
  ↓ MANY
Employee
  ↓ MANY
Skill
~~~

You can write:

~~~python
Department.objects.prefetch_related(
    "employees__skills"
)
~~~

This may execute multiple queries:

~~~text
Query 1 → Departments
Query 2 → Employees
Query 3 → Skills
~~~

Then Django builds the object graph in Python.

---

# 10. Combine prefetch_related() with select_related()

Suppose:

~~~text
Department
  ↓ MANY
Employee
  ↓ ONE
Manager
~~~

Use:

~~~python
departments = Department.objects.prefetch_related(
    Prefetch(
        "employees",
        queryset=Employee.objects.select_related(
            "manager"
        ),
    )
)
~~~

Typical query shape:

~~~text
Query 1:
Departments

Query 2:
Employees JOIN Manager
WHERE department_id IN (...)
~~~

Excellent because:

~~~text
Department → Employees
is MANY → prefetch

Employee → Manager
is ONE → select_related
~~~

---

# 11. E-commerce example

Relationship:

~~~text
Order
  ├── user      ONE
  └── items     MANY
        └── product ONE
~~~

Optimized:

~~~python
orders = (
    Order.objects
    .select_related(
        "user"
    )
    .prefetch_related(
        Prefetch(
            "items",
            queryset=OrderItem.objects.select_related(
                "product"
            ),
        )
    )
)
~~~

Then:

~~~python
for order in orders:
    print(order.user.email)

    for item in order.items.all():
        print(item.product.name)
~~~

No N+1 on user or product if the relation paths match the serializer/business usage.

---

# 12. Your Squad model

Structure:

~~~text
Squad
  ├── Team           ONE
  └── Memberships    MANY
        └── Player    ONE
~~~

Strong query:

~~~python
squads = (
    Squad.objects
    .select_related(
        "team"
    )
    .prefetch_related(
        Prefetch(
            "memberships",
            queryset=SquadMembership.objects.select_related(
                "player"
            ),
        )
    )
)
~~~

Typical query count:

~~~text
Query 1:
Squad JOIN Team

Query 2:
SquadMembership JOIN Player
WHERE squad_id IN (...)
~~~

Then:

~~~python
for squad in squads:
    print(squad.team.name)

    for membership in squad.memberships.all():
        print(
            membership.player.full_name,
            membership.squad_role,
            membership.jersey_number,
        )
~~~

---

# 13. Active membership subset

~~~python
squads = Squad.objects.prefetch_related(
    Prefetch(
        "memberships",
        queryset=(
            SquadMembership.objects
            .filter(is_active=True)
            .select_related("player")
        ),
        to_attr="active_memberships",
    )
)
~~~

Usage:

~~~python
for squad in squads:
    for membership in squad.active_memberships:
        print(
            membership.player.full_name
        )
~~~

---

# 14. Captain-specific Prefetch

~~~python
squads = Squad.objects.prefetch_related(
    Prefetch(
        "memberships",
        queryset=(
            SquadMembership.objects
            .filter(
                squad_role=SquadRole.CAPTAIN,
                is_active=True,
            )
            .select_related("player")
        ),
        to_attr="active_captains",
    )
)
~~~

Then:

~~~python
for captain_membership in squad.active_captains:
    print(
        captain_membership.player.full_name
    )
~~~

---

# 15. Player → squad_memberships

Your Player reverse relation:

~~~text
Player
  ↓ MANY
SquadMembership
  ↓ ONE
Squad
  ↓ ONE
Team
~~~

Good query:

~~~python
players = Player.objects.prefetch_related(
    Prefetch(
        "squad_memberships",
        queryset=(
            SquadMembership.objects
            .select_related(
                "squad__team"
            )
        ),
    )
)
~~~

Now each Player gets membership objects, while each membership already has Squad and Team eager-loaded.

---

# 16. Squad.players vs Squad.memberships

If you only need Player objects:

~~~python
Squad.objects.prefetch_related(
    "players"
)
~~~

But if you need:

~~~text
role
jersey
joined date
left date
active status
~~~

use:

~~~python
Squad.objects.prefetch_related(
    Prefetch(
        "memberships",
        queryset=SquadMembership.objects.select_related(
            "player"
        ),
    )
)
~~~

because those fields belong to SquadMembership.

---

# 17. Process memory

prefetch_related() builds model objects in the Django process.

Conceptually:

~~~text
QuerySet result cache
  ↓
Department object
  ↓
_prefetched_objects_cache
  ↓
Employee objects
Employee objects
Employee objects
...
~~~

So it can trade:

~~~text
fewer DB round trips
for
more Python memory
~~~

This is often a good trade for paginated APIs, but not automatically for huge relationship sets.

---

# 18. It does not fetch the whole related table

Suppose:

~~~python
Department.objects.filter(
    id=10
).prefetch_related(
    "employees"
)
~~~

Django fetches Employees related to the selected Department set.

It does not necessarily fetch every Employee in the database.

Typical secondary query:

~~~sql
SELECT *
FROM employee
WHERE department_id IN (10);
~~~

---

# 19. Large parent sets and large IN clauses

For many parent IDs:

~~~text
WHERE department_id IN (
  1, 2, 3, 4, ... thousands ...
)
~~~

The secondary query can become large.

Potential costs:

- SQL parsing;
- network payload;
- many related objects;
- worker memory;
- long prefetch time.

Paginate/filter parents and prefetch only what is needed.

---

# 20. prefetch_related() and iterator()

Streaming a huge QuerySet changes caching behavior.

When using iterator-style processing with prefetch behavior, use an appropriate chunk size and understand your Django version's semantics.

Example:

~~~python
for department in (
    Department.objects
    .prefetch_related("employees")
    .iterator(chunk_size=500)
):
    ...
~~~

The goal is to avoid retaining the entire parent QuerySet result in memory at once.

---

# 21. prefetch_related() vs annotate()

This is one of the most important distinctions.

If you need:

~~~python
for employee in department.employees.all():
    print(employee.name)
~~~

you need Employee objects.

Use:

~~~python
Department.objects.prefetch_related(
    "employees"
)
~~~

If you need only:

~~~text
number of employees
average salary
sum of salaries
maximum salary
~~~

do not load every Employee object.

Use:

~~~python
Department.objects.annotate(
    employee_count=Count("employees")
)
~~~

The DB calculates the count.

Memory difference:

~~~text
prefetch_related()
→ Department object
→ 100 Employee objects in Python

annotate()
→ Department object
→ employee_count = 100
~~~

---

# 22. prefetch_related() can technically target FK/O2O

Django can prefetch some single-valued relationships with separate queries.

But if the relationship is naturally single-valued and JOIN loading is appropriate, select_related() is usually more efficient and simpler.

Rule:

~~~text
FK / OneToOne
→ select_related() first choice

reverse FK / ManyToMany
→ prefetch_related() first choice
~~~

---

# 23. DRF example

Suppose:

~~~python
class DepartmentSerializer(serializers.ModelSerializer):
    employees = EmployeeSerializer(
        many=True
    )
~~~

Without prefetching:

~~~python
Department.objects.all()
~~~

the serializer can perform one Employee query per Department.

Better:

~~~python
Department.objects.prefetch_related(
    "employees"
)
~~~

---

# 24. Do not prefetch unused relations

Bad habit:

~~~python
Department.objects.prefetch_related(
    "employees",
    "projects",
    "documents",
    "meetings",
)
~~~

if the endpoint only displays Department name.

This performs unnecessary queries and creates unnecessary Python objects.

Optimize to the actual access pattern.

---

# 25. Query-count experiment

In development:

~~~python
from django.db import connection, reset_queries

reset_queries()

departments = (
    Department.objects
    .prefetch_related(
        "employees"
    )
)

for department in departments:
    list(
        department.employees.all()
    )

print(
    len(connection.queries)
)
~~~

Compare with the same code without prefetch_related().

---

# 26. Final mental model

~~~text
select_related()
→ one related object
→ SQL JOIN
→ related object constructed from same query

prefetch_related()
→ many related objects
→ separate SQL queries
→ Django maps objects together in Python
~~~

Strong interview answer:

> prefetch_related() is mainly used for multi-valued relations such as reverse ForeignKey and ManyToMany. Django fetches parent and related rows in separate queries, then associates the related model objects with their parents in Python to avoid N+1 queries.
