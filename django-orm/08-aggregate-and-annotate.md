# aggregate() and annotate() — Complete Notes

These two methods both ask the database to calculate values, but they answer different questions.

~~~text
aggregate()
→ one summary for the whole QuerySet
→ returns a dictionary
→ terminal operation

annotate()
→ calculated value for each object/group
→ returns a QuerySet
→ chainable
~~~

---

# 1. Example models

~~~python
from django.db import models

class Department(models.Model):
    name = models.CharField(max_length=100)

class Employee(models.Model):
    name = models.CharField(max_length=100)
    salary = models.IntegerField()
    is_active = models.BooleanField(default=True)
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="employees",
    )
~~~

Sample data:

| id | name | salary | department |
|---:|---|---:|---|
| 1 | John | 50000 | Engineering |
| 2 | Alice | 70000 | Engineering |
| 3 | David | 40000 | HR |
| 4 | Peter | 60000 | HR |
| 5 | Sam | 80000 | HR |

---

# 2. aggregate() — whole QuerySet summary

Import the common aggregate functions:

~~~python
from django.db.models import Count, Sum, Avg, Min, Max
~~~

## Count

~~~python
Employee.objects.aggregate(
    total_employees=Count("id")
)
~~~

Result:

~~~python
{"total_employees": 5}
~~~

Conceptual SQL:

~~~sql
SELECT COUNT(id) AS total_employees
FROM employee;
~~~

For a simple row count, this is usually simpler:

~~~python
Employee.objects.count()
~~~

which directly returns:

~~~python
5
~~~

## Sum

~~~python
Employee.objects.aggregate(
    total_salary=Sum("salary")
)
~~~

Result:

~~~python
{"total_salary": 300000}
~~~

SQL idea:

~~~sql
SELECT SUM(salary) AS total_salary
FROM employee;
~~~

## Avg

~~~python
from django.db.models import Avg

Employee.objects.aggregate(
    average_salary=Avg("salary")
)
~~~

Result:

~~~python
{"average_salary": 60000.0}
~~~

The database performs the calculation; Django does not need to load every Employee object into Python just to compute the average.

## Min and Max

~~~python
Employee.objects.aggregate(
    minimum_salary=Min("salary"),
    maximum_salary=Max("salary"),
)
~~~

Result:

~~~python
{
    "minimum_salary": 40000,
    "maximum_salary": 80000,
}
~~~

Important: Max("salary") returns the maximum salary value, not the Employee object earning it.

If you need the Employee object:

~~~python
employee = (
    Employee.objects
    .order_by("-salary", "id")
    .first()
)
~~~

## Multiple aggregate calculations in one query

~~~python
result = Employee.objects.aggregate(
    total_employees=Count("id"),
    total_salary=Sum("salary"),
    average_salary=Avg("salary"),
    minimum_salary=Min("salary"),
    maximum_salary=Max("salary"),
)
~~~

Result:

~~~python
{
    "total_employees": 5,
    "total_salary": 300000,
    "average_salary": 60000.0,
    "minimum_salary": 40000,
    "maximum_salary": 80000,
}
~~~

Conceptually:

~~~sql
SELECT
    COUNT(id),
    SUM(salary),
    AVG(salary),
    MIN(salary),
    MAX(salary)
FROM employee;
~~~

One aggregate() call can therefore calculate several summaries in one SQL query.

---

# 3. aggregate() with filter()

filter() decides which rows participate in the calculation.

~~~python
Employee.objects.filter(
    is_active=True
).aggregate(
    total_salary=Sum("salary")
)
~~~

Conceptual SQL:

~~~sql
SELECT SUM(salary)
FROM employee
WHERE is_active = TRUE;
~~~

Another example:

~~~python
Employee.objects.filter(
    department_id=10
).aggregate(
    average_salary=Avg("salary")
)
~~~

Think:

~~~text
filter()
→ choose source rows

aggregate()
→ calculate one final summary
~~~

---

# 4. Aggregate through a related manager

If you already have a Department instance:

~~~python
department = Department.objects.get(id=10)

result = department.employees.aggregate(
    total_salary=Sum("salary")
)
~~~

Equivalent idea:

