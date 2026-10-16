# Phase 02 — Actors, Use Cases & Candidate Domain Objects

## Goal

Move from requirements to candidate domain objects without blindly turning every noun into a class.

## Use-case-first discovery

Example use case:

```text
Record Delivery
```

Ask:

```text
Who performs it?
What data is required?
What objects participate?
What state changes?
```

Candidate concepts:

```text
Match
Innings
Player
Delivery
Extras
Wicket
```

## Noun extraction is only a starting point

Requirement:

> A scorer records each delivery in an innings. A delivery contains striker, non-striker, bowler, runs, extras and optional wicket information.

Possible nouns:

```text
Scorer
Delivery
Innings
Striker
Non-striker
Bowler
Runs
Extras
Wicket
```

But `Striker`, `Non-striker`, and `Bowler` are usually **roles played by Player**, not separate identity classes.

```text
Delivery
  striker      -> Player
  non_striker  -> Player
  bowler       -> Player
```

## Candidate object list

```text
Player
Team
Venue
Series
Match
MatchSquad
PlayingXI
Toss
Innings
Over
Delivery
DeliveryResult
Extras
WicketInfo
Partnership
Scorecard
Commentary
MatchResult
```

These are candidates, not final decisions.

## Ownership discovery

```text
Match
  └── Innings
       └── Over
            └── Delivery
```

This indicates strong lifecycle ownership.

By contrast:

```text
Match ---- Venue
```

Venue exists independently, so Match does not own its lifecycle.

## Rich domain vs anemic model

Bad direction:

```text
Entities contain only data.
One giant CricketService contains every rule.
```

Better direction:

```text
Entities protect their own state and invariants.
Domain services handle domain behavior with no natural single owner.
```

Example:

```text
innings.record_delivery(...)
```

can enforce:

```text
Cannot record after innings completion.
```

## Candidate object graph

```text
Series
  |
  └── Match
       ├── Venue
       ├── Team A
       ├── Team B
       ├── MatchSquad
       ├── Toss
       └── Innings
            ├── BattingTeam
            ├── BowlingTeam
            └── Over
                 └── Delivery
                      ├── striker
                      ├── non_striker
                      ├── bowler
                      ├── DeliveryResult
                      └── WicketInfo
```

## Six questions for every object

1. What identity does it have?
2. What data does it own?
3. What behavior does it own?
4. Who owns its lifecycle?
5. What rules must it protect?
6. Who is allowed to change it?
