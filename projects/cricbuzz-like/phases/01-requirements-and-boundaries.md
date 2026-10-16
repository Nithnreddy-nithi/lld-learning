# Phase 01 — Requirements & System Boundaries

## Goal

Turn the vague prompt **“Design Cricbuzz”** into a precise LLD scope before creating classes.

## Actors

```text
Viewer
Scorer / Admin
```

### Viewer use cases

- View live matches
- View current score
- View scorecard
- View commentary
- View player statistics
- View schedules/results

### Scorer/Admin use cases

- Create match
- Configure teams and Playing XI
- Record toss
- Start match
- Start innings
- Record each delivery
- Record wickets/extras
- End innings
- Complete match

## Functional requirements

- Manage players and teams
- Create matches
- Select squads and Playing XI
- Record toss
- Support T20, ODI, Test
- Record deliveries
- Handle runs, wides, no-balls, byes, leg-byes and wickets
- Track overs, strike and innings
- Calculate batter/bowler/fielding stats
- Maintain partnerships
- Produce live scorecard and commentary
- Calculate match result

## Non-functional requirements

- Correct scoring
- Consistency
- Extensibility for new cricket formats/rules
- Maintainability
- Concurrency safety
- Low-latency live reads
- Testability

## System boundary

### In scope

```text
Match management
Scoring engine
Scorecard
Statistics
Commentary
Live-score updates
```

### Initially out of scope

```text
News
Ads
Fantasy cricket
Video streaming
Payments
Social features
Betting
AI predictions
Complex DLS implementation
```

## Match lifecycle

```text
SCHEDULED
    ↓
TOSS_COMPLETED
    ↓
IN_PROGRESS
    ↓
COMPLETED

Possible side paths:
DELAYED / ABANDONED / CANCELLED
```

## Core business invariants

- A completed match cannot accept another delivery.
- An innings cannot start before the match starts.
- An over completes after 6 legal deliveries.
- Wide and no-ball do not count as legal deliveries.
- A team cannot lose more than 10 wickets.
- Players involved in scoring must belong to the match selection.
- Only the valid active innings may receive a delivery.

## Key lesson

Do **not** begin with classes. Start with:

```text
Vague problem
  ↓
Actors
  ↓
Use cases
  ↓
Functional requirements
  ↓
Non-functional requirements
  ↓
System boundary
  ↓
Business invariants
  ↓
Object modelling
```
