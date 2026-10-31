# Managers and Custom QuerySets — Complete Notes

The most useful mental model is:

~~~text
Manager
→ starts a model query

QuerySet
→ continues and composes the query
~~~

Example:

~~~python
Employee.objects.active().high_salary()
~~~

Break it down:

~~~text
Employee
  ↓
objects
  ↓
Manager
  ↓
active()
  ↓
EmployeeQuerySet
  ↓
high_salary()
  ↓
EmployeeQuerySet
~~~

---

# 1. What is a Manager?

Every Django model normally has:

~~~python
objects = models.Manager()
~~~

When you write:

~~~python
Employee.objects.all()
~~~

`objects` is the Manager.

The Manager is attached to the model and acts as the entry point for table-level ORM operations.

Examples:

~~~python
Employee.objects.all()
Employee.objects.filter(...)
Employee.objects.get(...)
Employee.objects.create(...)
~~~

---

# 2. Manager produces QuerySets

Conceptually:

~~~text
Employee.objects
  ↓
Manager
  ↓
get_queryset()
  ↓
Employee QuerySet
~~~

A Manager's `get_queryset()` defines the baseline QuerySet it returns.

---

# 3. Custom Manager

Suppose:

~~~python
class Employee(models.Model):
    name = models.CharField(max_length=100)
    active = models.BooleanField(default=True)
~~~

You can define:

~~~python
class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(
            active=True
        )
~~~

Attach:

~~~python
class Employee(models.Model):
    ...

    objects = models.Manager()
    active_objects = ActiveManager()
~~~

Usage:

~~~python
Employee.objects.all()
~~~

returns all Employees.

~~~python
Employee.active_objects.all()
~~~

returns only active Employees.

---

# 4. Why get_queryset() matters

This:

~~~python
def get_queryset(self):
    return super().get_queryset().filter(
        active=True
    )
~~~

means:

~~~text
Whenever this manager starts a query,
begin with active=True already applied.
~~~

Be careful if you hide rows globally through the default Manager because admin code, related-object behavior, recovery jobs, or internal code may need complete data.

---

# 5. Problem: repeated query logic

Suppose the application repeatedly writes:

~~~python
Employee.objects.filter(
    active=True,
    deleted=False,
)
~~~

and elsewhere:

~~~python
Employee.objects.filter(
    active=True,
    deleted=False,
    salary__gt=100000,
)
~~~

and elsewhere:

~~~python
Employee.objects.filter(
    active=True,
    deleted=False,
).order_by("-salary")
~~~

The business rule:

~~~text
active=True
deleted=False
~~~

is duplicated everywhere.

Custom QuerySets solve this.

---

# 6. Basic custom QuerySet

~~~python
class EmployeeQuerySet(models.QuerySet):
    def active(self):
        return self.filter(
            active=True,
            deleted=False,
        )

    def high_salary(self):
        return self.filter(
            salary__gt=100000
        )
~~~

Attach it:

~~~python
class Employee(models.Model):
    ...

    objects = (
        EmployeeQuerySet.as_manager()
    )
~~~

Now:

~~~python
Employee.objects.active()
~~~

and:

~~~python
Employee.objects.active().high_salary()
~~~

work.

---

# 7. Why chaining works

Each custom method returns:

~~~python
self.filter(...)
~~~

and `filter()` returns another QuerySet.

So:

~~~text
Employee.objects
  ↓
active()
  ↓
EmployeeQuerySet
  ↓
high_salary()
  ↓
EmployeeQuerySet
  ↓
order_by()
  ↓
EmployeeQuerySet
~~~

Example:

~~~python
employees = (
    Employee.objects
    .active()
    .high_salary()
    .order_by("-salary")
)
~~~

---

# 8. What is self inside a QuerySet method?

~~~python
def active(self):
    return self.filter(
        active=True
    )
~~~

Here:

~~~text
self
=
the current QuerySet state
~~~

Example:

~~~python
qs = Employee.objects.filter(
    department_id=10
)

qs = qs.active()
~~~

The custom method continues from the existing condition.

Conceptually:

~~~text
department_id = 10
  +
active = TRUE
~~~

So custom QuerySet methods do not necessarily start from the whole table.

---

