# Phase 05 — Core Class State & Behavior

## Goal

Decide what state and behavior belong inside the core domain objects instead of creating data-only classes or one giant service.

## Responsibility principle

```text
Entity
→ owns its own state and invariants

Value Object
→ represents meaningful immutable value

Domain Service
→ cross-object domain logic

Application Service
→ orchestrates a use case

Repository
→ persistence abstraction
```

## Match

Main responsibility:

```text
match lifecycle + match-level invariants
```

Possible state:

```text
id
format
status
venue
teams
toss
innings
result
```

Possible behavior:

```text
record_toss()
start()
start_next_innings()
complete()
abandon()
```

Important invariants:

- Cannot start before toss.
- Cannot record toss twice.
- Cannot complete before required innings finish.
- Cannot start another innings while one is active.
- Cannot modify a completed match.

Avoid direct mutation such as:

```python
match.status = MatchStatus.IN_PROGRESS
```

Prefer intent:

```python
match.start()
```

## Innings

Main responsibility:

```text
current scoring state + innings-level invariants
```

Possible state:

```text
id
batting_team
bowling_team
status
score
current_striker
current_non_striker
current_bowler
current_over
overs
wickets
```

Possible behavior:

```text
record_delivery()
rotate_strike()
start_new_over()
record_wicket()
complete()
```

Important invariants:

- Cannot record after completion.
- Cannot lose more than 10 wickets.
- Striker and non-striker must differ.
- Batters must belong to batting side.
- Bowler must belong to bowling side.
- Only one over can be active.

## Over

Main responsibility:

```text
over progression + legal-ball counting
```

Possible state:

```text
number
bowler
deliveries
legal_ball_count
status
```

Possible behavior:

```text
add_delivery()
is_complete()
complete()
```

Key rule:

```text
An over completes after 6 legal balls,
not necessarily after 6 delivery events.
```

A wide/no-ball may add a delivery event without increasing the legal-ball count.

## Delivery

A delivery represents one recorded ball event.

Possible state:

```text
sequence
striker
non_striker
bowler
result
```

Useful behavior:

```text
is_legal()
total_runs()
is_wicket()
```

A delivery should be treated as effectively immutable during normal scoring because it is historical event data.

## DeliveryResult

Value-oriented object that represents the outcome of a delivery.

Possible state:

```text
batter_runs
extras
wicket
is_legal
```

Possible behavior:

```text
total_runs()
is_wicket()
```

## Extras

Value Object representing extra runs.

Possible fields:

```text
wides
no_balls
byes
leg_byes
penalty
```

Possible behavior:

```text
total()
```

## ScoringEngine

Use a domain service when a scoring rule affects multiple objects and has no clean single owner.

Example:

```text
No-ball + 4 batter runs
```

may affect:

```text
team score
batter score
bowler conceded runs
legal-ball count
strike
over state
```

So a useful flow is:

```text
Delivery
   ↓
ScoringEngine
   ↓
ScoringImpact
   ↓
Innings applies impact
```

## Record-delivery application flow

```text
API / Controller
      ↓
RecordDeliveryUseCase
      ↓
load Match
      ↓
validate match/innings state
      ↓
build DeliveryResult
      ↓
build Delivery
      ↓
ScoringEngine calculates impact
      ↓
Innings applies changes
      ↓
Over records delivery
      ↓
Repository saves
```

## Application Service vs Domain Behavior

Application service:

```text
load
orchestrate
call domain
save
```

Entity/domain:

```text
protect business state
protect invariants
perform domain actions
```

Example:

```python
class RecordDeliveryUseCase:
    def execute(self, command):
        match = repo.get(command.match_id)
        match.record_delivery(...)
        repo.save(match)
```

## Validation layers

### Input validation

Examples:

```text
batter_runs must be an integer
required request fields
```

Belongs near API/controller/serializer.

### Domain validation

Examples:

```text
cannot record delivery after innings ends
cannot start match before toss
```

Belongs in domain entities/services.

### Persistence validation

Examples:

```text
unique constraints
foreign keys
database integrity
```

Belongs at persistence/database level.

## Avoid God Objects

Bad:

```text
Match handles:
scoring
stats
websockets
persistence
notifications
commentary
everything
```

Also bad:

```text
CricketService contains every business rule
while entities contain only fields.
```

Prefer responsibility placement based on ownership.

## Core responsibility table

| Class | Main responsibility |
|---|---|
| Match | Match lifecycle and match-level rules |
| Innings | Active scoring state and innings invariants |
| Over | Over progression and legal-ball count |
| Delivery | Immutable record of one ball event |
| DeliveryResult | Outcome value of a delivery |
| Extras | Extra-runs value and calculations |
| ScoringEngine | Cross-object cricket scoring calculation |
| RecordDeliveryUseCase | Orchestrate loading, domain call, persistence |

## Current conceptual flow

```text
Controller
   ↓
Application Service
   ↓
Match
   ↓
Innings
   ↓
ScoringEngine
   ↓
Over
   ↓
Delivery
```

Persistence remains separate:

```text
Application Service
   ↓
Repository
   ↓
Database
```

## Key lesson

Do not ask only:

> What fields does this class have?

Ask:

> What state does this object own, what invariants must it protect, and what business actions naturally belong to it?