~~~python
Employee.objects.filter(
    department=department
).aggregate(
    total_salary=Sum("salary")
)
~~~

---

# 5. aggregate() is terminal

This returns a dictionary:

~~~python
result = Employee.objects.aggregate(
    total_salary=Sum("salary")
)
~~~

So this is invalid:

~~~python
Employee.objects.aggregate(
    total_salary=Sum("salary")
).filter(is_active=True)
~~~

There is no QuerySet left to filter.

Correct:

~~~python
Employee.objects.filter(
    is_active=True
).aggregate(
    total_salary=Sum("salary")
)
~~~

Mental model:

~~~text
Manager
  ↓
QuerySet
  ↓
filter()
  ↓
QuerySet
  ↓
aggregate()
  ↓
dictionary
~~~

---

# 6. aggregate() executes immediately

This is lazy:

~~~python
qs = Employee.objects.filter(
    is_active=True
)
~~~

But:

~~~python
result = qs.aggregate(
    total_salary=Sum("salary")
)
~~~

must execute SQL immediately because Django has to return the final dictionary.

---

# 7. annotate() — calculated value per object/group

Suppose the question is:

> How many Employees are in each Department?

Use annotate():

~~~python
departments = Department.objects.annotate(
    employee_count=Count("employees")
)
~~~

Now every returned Department object has a temporary calculated attribute:

~~~python
for department in departments:
    print(
        department.name,
        department.employee_count,
    )
~~~

Output could be:

~~~text
Engineering 2
HR 3
~~~

The model itself does not permanently contain:

~~~python
employee_count = models.IntegerField()
~~~

The annotation exists only on objects produced by that annotated QuerySet.

---

# 8. SQL and GROUP BY mental model

The join before grouping looks conceptually like:

~~~text
Engineering | John
Engineering | Alice
HR          | David
HR          | Peter
HR          | Sam
~~~

Then SQL groups by Department:

~~~text
Engineering
  ├── John
  └── Alice

HR
  ├── David
  ├── Peter
  └── Sam
~~~

Then COUNT produces:

~~~text
Engineering → 2
HR          → 3
~~~

Conceptual SQL:

~~~sql
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
~~~

That is the core annotate() mental model.

---

# 9. annotate() returns a QuerySet

Unlike aggregate(), annotate() remains chainable.

~~~python
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
~~~

This is one of annotate()'s biggest strengths.

---

# 10. Filtering annotated values and HAVING

Suppose:

> Return Departments with more than 10 Employees.

~~~python
Department.objects.annotate(
    employee_count=Count("employees")
).filter(
    employee_count__gt=10
)
~~~

Conceptually:

~~~sql
SELECT
    department.id,
    COUNT(employee.id) AS employee_count
FROM department
LEFT JOIN employee
    ON employee.department_id = department.id
GROUP BY department.id
HAVING COUNT(employee.id) > 10;
~~~

Remember:

~~~text
WHERE
→ filters source rows before aggregation

HAVING
→ filters groups after aggregation
~~~

Django decides the correct SQL based on the expression you filter on.

---

# 11. Sum, Avg, Min, Max per Department

~~~python
departments = Department.objects.annotate(
    employee_count=Count("employees"),
    total_salary=Sum("employees__salary"),
    average_salary=Avg("employees__salary"),
    lowest_salary=Min("employees__salary"),
    highest_salary=Max("employees__salary"),
)
~~~

Now:

~~~python
for department in departments:
    print(
        department.name,
        department.employee_count,
        department.total_salary,
        department.average_salary,
        department.lowest_salary,
        department.highest_salary,
    )
~~~

The DB can calculate all of these in one grouped query.

---

# 12. annotate() with expressions

annotate() is not limited to aggregate functions.

Suppose Product has:

~~~python
class Product(models.Model):
    price = models.DecimalField(...)
    quantity = models.IntegerField()
~~~

You can calculate a temporary field:

~~~python
from django.db.models import F

products = Product.objects.annotate(
    inventory_value=F("price") * F("quantity")
)
~~~

Then:

~~~python
for product in products:
    print(product.inventory_value)
~~~

You can also filter on it:

