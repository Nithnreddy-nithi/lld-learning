# Phase 11 — Over + Delivery Modelling in Depth

## Goal

Model Over and Delivery correctly so the scoring system can represent legal balls, wides, no-balls, wickets, delivery sequence, and over completion without fragile shortcuts.

---

## 1. Why Delivery is an Entity

A Delivery is an event that happened at a specific point in the innings.

These two deliveries may have identical values:

```text
0 runs
same striker
same bowler
```

but they are still different events:

```text
12.1
12.2
```

So identity/history matters.

That makes Delivery entity-like.

---

## 2. Why Over is also useful as an Entity

An Over has:

```text
identity within innings
current bowler
delivery history
legal-ball count
completion state
```

It also protects an important invariant:

```text
an over completes after 6 legal deliveries
```

not after 6 raw delivery events.

---

## 3. Core Over state

A practical model:

```text
Over
----
number
bowler
deliveries
legal_ball_count
status
```

Example:

```text
Over 12
Bowler: Starc
Legal balls: 4
Delivery events: 6
Status: ACTIVE
```

Possible because wides/no-balls create additional delivery events.

---

## 4. Core Delivery state

A Delivery can contain:

```text
sequence
striker
non_striker
bowler
result
```

Where result contains:

```text
batter_runs
extras
wicket
is_legal
```

Conceptually:

```text
Delivery
   |
   +-- striker -> Player
   +-- non_striker -> Player
   +-- bowler -> Player
   |
   +-- DeliveryResult
          |
          +-- batter_runs
          +-- Extras
          +-- WicketInfo
          +-- is_legal
```

---

## 5. DeliveryResult as a Value Object

The event itself has identity.

The outcome does not need separate identity.

So:

```text
Delivery
→ Entity

DeliveryResult
→ Value Object
```

Example:

```python
@dataclass(frozen=True)
class DeliveryResult:
    batter_runs: int
    extras: Extras
    wicket: WicketInfo | None
    is_legal: bool
```

---

## 6. Extras model

Avoid:

```python
extras = 3
```

because 3 wides and 3 byes have different effects.

Better:

```python
@dataclass(frozen=True)
class Extras:
    wides: int = 0
    no_balls: int = 0
    byes: int = 0
    leg_byes: int = 0
    penalty: int = 0

    def total(self):
        return (
            self.wides
            + self.no_balls
            + self.byes
            + self.leg_byes
            + self.penalty
        )
```

---

## 7. Legal vs illegal delivery

A legal delivery counts toward the six legal balls in an over.

A wide or no-ball does not.

So:

```text
wide
→ delivery event recorded
→ legal_ball_count unchanged

no-ball
→ delivery event recorded
→ legal_ball_count unchanged

normal ball
→ delivery event recorded
→ legal_ball_count +1
```

This distinction is essential.

---

## 8. Example over with extras

Suppose:

```text
12.1 normal
12.2 normal
12.3 wide
12.3 normal
12.4 no-ball
12.4 normal
12.5 normal
12.6 normal
```

There are:

```text
8 delivery events
6 legal balls
```

The over completes only after the final legal ball.

---

## 9. Delivery numbering is not a decimal

Do not store:

```python
delivery_number = 12.3
```

as a float.

Why?

Because cricket notation is not decimal arithmetic.

After:

```text
12.5
```

comes:

```text
13.0
```

after the sixth legal ball.

And wides/no-balls can create repeated visible ball labels.

Better model:

```text
over_number
legal_ball_index
event_sequence
```

For example:

```python
@dataclass(frozen=True)
class DeliveryPosition:
    over_number: int
    legal_ball_number: int
    event_sequence: int
```

---

## 10. Why event_sequence helps

Consider:

```text
12.3 wide
12.3 no-ball
12.3 normal
```

The visible legal-ball number may remain 3 until a legal ball completes.

So you need another field to uniquely order events.

Example:

```text
event_sequence:
1
2
3
```

within that point in the over, or simply a monotonic innings delivery sequence.

---

## 11. Recommended identity

A Delivery may have a database ID:

```text
delivery_id
```

and domain position:

```text
over_number
legal_ball_number
event_sequence
```

Do not rely only on human-readable cricket notation for identity.

---

## 12. Over.add_delivery()

A core method:

```python
class Over:

    def add_delivery(self, delivery):

        if self.is_complete():
            raise InvalidOperation(
                "Over already completed"
            )

        if delivery.bowler != self.bowler:
            raise InvalidBowler()

        self.deliveries.append(delivery)

        if delivery.is_legal():
            self.legal_ball_count += 1
```

This keeps over progression inside Over.

---

## 13. Over.is_complete()

```python
def is_complete(self):
    return self.legal_ball_count == 6
```

Later, if special competition rules differ, this value can come from rules/configuration instead of hard-coded 6.

For standard cricket, 6 is a valid starting point.

---

## 14. Delivery behavior

Useful methods:

```python
class Delivery:

    def is_legal(self):
        return self.result.is_legal

    def total_runs(self):
        return (
            self.result.batter_runs
            + self.result.extras.total()
        )

    def is_wicket(self):
        return self.result.wicket is not None
```

This behavior belongs naturally with the delivery event.

---

## 15. Who decides is_legal?

Do not let arbitrary callers decide:

```python
is_legal=True
```

without validation.

The legality should be derived from the result/rules.

Typical idea:

```text
wide > 0
→ illegal

no_ball > 0
→ illegal

otherwise
→ legal
```