# 9. QuerySet methods are composable

~~~python
Employee.objects.filter(
    department_id=10
).active().high_salary()
~~~

Conceptual final SQL:

~~~sql
SELECT *
FROM employee
WHERE department_id = 10
  AND active = TRUE
  AND deleted = FALSE
  AND salary > 100000;
~~~

The intermediate method calls normally build one final query rather than executing one query each.

---

# 10. QuerySet laziness

This:

~~~python
qs = (
    Employee.objects
    .active()
    .high_salary()
    .order_by("-salary")
)
~~~

usually does not hit the DB immediately.

SQL executes when evaluated:

~~~python
list(qs)

for employee in qs:
    ...

qs.first()
qs.count()
~~~

So:

~~~text
active()
→ modify query state

high_salary()
→ modify query state

order_by()
→ modify query state

evaluation
→ execute SQL
~~~

---

# 11. Order can often be flexible

These simple filters:

~~~python
Employee.objects.active().high_salary()
~~~

and:

~~~python
Employee.objects.high_salary().active()
~~~

generally express the same conditions.

But this is not a universal rule for all QuerySet operations. Aggregation, slicing, annotations, grouping, and multi-valued joins can make method order significant.

---

# 12. QuerySet immutability mental model

~~~python
qs1 = Employee.objects.all()

qs2 = qs1.filter(
    active=True
)
~~~

Think:

~~~text
qs1
→ all Employees

qs2
→ derived QuerySet
→ active Employees
~~~

Django generally creates/clones query state instead of mutating qs1 in place.

That is why reusable chainable QuerySet methods feel functional.

---

# 13. Why not normal helper functions?

You could write:

~~~python
def get_active_employees():
    return Employee.objects.filter(
        active=True,
        deleted=False,
    )
~~~

But custom QuerySets integrate directly into ORM chaining:

~~~python
Employee.objects     .filter(department=department)     .active()     .high_salary()
~~~

This is more composable and expressive.

---

# 14. Parameterized QuerySet methods

~~~python
class EmployeeQuerySet(models.QuerySet):
    def active(self):
        return self.filter(
            active=True,
            deleted=False,
        )

    def min_salary(self, amount):
        return self.filter(
            salary__gte=amount
        )

    def for_department(self, department):
        return self.filter(
            department=department
        )
~~~

Usage:

~~~python
Employee.objects     .active()     .for_department(department)     .min_salary(75000)
~~~

---

# 15. QuerySet method with relationship traversal

~~~python
class EmployeeQuerySet(models.QuerySet):
    def engineers(self):
        return self.filter(
            department__name="Engineering"
        )
~~~

Usage:

~~~python
Employee.objects.engineers()
~~~

Django can generate the required JOIN.

---

# 16. QuerySet method with select_related()

~~~python
class EmployeeQuerySet(models.QuerySet):
    def with_department(self):
        return self.select_related(
            "department"
        )
~~~

Usage:

~~~python
Employee.objects     .active()     .with_department()
~~~

This centralizes reusable eager-loading behavior.

---

# 17. QuerySet method with prefetch_related()

~~~python
def with_skills(self):
    return self.prefetch_related(
        "skills"
    )
~~~

Usage:

~~~python
Employee.objects     .active()     .with_skills()
~~~

---

# 18. QuerySet method with annotate()

~~~python
from django.db.models import Count

class DepartmentQuerySet(models.QuerySet):
    def with_employee_count(self):
        return self.annotate(
            employee_count=Count(
                "employees"
            )
        )
~~~

Usage:

~~~python
departments = (
    Department.objects
    .with_employee_count()
)
~~~

Then:

~~~python
department.employee_count
~~~

is available.

---

# 19. QuerySet method with Q()

~~~python
from django.db.models import Q

class EmployeeQuerySet(models.QuerySet):
    def searchable(self, text):
        return self.filter(
            Q(name__icontains=text)
            | Q(email__icontains=text)
        )
~~~

Usage:

~~~python
Employee.objects.searchable(
    "nithin"
)
~~~

---

# 20. QuerySet method with F()

~~~python
from django.db.models import F

class EmployeeQuerySet(models.QuerySet):
    def over_target(self):
        return self.filter(
            sales__gt=F("target")
        )
