# Phase 04 — Relationships, Ownership, Composition & Cardinality

## Goal

Decide how domain objects relate, who owns lifecycle, and whether a relationship deserves its own object.

## Association

Objects know/use each other, but neither necessarily owns the other's lifecycle.

```text
Match ---- Venue
Delivery ---- Player
```

A venue or player still exists when the match/delivery disappears.

## Aggregation

A parent groups objects that can independently exist.

```text
Team ◇── Player
```

Use carefully because context often matters more than a simple Team → Player relationship.

## Composition

Strong lifecycle ownership.

```text
Match
  ◆── Innings
        ◆── Over
              ◆── Delivery
```

The child is meaningful primarily inside its parent context.

## Ownership test

Ask:

> If the parent disappears, does the child still make sense independently?

Examples:

```text
Match deleted → its Innings do not meaningfully stand alone.
Match deleted → Venue still exists.
```

## Cardinality

```text
1       exactly one
0..1    zero or one
1..*    one or more
0..*    zero or more
```

Important relationships:

```text
Venue 1 -------- N Match
Match 1 -------- 1..* Innings
Innings 1 ------ 0..* Over
Over 1 --------- 1..* Delivery
Match 1 -------- 0..1 Toss
Match 1 -------- 0..1 MatchResult
```

An over has **6 legal balls**, not necessarily 6 delivery events, because wides/no-balls can add extra delivery events.

## Relationship object: MatchTeam

A direct Match ↔ Team many-to-many loses match-specific information.

The relationship itself has data:

```text
captain
wicketkeeper
squad
playing XI
```

So promote the relationship into an object:

```text
Match
  |
  +---- MatchTeam ---- Team
           |
           +---- Squad
           +---- PlayingXI
```

General rule:

> When a relationship has important attributes or behavior, model the relationship as an object.

Other examples:

```text
Student + Course → Enrollment
User + Project → ProjectMembership
Product + Order → OrderItem
```

## Context-specific entities

Global concept:

```text
Player
```

Match-specific concept may be:

```text
MatchPlayer / SquadPlayer
```

This allows context-specific properties such as:

```text
selected
captain
wicketkeeper
team
```

## Aggregate-root idea

The outside world should not freely mutate deep internal state.

Bad:

```text
delivery.result = changed_result
```

because many dependent values could become inconsistent.

Prefer controlled entry points such as:

```text
innings.record_delivery(...)
```

or later, depending on aggregate boundaries:

```text
match.record_delivery(...)
```

## Current relationship picture

```text
Series
  |
  v
Match ---------------- Venue
  |
  +------ Toss
  +------ MatchResult
  |
  +------ MatchTeam ------ Team
  |         |
  |         +------ Squad
  |         +------ PlayingXI ------ Player
  |
  +------ Innings
            |
            +------ batting MatchTeam
            +------ bowling MatchTeam
            |
            +------ Over
                      |
                      +------ bowler: Player
                      |
                      +------ Delivery
                              |
                              +------ striker: Player
                              +------ non_striker: Player
                              +------ bowler: Player
                              |
                              +------ DeliveryResult
                                      |
                                      +------ Extras
                                      +------ WicketInfo
```

## Relationship checklist

For every relationship ask:

1. How many?
2. Who owns lifecycle?
3. Can the child exist independently?
4. Does the relationship itself have meaning?
5. Does the relationship have data?
6. Is a reverse reference actually necessary?
7. Who is allowed to modify it?