So a stronger design may derive it:

```python
@property
def is_legal(self):
    return (
        self.extras.wides == 0
        and self.extras.no_balls == 0
    )
```

This prevents inconsistent states such as:

```text
no_ball = 1
is_legal = True
```

---

## 16. Make invalid states hard to represent

This is a key LLD principle.

Bad:

```python
DeliveryResult(
    extras=Extras(no_balls=1),
    is_legal=True,
)
```

Better:

derive legality from Extras.

So:

```text
one source of truth
```

instead of two fields that can disagree.

---

## 17. Wicket modelling

A wicket can carry:

```text
kind
dismissed_player
fielder
credited_to_bowler
```

Example:

```python
@dataclass(frozen=True)
class WicketInfo:
    kind: WicketKind
    dismissed_player: Player
    fielder: Player | None = None
```

The scoring engine can decide whether the bowler receives wicket credit.

For example:

```text
bowled
caught
lbw
→ bowler credited

run out
→ bowler not credited
```

---

## 18. Delivery creation should validate participants

Before recording:

```text
striker must equal current innings striker
non-striker must equal current non-striker
bowler must equal current over bowler
players must belong to Playing XI
```

This prevents callers from recording impossible ball events.

---

## 19. Who creates Delivery?

A good flow:

```text
RecordDeliveryCommand
      ↓
RecordDeliveryUseCase
      ↓
validate IDs / load players
      ↓
construct DeliveryResult
      ↓
construct Delivery
      ↓
Innings.record_delivery(delivery)
```

The controller should not manipulate Over directly.

---

## 20. Current Over flow

```text
Innings
   |
   v
current_over
   |
   +-- add_delivery(delivery)
           |
           +-- append event
           +-- increment legal ball if legal
           +-- complete at 6 legal balls
```

---

## 21. End-of-over strike change

A completed over usually swaps ends:

```text
striker ↔ non-striker
```

But do not make Over change Innings batters directly.

Why?

Because Over should not own Innings batting state.

Better:

```text
Over reports:
is_complete = true

Innings reacts:
rotate_strike()
```

This keeps ownership clear.

---

## 22. Avoid circular ownership

Bad:

```text
Innings owns Over
Over mutates Innings
Innings mutates Over
```

That creates tight coupling.

Better:

```text
Innings owns Over

Over protects over-level state

Innings coordinates higher-level reaction
```

---

## 23. Corrections and edits

Real scoring systems need corrections.

Example:

```text
12.3 recorded as 4
later corrected to 6
```

Do not casually allow:

```python
delivery.result = new_result
```

because score, stats, partnership, and bowler figures may already depend on the original result.

Corrections need a controlled workflow.

---

## 24. Correction strategies

Possible approaches:

### Recalculate from delivery history

```text
correct delivery
      ↓
replay innings events
      ↓
rebuild score/stats
```

Very consistent, but potentially more expensive.

### Compensating event

```text
DeliveryCorrectedEvent
```

Useful in event-driven systems.

### Controlled update + projection rebuild

Common practical approach.

The important lesson:

> Delivery is historical source data, so correction must update dependent projections consistently.

---

## 25. Delivery as source of truth

A scoring system may treat delivery history as authoritative:

```text
Deliveries
   ↓
Score
Batter stats
Bowler stats
Partnership
Commentary
```

This allows projections to be rebuilt.

It is much safer than treating every aggregate field as independent truth.

---

## 26. Over status

Possible enum:

```python
class OverStatus(Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
```

But if completion can be derived from legal_ball_count, explicit status may be redundant.

Ask:

> Is status independent state, or can it be derived?

Avoid storing duplicate state unless useful.

---

## 27. Bowler change invariant

A new over may use a different bowler.

In standard cricket, the same bowler cannot bowl consecutive overs.

This rule belongs above a single Over because it requires knowledge of the previous over.

So:

```text
Over
→ knows its own bowler

Innings / bowling policy
→ validates next-over bowler
```

Good ownership distinction.

---

## 28. Maiden over

A maiden depends on runs conceded by bowler during the over.

This can be derived from deliveries.

So avoid storing:

```python
is_maiden = True
```

as independent truth unless needed for performance.

Prefer:

```python
def is_maiden(self):
    return ...
```

based on delivery results.

---

## 29. Core responsibility split

```text
Delivery
→ one event and its outcome

DeliveryResult
→ immutable value describing outcome

Extras
→ extra-run breakdown

WicketInfo
→ dismissal details

Over
→ delivery collection + legal-ball progression

Innings
→ higher-level batting context and over transitions

ScoringEngine
→ calculates scoring/statistical effects
```

---

## 30. Current object picture

```text
Innings
   |
   +-- current_over
         |
         +-- bowler
         +-- legal_ball_count
         |
         +-- Delivery
               |
               +-- striker
               +-- non_striker
               +-- bowler
               |
               +-- DeliveryResult
                     |
                     +-- batter_runs
                     +-- Extras
                     +-- WicketInfo
```

---

## 31. Interview explanation

A strong explanation:

> I would model Delivery as an immutable historical event and Over as the owner of over-level progression. Over counts legal deliveries rather than raw delivery events, because wides and no-balls add events without consuming a legal ball. I would keep end-of-over batting changes in Innings, since Over should not mutate higher-level innings state.

---

## Key takeaway

```text
Delivery events != legal balls
```

and:

```text
Over owns legal-ball progression

Innings owns batting context

Delivery history is the strongest source of truth
```
