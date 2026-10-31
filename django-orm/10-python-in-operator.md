# Python `in` Membership Operator

Python's `in` operator checks membership:

```text
"Does this value exist inside this collection?"
```

## Lists

```python
nums = [10, 20, 30]

20 in nums   # True
50 in nums   # False
```

## Strings

```python
"py" in "python"   # True
"x" in "python"    # False
```

For strings, membership can mean substring containment.

## Dictionaries

For dictionaries, `in` checks keys:

```python
user = {
    "name": "Nithin",
    "age": 25,
}

"name" in user      # True
"Nithin" in user    # False
```

To check values:

```python
"Nithin" in user.values()  # True
```

## Sets

```python
5 in {1, 5, 10}  # True
```

Set membership is commonly used when fast membership checks are needed.

## not in

```python
5 not in [1, 2, 3]  # True
```

## Django __in lookup

Python:

```python
2 in [1, 2, 3]
```

checks Python-side membership.

Django:

```python
Employee.objects.filter(
    id__in=[1, 2, 3]
)
```

uses the ORM `__in` lookup and maps conceptually to SQL:

```sql
WHERE id IN (1, 2, 3)
```

They are different features, but the membership idea is similar.
