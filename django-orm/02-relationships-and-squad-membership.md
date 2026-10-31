# Relationships and SquadMembership

## Relationship types

Django's main relationship fields are:

- `ForeignKey` — many-to-one.
- `OneToOneField` — one-to-one.
- `ManyToManyField` — many-to-many.

## ForeignKey

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

The database stores `department_id` on the Employee table.

Forward:

```python
employee.department
employee.department_id
```

Reverse:

```python
department.employees.all()
```

Without `related_name="employees"`, the default reverse object accessor is typically `employee_set`.

## Reverse relationships

A relation defined on A pointing to B gives:

```text
A → B = forward
B → A = reverse
```

Example:

```python
Department.objects.filter(
    employees__name="John"
)
```

Reverse relations that return many objects use a related manager, so you can call:

```python
department.employees.all()
department.employees.filter(...)
department.employees.count()
department.employees.exists()
department.employees.order_by(...)
```

Reverse multi-valued joins may duplicate parent rows; `.distinct()` can be necessary.

## One-to-one

```python
class Profile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
    )
```

Forward:

```python
profile.user
```

Reverse:

```python
user.profile
```

Both sides are single-valued.

## Many-to-many

```python
class Student(models.Model):
    courses = models.ManyToManyField(
        Course,
        related_name="students",
    )
```

Django creates a junction table containing the two foreign keys.

```python
student.courses.all()
course.students.all()
```

Both directions are multi-valued.

---

# Squad, Team, Player, SquadMembership

Your relationship structure is:

```text
Team
  ↓ one-to-many
Squad
  ↓ many-to-many through SquadMembership
Player
```

More explicitly:

```text
Team
  ↑
  │ Squad.team FK
Squad
  ↓
SquadMembership
  ↓
Player
```

A Team can have many Squads:

```python
squad.team
team.squads.all()
```

A Squad can contain many Players, and a Player can belong to many Squads:

```python
squad.players.all()
player.squads.all()
```

## Why SquadMembership exists

If the only requirement were:

> A Squad has many Players.

then this could be enough:

```python
players = models.ManyToManyField(
    Player,
    related_name="squads",
)
```

Django would create a hidden table roughly like:

```text
squad_id | player_id
---------|----------
10       | 100
10       | 101
10       | 102
```

But your relationship itself has extra data:

```text
squad_role
jersey_number
joined_on
left_on
is_active
created_at
updated_at
```

Those values do not belong to Player globally and do not belong to Squad globally. They belong to:

```text
this Player's membership in this particular Squad
```

Therefore the explicit through model is justified:

```python
class SquadMembership(models.Model):
    squad = models.ForeignKey(
        Squad,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    player = models.ForeignKey(
        Player,
        on_delete=models.PROTECT,
        related_name="squad_memberships",
    )
    squad_role = models.CharField(...)
    jersey_number = models.PositiveSmallIntegerField(...)
    joined_on = models.DateField(...)
    left_on = models.DateField(...)
    is_active = models.BooleanField(default=True)
```

## Physical database idea

```text
Team
id | name

Squad
id | name | team_id

Player
id | full_name

SquadMembership
id | squad_id | player_id | role | jersey | active
```

Example:

```text
squad_id | player_id | role       | jersey
---------|-----------|------------|-------
10       | 100       | player     | 18
10       | 101       | captain    | 45
11       | 100       | player     | 18
```

Player 100 appears in Squad 10 and Squad 11 through two different membership rows.

## Why keep Squad.players if SquadMembership already exists?

```python
players = models.ManyToManyField(
    Player,
    through="SquadMembership",
    related_name="squads",
)
```

This does not create another relationship table. It tells Django:

> Use SquadMembership as the join table for the Squad ↔ Player many-to-many relation.

It provides the convenient API:

```python
squad.players.all()
```

instead of manually writing a Player filter through memberships.

Use:

```python
squad.players.all()
```

when you need Player objects.

Use:

```python
squad.memberships.all()
```

when you need relationship metadata such as role, jersey, joined date, or active status.

Example:

```python
for membership in squad.memberships.select_related("player"):
    print(
        membership.player.full_name,
        membership.squad_role,
        membership.jersey_number,
    )
```

## Unique membership

A constraint like:

```python
models.UniqueConstraint(
    fields=("squad", "player"),
    name="squads_unique_player_membership",
)
```

prevents duplicate membership rows for the same player in the same squad, while still allowing the same player in a different squad.

## on_delete

Typical meanings:

- `CASCADE` — delete dependent rows.
- `PROTECT` — block parent deletion while referenced.
- `RESTRICT` — restrict deletion according to DB relationship rules.
- `SET_NULL` — set FK to NULL; requires `null=True`.
- `SET_DEFAULT` — set FK to its default.
- `DO_NOTHING` — Django does not perform automatic action.

In your model:

- deleting a Squad can cascade to its memberships;
- deleting a Player can be protected while memberships reference it.
