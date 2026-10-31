# Django ORM Learning Notes

These notes collect the Django ORM material covered in the learning thread, with practical SQL translations, performance notes, memory behavior, and cricket/Squad examples.

## Contents

1. [Managers and Custom QuerySets](./01-managers-and-custom-querysets.md)
2. [Relationships and SquadMembership](./02-relationships-and-squad-membership.md)
3. [CRUD Operations](./03-crud-operations.md)
4. [JOINs and Relationship Traversal](./04-joins-and-traversal.md)
5. [select_related()](./05-select-related.md)
6. [prefetch_related()](./06-prefetch-related.md)
7. [only(), defer(), values(), values_list()](./07-loading-required-fields.md)
8. [aggregate() and annotate()](./08-aggregate-and-annotate.md)
9. [select_for_update() and Concurrency](./09-select-for-update.md)
10. [Python `in` Membership Operator](./10-python-in-operator.md)

## Core ORM mental model

- **Manager** starts a model query: `Employee.objects`
- **QuerySet** represents and composes a collection query.
- QuerySets are generally **lazy** until evaluated.
- Forward `ForeignKey` / `OneToOne` access returns one object.
- Reverse `ForeignKey` / `ManyToMany` access returns a collection.
- `select_related()` eagerly loads single-valued relations using SQL JOINs.
- `prefetch_related()` eagerly loads multi-valued relations using separate queries and Python-side matching.
- `annotate()` asks the database for a calculated value per object/group.
- `aggregate()` asks the database for an overall summary and returns a dictionary.
- `select_for_update()` locks selected rows inside a transaction for concurrency-sensitive workflows.

Always ask:

1. What model/table am I starting from?
2. What relationships am I traversing?
3. Does each hop return one object or many?
4. What SQL will Django likely generate?
5. Am I loading full objects when I only need a calculation or a few columns?
6. Could this create N+1 queries?
7. Could concurrent requests race on the same rows?
