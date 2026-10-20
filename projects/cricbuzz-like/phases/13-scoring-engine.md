# Phase 13 — Scoring Engine in Depth

## Goal

Create a clean scoring engine that converts one delivery outcome into all the domain effects needed by the rest of the system.

Input:

```text
DeliveryResult
```

Output:

```text
ScoringImpact
```

Then higher-level objects apply the impact.

---

## 1. Why we need a ScoringEngine

Without a scoring engine, Innings can become full of cricket-specific branches:

```python
if wide:
    ...
elif no_ball:
    ...
elif bye:
    ...
elif leg_bye:
    ...
elif wicket:
    ...
```

That mixes:

```text
state ownership
+
scoring rules
+
statistics rules
```

A better split is:

```text
DeliveryResult
      ↓
ScoringEngine
      ↓
ScoringImpact
      ↓
Innings / stats / over apply it
```

---

## 2. Input: DeliveryResult

```python
@dataclass(frozen=True)
class DeliveryResult:
    batter_runs: int
    extras: Extras
    wicket: WicketInfo | None = None

    @property
    def total_team_runs(self):
        return (
            self.batter_runs
            + self.extras.total()
        )

    @property
    def is_legal(self):
        return (
            self.extras.wides == 0
            and self.extras.no_balls == 0
        )
```

This describes what happened.

---

## 3. Output: ScoringImpact

```python
@dataclass(frozen=True)
class ScoringImpact:
    team_runs: int
    batter_runs: int
    bowler_runs: int

    legal_delivery: bool

    batter_ball_faced: bool
    team_wicket: bool
    bowler_wicket: bool

    rotate_strike: bool
```

Why separate these?

Because one delivery affects different projections differently.

---

## 4. Example: normal FOUR

Input:

```text
batter_runs = 4
extras = 0
wicket = None
```

Impact:

```text
team_runs = 4
batter_runs = 4
bowler_runs = 4
legal_delivery = true
batter_ball_faced = true
team_wicket = false
bowler_wicket = false
rotate_strike = false
```

---

## 5. Example: 1 run

Impact:

```text
team_runs = 1
batter_runs = 1
bowler_runs = 1
legal_delivery = true
batter_ball_faced = true
rotate_strike = true
```

---

## 6. Example: wide

Input:

```text
wides = 1
```

Impact:

```text
team_runs = 1
batter_runs = 0
bowler_runs = 1
legal_delivery = false
batter_ball_faced = false
rotate_strike = false
```

---

## 7. Example: no-ball + FOUR off bat

Input:

```text
batter_runs = 4
no_ball = 1
```

Impact:

```text
team_runs = 5
batter_runs = 4
bowler_runs = 5
legal_delivery = false
batter_ball_faced = true
rotate_strike = false
```

---

## 8. Example: four byes

Input:

```text
batter_runs = 0
byes = 4
```

Impact:

```text
team_runs = 4
batter_runs = 0
bowler_runs = 0
legal_delivery = true
batter_ball_faced = true
rotate_strike = false
```

---

## 9. Example: run-out

Input:

```text
wicket.kind = RUN_OUT
```

Impact:

```text
team_wicket = true
bowler_wicket = false
```

The dismissed player comes from WicketInfo.

---

## 10. ScoringEngine implementation

```python
class ScoringEngine:

    def calculate(self, result: DeliveryResult) -> ScoringImpact:

        team_runs = result.total_team_runs

        bowler_runs = self._bowler_runs(result)

        team_wicket = result.wicket is not None

        bowler_wicket = (
            self._is_bowler_wicket(result.wicket)
            if result.wicket
            else False
        )

        batter_ball_faced = (
            result.extras.wides == 0
        )

        rotate_strike = (
            team_runs % 2 == 1
        )

        return ScoringImpact(
            team_runs=team_runs,
            batter_runs=result.batter_runs,
            bowler_runs=bowler_runs,
            legal_delivery=result.is_legal,
            batter_ball_faced=batter_ball_faced,
            team_wicket=team_wicket,
            bowler_wicket=bowler_wicket,
            rotate_strike=rotate_strike,
        )
```

