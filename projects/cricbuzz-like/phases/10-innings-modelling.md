# Phase 10 — Innings Modelling in Depth

## Goal

Model Innings as a rich domain entity that owns the current batting context, scoring state, over progression, and innings-level invariants.

The central question is:

> What should Innings know and protect, and what should remain outside it?

---

## 1. Why Innings is an Entity

An innings has:

```text
identity
lifecycle
mutable state
history
behavior
```

Example lifecycle:

```text
NOT_STARTED
    ↓
IN_PROGRESS
    ↓
COMPLETED
```

A Test match can have multiple innings, so identity also matters.

---

## 2. Core state owned by Innings

A useful starting model:

```text
Innings
-------
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

In practice, some of these may be derived or delegated, but this is a good domain starting point.

---

## 3. Score ownership

The current team score belongs to Innings.

```text
Innings
  |
  +-- Score
```

Example:

```text
156/3
```

A Score value object might be:

```python
@dataclass(frozen=True)
class Score:
    runs: int
    wickets: int
```

The Innings owns the current Score value.

---

## 4. Why score should not be mutated freely

Avoid:

```python
innings.score.runs += 4
```

Prefer controlled domain methods:

```python
innings.add_runs(4)
```

or:

```python
innings.apply_scoring_impact(impact)
```

This prevents arbitrary state changes.

---

## 5. Current batting pair

Innings needs the active batting pair:

```text
striker
non-striker
```

Invariant:

```text
striker != non_striker
```

Both must belong to the batting Playing XI.

---

## 6. Current bowler

The current bowler belongs to the bowling side.

Invariant:

```text
current_bowler must be in bowling Playing XI
```

This validation should be enforced before recording deliveries.

---

## 7. Starting an innings

A possible API:

```python
innings.start(
    striker=player_a,
    non_striker=player_b,
    opening_bowler=player_c,
)
```

Checks:

```text
innings is NOT_STARTED
striker is in batting XI
non-striker is in batting XI
striker != non-striker
bowler is in bowling XI
```

Then:

```text
status = IN_PROGRESS
current_striker = striker
current_non_striker = non_striker
current_bowler = bowler
create first over
```

---

## 8. Recording a delivery

Conceptual method:

```python
innings.record_delivery(delivery)
```

This should validate:

```text
innings is IN_PROGRESS
delivery striker matches current striker
delivery non-striker matches current non-striker
delivery bowler matches current bowler
current over is active
```

Then scoring behavior can be delegated to ScoringEngine.

---

## 9. Suggested flow

```text
Innings.record_delivery()
        ↓
validate active context
        ↓
ScoringEngine.calculate(...)
        ↓
apply ScoringImpact
        ↓
current_over.add_delivery(...)
        ↓
rotate strike if needed
        ↓
handle wicket if needed
        ↓
close over if complete
        ↓
check innings completion
```

---

## 10. ScoringImpact

A useful domain value can represent all effects of one ball.

Example:

```python
@dataclass(frozen=True)
class ScoringImpact:
    team_runs: int
    batter_runs: int
    bowler_runs: int
    wicket: bool
    legal_delivery: bool
    rotate_strike: bool
```

Then Innings applies the result instead of recalculating every rule.

---

## 11. Strike rotation

Basic idea:

```text
Odd runs
→ striker and non-striker swap
```

Also:

```text
End of over
→ striker and non-striker swap
```

But real cricket has edge cases around run-outs, completed runs, no-balls, etc.

So strike rotation should be driven by calculated scoring impact rather than simplistic assumptions everywhere.

---

## 12. A dedicated method

```python
def rotate_strike(self):
    self.current_striker, self.current_non_striker = (
        self.current_non_striker,
        self.current_striker,
    )
```

Simple, but only call it when rules say rotation is required.

---

## 13. Wicket handling

A wicket can change current batting context.

Typical flow:

```text
wicket recorded
    ↓
increment wickets
    ↓
identify dismissed batter
    ↓
mark batter dismissed
    ↓
select next batter
    ↓
update striker/non-striker based on dismissal context
```

Do not simply assume:

```text
wicket always means striker leaves
```

because run-outs can dismiss the non-striker.

---

## 14. Wicket count invariant

For standard cricket:

```text
maximum wickets = 10
```

If:

```text
wickets == 10
```

the innings is generally all out and should end, unless a special rule/context applies.

This is a domain invariant.

---

## 15. Current over ownership

An innings owns a sequence of overs:

```text
Innings
  |
  +-- Over 1
  +-- Over 2
  +-- Over 3
  ...
```

At most one over should be active.

So:

```text
current_over
```

is the active one.

---

## 16. Starting a new over

A method might be:

```python
def start_new_over(self, bowler):
    if self.current_over and not self.current_over.is_complete():
        raise InvalidOperation(
            "Current over is not complete"
        )

    self.current_over = Over(
        number=len(self.overs) + 1,
        bowler=bowler,
    )

    self.overs.append(self.current_over)
```

This protects the invariant:

```text
only one active over
```

---

## 17. Over completion

After every delivery:

```python
if self.current_over.is_complete():
    self.rotate_strike()
```

Then a new bowler/over can be selected.

Important:

```text
over completion depends on legal balls
```

not raw delivery count.

---

## 18. Innings completion conditions

Different formats may end an innings for different reasons.

Common reasons:

```text
all out
maximum overs reached
target chased
declaration
forfeit
manual completion
```

So Innings should not hard-code every format rule itself.

This is where MatchRules strategy can participate.

---

## 19. Example

```python
if self.rules.should_end_innings(self):
    self.complete()