~~~

Usage:

~~~python
Employee.objects.over_target()
~~~

---

# 21. Reuse QuerySet methods inside each other

~~~python
class EmployeeQuerySet(models.QuerySet):
    def not_deleted(self):
        return self.filter(
            deleted=False
        )

    def active(self):
        return (
            self.not_deleted()
            .filter(active=True)
        )

    def high_salary(self):
        return self.filter(
            salary__gt=100000
        )
~~~

Now:

~~~python
Employee.objects.active().high_salary()
~~~

keeps the business rules centralized.

---

# 22. Chainable vs terminal methods

Chainable methods return a QuerySet:

~~~text
active()
paid()
recent()
with_department()
for_user()
~~~

Terminal methods return a final value/object:

~~~text
count()
exists()
first()
last()
aggregate()
~~~

Example:

~~~python
Employee.objects.active().count()
~~~

returns an integer.

After that you cannot continue normal QuerySet chaining.

---

# 23. Why custom QuerySet instead of Manager methods for filters?

Suppose:

~~~python
class EmployeeManager(models.Manager):
    def active(self):
        return self.filter(
            active=True
        )

    def high_salary(self):
        return self.filter(
            salary__gt=100000
        )
~~~

Employee.objects.active() works.

But after active(), the return value is a QuerySet.

If high_salary() only exists on the Manager, then:

~~~python
Employee.objects.active().high_salary()
~~~

may fail.

Putting chainable filters on the QuerySet solves this.

---

# 24. as_manager()

~~~python
class Employee(models.Model):
    ...

    objects = (
        EmployeeQuerySet.as_manager()
    )
~~~

Django creates a Manager exposing appropriate custom QuerySet methods.

This is the simplest pattern when you mainly need chainable query methods.

---

# 25. Manager.from_queryset()

Sometimes you need both:

- custom QuerySet methods;
- custom Manager-only creation methods.

~~~python
class EmployeeManager(
    models.Manager.from_queryset(
        EmployeeQuerySet
    )
):
    def create_employee(
        self,
        name,
        salary,
    ):
        return self.create(
            name=name,
            salary=salary,
            active=True,
        )
~~~

Attach:

~~~python
class Employee(models.Model):
    ...

    objects = EmployeeManager()
~~~

Now all work:

~~~python
Employee.objects.create_employee(
    "John",
    120000,
)

Employee.objects.active()

Employee.objects.active().high_salary()
~~~

---

# 26. as_manager() vs from_queryset()

~~~text
Only custom QuerySet methods?
→ QuerySet.as_manager()

Need custom QuerySet methods
+
custom Manager-specific methods?
→ Manager.from_queryset()
~~~

---

# 27. Custom UserManager

Authentication user creation is a classic Manager use case.

~~~python
from django.contrib.auth.base_user import BaseUserManager

class UserManager(BaseUserManager):
    use_in_migrations = True

    def get_by_natural_key(self, email):
        return self.get(
            email=email.strip().lower()
        )

    def _create_user(
        self,
        email,
        password,
        **extra_fields,
    ):
        if not email:
            raise ValueError(
                "Email is required"
            )

        normalized_email = (
            email.strip().lower()
        )

        user = self.model(
            email=normalized_email,
            **extra_fields,
        )

        user.set_password(password)

        user.save(
            using=self._db
        )

        return user

    def create_user(
        self,
        email,
        password=None,
        **extra_fields,
    ):
        extra_fields.setdefault(
            "is_staff",
            False,
        )
        extra_fields.setdefault(
            "is_superuser",
            False,
        )

        return self._create_user(
            email,
            password,
            **extra_fields,
        )

    def create_superuser(
        self,
        email,
        password=None,
        **extra_fields,
    ):
        extra_fields.setdefault(
            "is_staff",
            True,
        )
        extra_fields.setdefault(
            "is_superuser",
            True,
        )

        if (
            extra_fields.get("is_staff")
            is not True
        ):
            raise ValueError(
                "Superuser must have "
                "is_staff=True"
            )

        if (
            extra_fields.get(
                "is_superuser"
            )
            is not True
        ):
            raise ValueError(
                "Superuser must have "
                "is_superuser=True"
            )

        return self._create_user(
            email,
            password,
            **extra_fields,
        )
