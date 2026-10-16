# Phase 03 — Entity, Value Object, Enum & Domain Service

## Core classification

```text
Entity
Value Object
Enum
Domain Service
```

## Entity

An entity is primarily defined by identity.

Two objects can have identical attributes and still be different entities.

Examples:

```text
Player
Team
Venue
Series
Match
Innings
Over
Delivery
```

Entity mental model:

```text
identity + lifecycle + mutable state + behavior
```

## Value Object

A value object is defined by its values, not identity.

Examples:

```text
Score(150, 4)
Extras(...)
DeliveryResult(...)
WicketInfo(...)
MatchResult(...)
OverProgress(...)
CountryCode("IN")
```

Typical characteristics:

- Equality by value
- Usually immutable
- Can contain validation and behavior
- Does not need meaningful domain identity

### Important persistence distinction

A value object **can absolutely be stored in a database**.

Domain:

```text
Innings
  └── Score(150, 4)
```

Database:

```text
innings
----------------
id
runs
wickets
```

The value object does not require its own business identity or separate table.

## Enum

Use for a small closed set of choices.

Examples:

```text
MatchFormat
  TEST
  ODI
  T20

WicketKind
  BOWLED
  CAUGHT
  LBW
  RUN_OUT
  STUMPED
```

## Domain Service

Use when:

1. Behavior belongs to the business domain.
2. It does not naturally belong to one entity.
3. It may coordinate multiple domain objects.

Examples:

```text
ScoringEngine
MatchResultCalculator
NetRunRateCalculator
```

Do not create a service just to move logic out of an entity.

## Classification table

| Concept | Type |
|---|---|
| Player | Entity |
| Team | Entity |
| Venue | Entity |
| Series | Entity |
| Match | Entity |
| Innings | Entity |
| Over | Entity |
| Delivery | Entity |
| PlayingXI | Match-owned object/value |
| Toss | Value Object |
| Score | Value Object |
| Extras | Value Object |
| DeliveryResult | Value Object |
| WicketInfo | Value Object |
| MatchResult | Value Object |
| OverProgress | Value Object |
| CountryCode | Value Object |
| MatchFormat | Enum |
| MatchStatus | Enum / later State |
| InningsStatus | Enum |
| WicketKind | Enum |
| ScoringEngine | Domain Service |
| MatchResultCalculator | Domain Service |

## Decision tree

```text
Does unique identity matter?
        |
       YES
        ↓
      Entity

Otherwise, is it defined by value and owns validation/behavior?
        |
       YES
        ↓
   Value Object

Is it a fixed closed choice?
        |
       YES
        ↓
       Enum

Is it domain behavior with no natural single owner?
        |
       YES
        ↓
 Domain Service
```