~~~python
Product.objects.annotate(
    inventory_value=F("price") * F("quantity")
).filter(
    inventory_value__gt=100000
)
~~~

The calculation and filtering happen database-side.

---

# 13. String expression example

Suppose Employee has first_name and last_name:

~~~python
from django.db.models import Value
from django.db.models.functions import Concat

employees = Employee.objects.annotate(
    full_name=Concat(
        "first_name",
        Value(" "),
        "last_name",
    )
)
~~~

Then:

~~~python
employee.full_name
~~~

is available on each annotated object.

---

# 14. values() + annotate() = GROUP BY pattern

Very important reporting pattern:

~~~python
Employee.objects.values(
    "department_id"
).annotate(
    employee_count=Count("id")
)
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

Conceptual SQL:

~~~sql
SELECT
    department_id,
    COUNT(id)
FROM employee
GROUP BY department_id;
~~~

A useful pattern to remember:

~~~python
Model.objects.values(
    "group_field"
).annotate(
    result=AggregateFunction("field")
)
~~~

Example by status:

~~~python
Order.objects.values(
    "status"
).annotate(
    order_count=Count("id")
)
~~~

Possible result:

~~~python
[
    {"status": "pending", "order_count": 20},
    {"status": "paid", "order_count": 50},
    {"status": "cancelled", "order_count": 5},
]
~~~

---

# 15. Order of values() and annotate() matters

This:

~~~python
Employee.objects.values(
    "department_id"
).annotate(
    employee_count=Count("id")
)
~~~

clearly groups Employees by department_id.

But:

~~~python
Employee.objects.annotate(
    employee_count=Count("id")
).values(
    "department_id",
    "employee_count",
)
~~~

can have different grouping/projection behavior.

With aggregation, QuerySet method order matters.

---

# 16. filter() before vs after annotate()

These are not always equivalent:

~~~python
Department.objects.filter(
    employees__salary__gt=50000
).annotate(
    employee_count=Count("employees")
)
~~~

and:

~~~python
Department.objects.annotate(
    employee_count=Count("employees")
).filter(
    employees__salary__gt=50000
)
~~~

Why?

Because one can restrict joined Employee rows before calculating the aggregate, while the other can introduce filtering after/alongside an already-defined aggregation path.

Rule:

~~~text
filter(...).annotate(...)
is not always the same as
annotate(...).filter(...)
~~~

Always inspect what rows are being counted.

---

# 17. Conditional aggregation

Suppose you want both:

- total Employees;
- active Employees.

Use filtered aggregates:

~~~python
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
~~~

If Engineering has:

~~~text
John  active=True
Alice active=True
Mike  active=False
~~~

then:

~~~text
employee_count = 3
active_employee_count = 2
~~~

One grouped query can calculate both values.

---

# 18. distinct=True

Multi-valued joins can multiply rows.

When that would cause the same logical entity to be counted more than once:

~~~python
Department.objects.annotate(
    employee_count=Count(
        "employees",
        distinct=True,
    )
)
~~~

Conceptually:

~~~sql
COUNT(DISTINCT employee.id)
~~~

Do not add distinct=True blindly. Use it to solve real duplicate-counting caused by the join graph.

---

# 19. Empty groups and None

Count() normally gives zero when no related rows exist.

But Sum()/Avg()/Min()/Max() can produce None if there are no values.

Example:

~~~python
Department.objects.annotate(
    total_salary=Sum("employees__salary")
)
~~~

A Department with no Employees may have:

~~~python
department.total_salary is None
~~~

Use Coalesce when you need a fallback:

~~~python
from django.db.models import Sum, Value
from django.db.models.functions import Coalesce

Department.objects.annotate(
    total_salary=Coalesce(
        Sum("employees__salary"),
        Value(0),
    )
)
~~~

Now the empty Department can receive 0.

---

# 20. annotate() can prevent N+1 count queries

Potential N+1:

~~~python
departments = Department.objects.all()

for department in departments:
    print(
        department.employees.count()
    )
~~~

For 100 Departments, this can mean:

~~~text
1 Department query
+
100 COUNT queries
=
101 queries
~~~

Better:

~~~python
departments = Department.objects.annotate(
    employee_count=Count("employees")
)