~~~

Important:

~~~text
self.model
→ attached User model

self._db
→ selected database alias

set_password()
→ hash password

create_user/create_superuser
→ creation entry points
→ Manager responsibility fits well
~~~

---

# 28. Production soft-delete example

~~~python
class ProductQuerySet(models.QuerySet):
    def not_deleted(self):
        return self.filter(
            is_deleted=False
        )

    def active(self):
        return self.filter(
            is_active=True,
            is_deleted=False,
        )

    def deleted(self):
        return self.filter(
            is_deleted=True
        )
~~~

Usage:

~~~python
Product.objects.active()
Product.objects.deleted()
~~~

If the definition of active changes later, you modify one method instead of dozens of query locations.

---

# 29. Business vocabulary

Compare:

~~~python
Order.objects.filter(
    status="paid",
    refunded=False,
    cancelled=False,
)
~~~

with:

~~~python
Order.objects.completed()
~~~

The second exposes domain meaning.

Good method names:

~~~text
.active()
.pending()
.completed()
.available()
.overdue()
.expired()
.for_team(team)
.with_player()
~~~

Avoid vague names:

~~~text
.get_data()
.do_filter()
.process()
.fetch_stuff()
~~~

---

# 30. Your Squad QuerySet example

~~~python
class SquadQuerySet(models.QuerySet):
    def active(self):
        return self.filter(
            is_active=True
        )

    def for_season(self, season):
        return self.filter(
            season=season
        )

    def with_team(self):
        return self.select_related(
            "team"
        )
~~~

Attach:

~~~python
class Squad(models.Model):
    ...

    objects = (
        SquadQuerySet.as_manager()
    )
~~~

Usage:

~~~python
Squad.objects     .active()     .for_season("2026")     .with_team()
~~~

Reads almost like English.

---

# 31. SquadMembership QuerySet

~~~python
class SquadMembershipQuerySet(
    models.QuerySet
):
    def active(self):
        return self.filter(
            is_active=True
        )

    def captains(self):
        return self.filter(
            squad_role=SquadRole.CAPTAIN
        )

    def for_squad(self, squad):
        return self.filter(
            squad=squad
        )

    def with_player(self):
        return self.select_related(
            "player"
        )

    def with_squad(self):
        return self.select_related(
            "squad"
        )
~~~

Usage:

~~~python
SquadMembership.objects     .for_squad(squad)     .active()     .captains()     .with_player()
~~~

---

# 32. Custom methods can still use standard QuerySet operations

~~~python
Employee.objects     .active()     .values(
        "id",
        "name",
    )
~~~

~~~python
Employee.objects     .active()     .update(
        status="verified"
    )
~~~

~~~python
Employee.objects     .active()     .aggregate(...)
~~~

~~~python
Employee.objects     .active()     .delete()
~~~

Be careful: chainability makes destructive operations easy too.

---

# 33. Do not turn QuerySets into workflow/service layers

Good QuerySet responsibilities:

~~~text
filtering
ordering
annotations
eager loading
database expressions
bulk database selection
~~~

Bad fit:

~~~text
send emails
charge cards
call third-party APIs
publish Kafka events
run cross-service workflows
~~~

Those belong in services/background jobs.

---

# 34. Testing custom QuerySets

~~~python
@pytest.mark.django_db
def test_active_queryset():
    Employee.objects.create(
        name="A",
        active=True,
        deleted=False,
    )

    Employee.objects.create(
        name="B",
        active=False,
        deleted=False,
    )

    assert (
        Employee.objects
        .active()
        .count()
        == 1
    )
~~~

Custom QuerySets give business query rules one place to test.

---

# 35. Final mental model

~~~text
Reusable + chainable DB logic
→ Custom QuerySet

Model-level creation entry point
→ Manager

External workflow/business orchestration
→ Service layer / Celery / integration layer
~~~

Strong interview answer:

> A custom QuerySet is used to encapsulate reusable chainable ORM logic. Because each method returns another QuerySet, methods such as active(), high_salary(), and with_department() can be composed naturally. A Manager remains the model-level query entry point and is often a better place for creation helpers such as create_user().
