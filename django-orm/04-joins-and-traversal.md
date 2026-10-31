# JOINs and Relationship Traversal — Complete Notes

Django ORM hides SQL syntax, but relationship traversal is fundamentally SQL JOIN behavior.

Core idea:

~~~text
Model relationship
  ↓
double-underscore traversal
  ↓
Django determines JOIN path
  ↓
SQL JOIN
~~~

---

# 1. Forward relationship traversal

Models:

~~~python
class Department(models.Model):
    name = models.CharField(
        max_length=100
    )

class Employee(models.Model):
    name = models.CharField(
        max_length=100
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="employees",
    )
~~~

Employee contains the FK, so:

~~~text
Employee → Department
~~~

is forward traversal.

Query:

~~~python
Employee.objects.filter(
    department__name="Engineering"
)
~~~

Break the path:

~~~text
department
→ follow ForeignKey

name
→ field on Department
~~~

Conceptual SQL:

~~~sql
SELECT employee.*
FROM employee
INNER JOIN department
    ON employee.department_id = department.id
WHERE department.name = 'Engineering';
~~~

---

# 2. FK existence does not mean every query joins

This:

~~~python
Employee.objects.all()
~~~

does not need a Department JOIN merely because Employee has a department FK.

Django adds joins when the query actually requires related-table data.

---

# 3. Lookup after traversal

~~~python
Employee.objects.filter(
    department__name__icontains="engine"
)
~~~

Break it:

~~~text
department
→ relationship

name
→ related model field

icontains
→ lookup
~~~

---

# 4. Reverse relationship traversal

Because Employee defines:

~~~python
related_name="employees"
~~~

Department can traverse backward:

~~~python
Department.objects.filter(
    employees__name="John"
)
~~~

Conceptual SQL:

~~~sql
SELECT department.*
FROM department
INNER JOIN employee
    ON employee.department_id = department.id
WHERE employee.name = 'John';
~~~

Forward:

~~~text
Employee.department
~~~

Reverse:

~~~text
Department.employees
~~~

---

# 5. Multi-level JOINs

Suppose:

~~~text
Employee
  ↓ department
Department
  ↓ location
Location
  ↓ city
~~~

Query:

~~~python
Employee.objects.filter(
    department__location__city="Bangalore"
)
~~~

Conceptually:

~~~sql
SELECT employee.*
FROM employee
JOIN department
    ON employee.department_id = department.id
JOIN location
    ON department.location_id = location.id
WHERE location.city = 'Bangalore';
~~~

Mental model:

~~~text
A.objects.filter(
    b__c__d=value
)

start A
→ follow b
→ follow c
→ compare d
~~~

---

# 6. ManyToMany JOIN

Suppose:

~~~python
class Student(models.Model):
    courses = models.ManyToManyField(
        Course,
        related_name="students",
    )
~~~

Query:

~~~python
Student.objects.filter(
    courses__name="Python"
)
~~~

Conceptually:

~~~text
Student
→ M2M junction table
→ Course
~~~

SQL roughly:

~~~sql
SELECT student.*
FROM student
JOIN student_courses
    ON student_courses.student_id = student.id
JOIN course
    ON course.id = student_courses.course_id
WHERE course.name = 'Python';
~~~

---

# 7. Your Squad → Player JOIN

Your relation is:

~~~text
Squad
→ SquadMembership
→ Player
~~~

because:

~~~python
players = models.ManyToManyField(
    Player,
    through="SquadMembership",
    related_name="squads",
)
~~~

You can write:

~~~python
Squad.objects.filter(
    players__full_name="Virat Kohli"
)
~~~

Conceptually:

~~~sql
SELECT squad.*
FROM squad
JOIN squad_membership
    ON squad_membership.squad_id = squad.id
JOIN player
    ON squad_membership.player_id = player.id
WHERE player.full_name = 'Virat Kohli';
~~~

Django knows to use SquadMembership because it is the explicit through model.

---

# 8. Query relationship metadata through memberships

If you need:

~~~text
Player name
+
captain role
~~~

query the through model path:

~~~python
Squad.objects.filter(
    memberships__player__full_name="Virat Kohli",
    memberships__squad_role=SquadRole.CAPTAIN,
)
~~~

This reads:

~~~text
Squad
→ memberships
→ player
→ full_name

and

Squad
→ memberships
→ squad_role
~~~

---

# 9. Team JOIN

Your Squad has:

~~~python
team = models.ForeignKey(
    Team,
    on_delete=models.PROTECT,
    related_name="squads",
)
~~~

So:

~~~python
Squad.objects.filter(
    team__name="India"
)
~~~

is:

~~~text
Squad
→ Team
→ name
~~~

---

# 10. Player in Team India

~~~python
Player.objects.filter(
    squads__team__name="India"
).distinct()
~~~

Path:

~~~text
Player
→ Squads
→ Team
→ name
~~~

Because a Player can belong to several India Squads, the JOIN may produce duplicate Player rows.

Hence:

~~~python
.distinct()
~~~

can be required.

---

# 11. Captain of India example

~~~python
Player.objects.filter(
    squad_memberships__squad_role=(
        SquadRole.CAPTAIN
    ),
    squad_memberships__squad__team__name="India",
).distinct()
~~~

Path:

~~~text
Player
→ squad_memberships
→ squad_role

Player
→ squad_memberships
→ squad
→ team
→ name
~~~

---

# 12. Why duplicates happen

Suppose Department Engineering has two matching Employees:

~~~text
Engineering | John
Engineering | Alice
~~~

A reverse JOIN produces two joined rows for Engineering.

So:

~~~python
Department.objects.filter(
    employees__salary__gt=50000
)
~~~

can return duplicate Department rows at SQL result level.

Use:

~~~python
Department.objects.filter(
    employees__salary__gt=50000
).distinct()
~~~

when you want unique Department objects.

---

# 13. Forward FK usually does not multiply starting rows

This:

~~~python
Employee.objects.filter(
    department__name="Engineering"
)
~~~

starts from Employee.

Each Employee has at most one Department.

So following the FK normally does not duplicate Employee rows.

The duplication problem is mainly associated with traversing:

~~~text
reverse ForeignKey
ManyToMany
other multi-valued relations
~~~

---

# 14. INNER JOIN behavior

A normal related-field filter like:

~~~python
Employee.objects.filter(
    department__name="Engineering"
)
~~~

usually needs an INNER JOIN because a matching Department row is required.

Conceptually:

~~~sql
INNER JOIN department ...
WHERE department.name = 'Engineering'
~~~

Rows with no Department cannot satisfy that condition.

---

# 15. LEFT OUTER JOIN behavior

Suppose you ask:

> Departments with no Employees.

~~~python
Department.objects.filter(
    employees__isnull=True
)
~~~

Conceptually:

~~~sql
SELECT department.*
FROM department
LEFT OUTER JOIN employee
    ON employee.department_id = department.id
WHERE employee.id IS NULL;
~~~

The outer join is needed to preserve Departments that have no matching Employee.

---

# 16. Forward isnull may not need a JOIN

Suppose Employee.department is nullable.

~~~python
Employee.objects.filter(
    department__isnull=True
)
~~~

Django may simply test:

~~~sql
WHERE employee.department_id IS NULL
~~~

because the FK column already lives on Employee.

No related-table data is required.

---

# 17. Relationship traversal in exclude()

~~~python
Employee.objects.exclude(
    department__name="HR"
)
~~~

Django can use relationship traversal in exclusions too.

---

# 18. Relationship traversal in order_by()

~~~python
Employee.objects.order_by(
    "department__name"
)
~~~

Django may JOIN Department to order by its name.

---

# 19. Relationship traversal in values()

~~~python
Employee.objects.values(
    "name",
    "department__name",
)
~~~

returns dictionary rows such as:

~~~python
{
    "name": "John",
    "department__name": "Engineering",
}
~~~

Django performs the JOIN needed to select Department.name.

---

# 20. Relationship traversal in values_list()

~~~python
Employee.objects.values_list(
    "name",
    "department__name",
)
~~~

Rows:

~~~python
("John", "Engineering")
~~~

---

# 21. Relationship traversal in annotate()

~~~python
from django.db.models import Count

Department.objects.annotate(
    employee_count=Count(
        "employees"
    )
)
~~~

Django joins Employees and groups by Department.

---

# 22. Relationship traversal in aggregate()

~~~python
Department.objects.aggregate(
    total_employees=Count(
        "employees"
    )
)
~~~

Again, the relationship path can cause joins.

---

# 23. JOIN for filtering vs eager loading

This:

~~~python
Employee.objects.filter(
    department__name="Engineering"
)
~~~

uses Department to determine which Employees match.

But later:

~~~python
employee.department
~~~

is an object-access concern.

If you need Department objects too:

~~~python
Employee.objects     .filter(
        department__name="Engineering"
    )     .select_related(
        "department"
    )
~~~

Remember:

~~~text
relationship traversal
→ query logic

select_related()
→ eager load single object

prefetch_related()
→ eager load collections
~~~

---

# 24. Multi-valued filter subtlety

Suppose Blog has many Entry rows.

Conditions in one filter call:

~~~python
Blog.objects.filter(
    entries__headline__contains="Lennon",
    entries__pub_date__year=2008,
)
~~~

typically mean:

> Find Blogs having a related Entry where that same joined Entry satisfies both conditions.

But separating them:

~~~python
Blog.objects.filter(
    entries__headline__contains="Lennon"
).filter(
    entries__pub_date__year=2008
)
~~~

can allow different related Entry rows to satisfy the two conditions because separate joins may be introduced.

This is an advanced but important multi-valued relationship detail.

Rule:

~~~text
Across reverse FK/M2M paths,
same filter() vs separate filter() calls
can produce different semantics.
~~~

---

# 25. JOIN reuse

Django's query compiler can reuse compatible joins within a query rather than blindly creating a completely new join for every field reference.

You should still inspect generated SQL for complex queries instead of guessing.

---

# 26. Active Player example

~~~python
Player.objects.filter(
    squad_memberships__is_active=True,
    squad_memberships__squad__is_active=True,
).distinct()
~~~

This says:

~~~text
Player
→ active membership
→ whose Squad is active
~~~

The reverse relation is multi-valued, so distinct() is often appropriate.

---

# 27. Squad role and Team together

~~~python
Player.objects.filter(
    squad_memberships__squad_role=(
        SquadRole.CAPTAIN
    ),
    squad_memberships__squad__team__name="India",
).distinct()
~~~

Because both conditions are in the same filter() call on the same multi-valued path, they are intended to describe the same joined membership row.

---

# 28. Inspect generated SQL

~~~python
qs = Employee.objects.filter(
    department__location__city="Bangalore"
)

print(
    qs.query
)
~~~

This is one of the best ways to learn Django ORM deeply.

For every JOIN query ask:

~~~text
1. What is the starting table?
2. Which __ path is being followed?
3. What FK/junction table connects the next table?
4. Is the relationship single-valued or multi-valued?
5. Could this multiply starting rows?
6. Do I need distinct()?
7. Am I only filtering, or do I also need eager loading?
~~~

---

# 29. Final mental model

~~~text
A.objects.filter(
    b__c__d=value
)

A
↓
relationship b
↓
related model
↓
relationship c
↓
related model
↓
field d comparison
~~~

Django's double-underscore traversal is essentially a high-level way to describe SQL relationship navigation and lookups.
