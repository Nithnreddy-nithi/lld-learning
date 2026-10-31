# Managers and Custom QuerySets

## Manager mental model

```python
Employee.objects
```

`objects` is normally a Django `Manager`.

Think:

```text
Model
  ↓
Manager
  ↓
QuerySet
  ↓
Database
```

A Manager is the model-level query entry point. A QuerySet is the chainable representation of a collection query.

## Custom Manager

```python
class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(active=True)
```

Attach it:

```python
class Employee(models.Model):
    objects = models.Manager()
    active_objects = ActiveManager()
```

Now:

```python
Employee.objects.all()          # all employees
Employee.active_objects.all()   # only active employees
```

`get_queryset()` changes the baseline QuerySet produced by that manager.

Be careful with managers that permanently hide rows, especially when Django internals or admin code need the full data set.

## Manager vs QuerySet methods

Core rule:

```text
Manager = starts the query
QuerySet = continues the query
```

If a method should be reusable and chainable, it normally belongs on a custom QuerySet.

```python
class EmployeeQuerySet(models.QuerySet):
    def active(self):
        return self.filter(active=True)

    def high_salary(self):
        return self.filter(salary__gt=100000)
```

Attach:

```python
class Employee(models.Model):
    objects = EmployeeQuerySet.as_manager()
```

Usage:

```python
Employee.objects.active().high_salary()
```

Flow:

```text
Employee.objects
    ↓ Manager
.active()
    ↓ EmployeeQuerySet
.high_salary()
    ↓ EmployeeQuerySet
```

The methods chain because each method returns another QuerySet.

## Why not put every filter method on the Manager?

If `active()` is only a Manager method and returns an ordinary QuerySet, then:

```python
Employee.objects.active().high_salary()
```

can fail if `high_salary()` exists only on the Manager.

Custom QuerySet methods solve this by remaining available after each chaining step.

## Parameterized QuerySet methods

```python
class EmployeeQuerySet(models.QuerySet):
    def active(self):
        return self.filter(active=True, deleted=False)

    def min_salary(self, amount):
        return self.filter(salary__gte=amount)

    def in_department(self, department):
        return self.filter(department=department)

    def with_department(self):
        return self.select_related("department")
```

Usage:

```python
Employee.objects     .active()     .min_salary(75000)     .in_department(department)     .with_department()
```

Because QuerySets are lazy, this normally composes one final SQL query rather than executing one query per method.

## Reusing custom QuerySet methods

```python
class EmployeeQuerySet(models.QuerySet):
    def not_deleted(self):
        return self.filter(deleted=False)

    def active(self):
        return self.not_deleted().filter(active=True)
```

This centralizes business definitions such as “active”.

## as_manager() vs Manager.from_queryset()

Use:

```python
EmployeeQuerySet.as_manager()
```

when you mainly need custom QuerySet methods.

If you also need Manager-specific creation methods:

```python
class EmployeeManager(
    models.Manager.from_queryset(EmployeeQuerySet)
):
    def create_employee(self, name, salary):
        return self.create(
            name=name,
            salary=salary,
            active=True,
        )
```

Then:

```python
Employee.objects.create_employee(...)
Employee.objects.active().high_salary()
```

## Custom UserManager example

A custom authentication manager often contains creation entry points because creation is not a chainable collection filter.

```python
from django.contrib.auth.base_user import BaseUserManager

class UserManager(BaseUserManager):
    use_in_migrations = True

    def get_by_natural_key(self, email):
        return self.get(email=email.strip().lower())

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("An email address is required.")

        normalized_email = email.strip().lower()
        user = self.model(
            email=normalized_email,
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(
            email,
            password,
            **extra_fields,
        )

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("A superuser must have is_staff=True.")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("A superuser must have is_superuser=True.")

        return self._create_user(
            email,
            password,
            **extra_fields,
        )
```

Important points:

- `self.model` is the model attached to the manager.
- `self._db` is the selected database alias.
- `set_password()` hashes the password.
- `setdefault()` only supplies a value when the caller did not provide one.
- `create_user()` / `create_superuser()` fit Manager semantics because they are creation entry points.

## Production guideline

Put reusable database-set logic in QuerySets:

```text
.active()
.paid()
.available()
.for_team(team)
.with_player()
.with_department()
```

Put non-chainable creation entry points on Managers:

```text
.create_user()
.create_superuser()
.create_employee()
```

Keep external workflows such as emails, payment APIs, Kafka publishing, etc. in service/background layers rather than turning the QuerySet into a general business-service class.