for department in departments:
    print(
        department.employee_count
    )
~~~

The database performs the grouped count.

---

# 21. annotate() vs prefetch_related()

This distinction is essential.

If you need the Employee objects themselves:

~~~python
for employee in department.employees.all():
    print(employee.name)
~~~

use prefetch_related():

~~~python
Department.objects.prefetch_related(
    "employees"
)
~~~

Django fetches Employee rows and creates Employee Python objects.

If you only need a calculation:

~~~text
count
sum
average
minimum
maximum
~~~

use annotate():

~~~python
Department.objects.annotate(
    employee_count=Count("employees")
)
~~~

The database calculates the number and returns only that calculated value with each Department row.

Mental model:

~~~text
prefetch_related()
→ "Give me related objects."

annotate()
→ "Calculate information about related rows."
~~~

---

# 22. Python-memory difference

prefetch_related():

~~~text
Department object
  ↓
prefetch cache
  ├── Employee object
  ├── Employee object
  ├── Employee object
  └── ...
~~~

annotate():

~~~text
Department object
  + employee_count = 100
~~~

The database counted the employees. Django did not need to instantiate 100 Employee objects just to know the count.

This is why annotate() can be much more memory-efficient when only summary data is needed.

---

# 23. Squad examples

Your relationship:

~~~text
Squad
  ↓
memberships
  ↓
SquadMembership
~~~

## Count all memberships per Squad

~~~python
from django.db.models import Count

squads = Squad.objects.annotate(
    member_count=Count(
        "memberships"
    )
)
~~~

Then:

~~~python
for squad in squads:
    print(
        squad.name,
        squad.member_count,
    )
~~~

Possible output:

~~~text
India ODI Squad 15
India Test Squad 18
India T20 Squad 16
~~~

## Count only active memberships

~~~python
from django.db.models import Count, Q

squads = Squad.objects.annotate(
    active_player_count=Count(
        "memberships",
        filter=Q(
            memberships__is_active=True
        ),
    )
)
~~~

## Count active captains

~~~python
squads = Squad.objects.annotate(
    captain_count=Count(
        "memberships",
        filter=Q(
            memberships__squad_role=SquadRole.CAPTAIN,
            memberships__is_active=True,
        ),
    )
)
~~~

You can detect bad data:

~~~python
squads.filter(
    captain_count__gt=1
)
~~~

## Total and active memberships together

~~~python
squads = Squad.objects.annotate(
    total_members=Count(
        "memberships"
    ),
    active_members=Count(
        "memberships",
        filter=Q(
            memberships__is_active=True
        ),
    ),
)
~~~

## Find Squads with at least 15 active memberships

~~~python
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
~~~

Conceptually:

~~~text
Squad
  ↓
group related memberships by Squad
  ↓
count only active memberships
  ↓
keep groups where count >= 15
~~~

## Group membership rows by squad_id

~~~python
SquadMembership.objects.values(
    "squad_id"
).annotate(
    member_count=Count("id")
)
~~~

Result:

~~~python
[
    {
        "squad_id": 1,
        "member_count": 15,
    },
    {
        "squad_id": 2,
        "member_count": 18,
    },
]
~~~

---

# 24. Deep relationship annotation

Example:

~~~python
Team.objects.annotate(
    player_count=Count(
        "squads__memberships__player",
        distinct=True,
    )
)
~~~

Path:

~~~text
Team
  ↓
Squads
  ↓
Memberships
  ↓
Player
~~~

distinct=True may be necessary because the same Player can appear through multiple SquadMembership rows.

---

# 25. Final mental model

aggregate():

~~~text
Employee rows
  ↓
database calculation
  ↓
ONE final result

Example:
average salary of all Employees
~~~

annotate():

~~~text
Department rows
  ↓
JOIN related Employees
  ↓
GROUP BY Department
  ↓
calculation for EACH Department
  ↓
Department objects + temporary calculated attributes
~~~

Strong interview answer:

> aggregate() calculates an overall summary for a QuerySet and returns a dictionary. annotate() adds database-calculated values to each object or group and returns a chainable QuerySet. values() before annotate() is commonly used to create SQL GROUP BY style reports.