This is only a starting model. Real cricket has edge cases, but the architecture is the important point.

---

## 11. Bowler runs calculation

Wides and no-balls are normally charged to the bowler.

Byes and leg-byes are not.

So:

```python
def _bowler_runs(self, result):
    return (
        result.batter_runs
        + result.extras.wides
        + result.extras.no_balls
    )
```

Penalty-run treatment may depend on competition rules, so do not hard-code assumptions carelessly if that requirement matters.

---

## 12. Bowler wicket calculation

```python
BOWLER_WICKET_KINDS = {
    WicketKind.BOWLED,
    WicketKind.CAUGHT,
    WicketKind.LBW,
    WicketKind.STUMPED,
    WicketKind.HIT_WICKET,
}
```

Then:

```python
def _is_bowler_wicket(self, wicket):
    return (
        wicket.kind
        in BOWLER_WICKET_KINDS
    )
```

This keeps:

```text
team wicket
!=
bowler wicket
```

---

## 13. Batter ball faced

A wide does not count as a ball faced by the batter.

A no-ball generally does count as a ball faced for batting statistics when applicable, unlike a wide.

That means:

```python
batter_ball_faced = (
    result.extras.wides == 0
)
```

Again, scoring rules should be centralized rather than copied into stats code.

---

## 14. Strike rotation

A naive rule:

```text
odd total runs
→ rotate strike
```

works for many normal cases.

But run-outs and some edge cases can change who ends up at which end.

So a more advanced design may return:

```text
next_striker
next_non_striker
```

or a richer StrikeChange value instead of one boolean.

Do not over-design until the requirement appears.

---

## 15. Applying impact to Innings

```python
def apply_scoring_impact(self, impact):

    self.score = Score(
        runs=(
            self.score.runs
            + impact.team_runs
        ),
        wickets=(
            self.score.wickets
            + (1 if impact.team_wicket else 0)
        ),
    )
```

Then:

```python
if impact.rotate_strike:
    self.rotate_strike()
```

---

## 16. Applying impact to Over

```python
self.current_over.add_delivery(delivery)
```

Over decides whether legal-ball count changes.

That is still Over's responsibility.

ScoringEngine does not mutate Over directly.

---

## 17. Applying impact to batter stats

A match batting stat object may update:

```text
runs
balls faced
fours
sixes
dismissal
```

Example:

```python
batter_stats.runs += impact.batter_runs

if impact.batter_ball_faced:
    batter_stats.balls += 1
```

Boundary counts can be derived from batter_runs:

```text
4 → four +1
6 → six +1
```

---

## 18. Applying impact to bowler stats

A bowler stat projection may update:

```text
legal balls
runs conceded
wickets
wides
no-balls
```

Example:

```python
bowler_stats.runs_conceded += (
    impact.bowler_runs
)

if impact.legal_delivery:
    bowler_stats.legal_balls += 1

if impact.bowler_wicket:
    bowler_stats.wickets += 1
```

---

## 19. Why ScoringEngine should not update every object itself

Bad:

```text
ScoringEngine
  updates Innings
  updates Over
  updates BatterStats
  updates BowlerStats
  publishes websocket
  saves database
```

Then ScoringEngine becomes a God Service.

Better:

```text
ScoringEngine
→ calculate effects

Domain/application layer
→ apply effects to owners
```

This is a very important separation.

---

## 20. Pure calculation is easier to test

A ScoringEngine can be nearly pure:

```text
input
→ output
```

Example test:

```python
result = DeliveryResult(
    batter_runs=4,
    extras=Extras(no_balls=1),
)

impact = engine.calculate(result)

assert impact.team_runs == 5
assert impact.batter_runs == 4
assert impact.bowler_runs == 5
assert impact.legal_delivery is False
```

No database.
No HTTP.
No Redis.