```

Then:

```text
T20Rules
ODIRules
TestRules
```

can differ.

---

## 20. Example completion checks

Limited overs:

```text
wickets == 10
OR
overs limit reached
OR
target chased
```

Test:

```text
wickets == 10
OR
declared
OR
forfeited
```

This is a strong Strategy Pattern use case.

---

## 21. Innings status

A simple enum:

```python
class InningsStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
```

We may later add:

```text
DECLARED
FORFEITED
ALL_OUT
```

depending on whether those are statuses or completion reasons.

---

## 22. Status vs completion reason

Important distinction.

Status:

```text
IN_PROGRESS
COMPLETED
```

Completion reason:

```text
ALL_OUT
OVERS_EXHAUSTED
TARGET_REACHED
DECLARED
FORFEITED
```

Do not overload one enum with two different meanings if the distinction matters.

---

## 23. Possible model

```python
class Innings:

    def __init__(
        self,
        batting_team,
        bowling_team,
        rules,
    ):
        self.batting_team = batting_team
        self.bowling_team = bowling_team
        self.rules = rules

        self.status = InningsStatus.NOT_STARTED
        self.score = Score(0, 0)

        self.current_striker = None
        self.current_non_striker = None
        self.current_bowler = None

        self.overs = []
        self.current_over = None
```

---

## 24. start()

```python
def start(
    self,
    striker,
    non_striker,
    opening_bowler,
):
    if self.status != InningsStatus.NOT_STARTED:
        raise InvalidOperation()

    if striker == non_striker:
        raise ValueError(
            "Striker and non-striker must differ"
        )

    if not self.batting_team.is_playing_member(striker):
        raise InvalidPlayer()

    if not self.batting_team.is_playing_member(non_striker):
        raise InvalidPlayer()

    if not self.bowling_team.is_playing_member(opening_bowler):
        raise InvalidPlayer()

    self.current_striker = striker
    self.current_non_striker = non_striker
    self.current_bowler = opening_bowler

    self.status = InningsStatus.IN_PROGRESS

    self.start_new_over(opening_bowler)
```

---

## 25. apply_scoring_impact()

```python
def apply_scoring_impact(self, impact):
    self.score = Score(
        runs=self.score.runs + impact.team_runs,
        wickets=self.score.wickets + (
            1 if impact.wicket else 0
        ),
    )
```

This keeps Score immutable while Innings remains mutable.

---

## 26. complete()

```python
def complete(self, reason):
    if self.status != InningsStatus.IN_PROGRESS:
        raise InvalidOperation()

    self.status = InningsStatus.COMPLETED
    self.completion_reason = reason
```

Now completion is explicit.

---

## 27. What should Innings NOT do?

Avoid giving Innings responsibilities like:

```text
save to database
publish websocket message
send notification
update player career statistics
generate API response
```

Those belong outside the entity.

---

## 28. Application flow around Innings

```text
RecordDeliveryUseCase
      ↓
load Match
      ↓
get current Innings
      ↓
innings.record_delivery(...)
      ↓
repository.save(...)
      ↓
publish domain event
```

Innings owns cricket state.

Application service owns orchestration.

---

## 29. Derived values

Some values can be derived instead of directly stored:

```text
overs bowled
run rate
required run rate
current partnership
balls remaining
```

Whether to cache/store them is a persistence/performance decision.

Domain modelling should first ask:

> What is the source of truth?

---

## 30. Source of truth

For scoring systems, the strongest source of truth is often:

```text
Delivery history
```

Current score and statistics can be derived/projected from deliveries.

But for performance, we may also maintain current aggregate state.

Important:

```text
delivery history
→ authoritative event data

score/statistics
→ derived or maintained projections
```

---

## 31. Aggregate boundary question

Should Match be the aggregate root for Innings?

Conceptually maybe, but a live match can contain many deliveries and become huge.

So we should separate:

```text
domain ownership
```

from:

```text
persistence loading strategy
```

We may logically say Match owns Innings while repositories load only the current innings and needed state.

---

## 32. Core invariants summary

Innings must protect:

```text
cannot record before start
cannot record after completion
striker != non-striker
batters belong to batting XI
bowler belongs to bowling XI
only one current over
wickets cannot exceed allowed maximum
new over cannot start before current one completes
completion must follow valid rules
```

---

## 33. Current object picture

```text
Match
  |
  +-- MatchTeam (batting)
  +-- MatchTeam (bowling)
  |
  +-- Innings
        |
        +-- Score
        +-- striker
        +-- non-striker
        +-- current bowler
        |
        +-- Over
              |
              +-- Delivery
```

---

## 34. Interview explanation

A strong answer:

> I would model Innings as an entity because it has its own lifecycle and evolving state. It owns the current batting pair, score, active bowler and over progression. It protects innings-level invariants, while format-specific completion rules are delegated to MatchRules and cross-object scoring calculations can be delegated to ScoringEngine.

---

## Key takeaway

```text
Innings
→ owns the live scoring context

Score
→ value object

Over
→ owns legal-ball progression

ScoringEngine
→ computes delivery effects

MatchRules
→ decides format-specific completion rules
```

Innings should be rich enough to protect its state, but not become a God Object.