That makes unit tests very easy.

---

## 21. Command flow

```text
POST delivery
    ↓
Controller
    ↓
RecordDeliveryUseCase
    ↓
load Match/Innings
    ↓
build DeliveryResult
    ↓
build Delivery
    ↓
ScoringEngine.calculate()
    ↓
ScoringImpact
    ↓
Innings.apply(...)
Over.add_delivery(...)
Stats.apply(...)
    ↓
save transaction
    ↓
publish event
```

---

## 22. Transaction boundary

Recording a delivery may update multiple pieces of state.

They should succeed atomically.

Conceptually:

```text
BEGIN

save delivery
update innings score
update over
update batter stats
update bowler stats

COMMIT
```

If one critical update fails:

```text
ROLLBACK
```

This prevents partial scoring state.

---

## 23. Idempotency

A scorer/client may retry the same request.

Without protection:

```text
12.3 FOUR
submitted twice
→ score increases by 8
```

So each record-delivery command should have a stable idempotency key or unique event identity.

Example:

```text
command_id
or
client_event_id
```

Then duplicate requests can be recognized.

---

## 24. Versioning / optimistic locking

Two scorers might update the same innings concurrently.

A version field can help:

```text
innings.version = 42
```

Request expects version 42.

If database now has version 43:

```text
reject conflict
```

This prevents lost updates.

---

## 25. Events after scoring

After a successful transaction, the application can publish:

```text
DeliveryRecorded
ScoreUpdated
WicketFallen
OverCompleted
InningsCompleted
```

Other parts of the system can react:

```text
commentary
websocket
notifications
analytics
```

Do not mix those concerns into the scoring calculation itself.

---

## 26. Scoring engine vs rules strategy

ScoringEngine performs generic delivery-effect calculation.

MatchRules handles format-specific behavior.

```text
ScoringEngine
→ wide/no-ball/bye/wicket effects

MatchRules
→ T20/ODI/Test constraints and completion rules
```

They solve different kinds of variation.

---

## 27. Example full flow: FOUR

```text
DeliveryResult
  batter_runs = 4
  extras = 0

        ↓

ScoringEngine

        ↓

ScoringImpact
  team_runs = 4
  batter_runs = 4
  bowler_runs = 4
  legal_delivery = true
  rotate_strike = false

        ↓

Innings score +4
Batter runs +4
Batter balls +1
Bowler runs +4
Over legal balls +1
```

---

## 28. Example full flow: WIDE

```text
DeliveryResult
  wides = 1

        ↓

ScoringImpact
  team_runs = 1
  batter_runs = 0
  bowler_runs = 1
  legal_delivery = false
  batter_ball_faced = false

        ↓

Innings score +1
Bowler runs +1
Over legal balls unchanged
Batter balls unchanged
```

---

## 29. Example full flow: RUN OUT

```text
DeliveryResult
  wicket = RUN_OUT

        ↓

ScoringImpact
  team_wicket = true
  bowler_wicket = false

        ↓

Innings wickets +1
Dismissed batter marked out
Bowler wickets unchanged
Next batter required
```

---

## 30. Responsibility summary

```text
DeliveryResult
→ what happened

ScoringEngine
→ calculate consequences

ScoringImpact
→ immutable result of calculation

Innings
→ apply team-state changes

Over
→ apply legal-ball progression

BattingStats
→ apply batter effects

BowlingStats
→ apply bowler effects

Application Service
→ orchestrate transaction
```

---

## 31. Interview explanation

A strong answer:

> I would make the scoring engine primarily a pure domain calculator. It receives a validated DeliveryResult and returns a ScoringImpact describing team runs, batter runs, bowler runs, legality and wicket effects. The owning domain objects then apply those effects. This keeps scoring rules testable and prevents the engine from becoming a God Service.

---

## Key takeaway

```text
Do not let one method mutate everything.

Calculate first.
Apply second.
Persist atomically.
Publish events after success.
```
