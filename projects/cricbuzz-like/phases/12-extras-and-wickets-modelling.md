# Phase 12 — Extras and Wickets Modelling in Depth

## Goal

Model extras and wickets so that one delivery can correctly represent combinations such as:

- wide
- no-ball
- bye
- leg-bye
- wicket
- run-out
- no-ball + batter runs
- wide + run-out

The key challenge is avoiding contradictory states.

---

## 1. Why Extras needs a real value object

Do not model extras as:

```python
extras = 3
```

because these have different meanings:

```text
3 wides
3 byes
3 leg-byes
1 no-ball + 2 byes
```

A better model:

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

## 2. Extras affect different statistics differently

Example:

```text
wide
→ team score increases
→ bowler conceded runs increase
→ batter gets 0
→ legal ball count does not increase

bye
→ team score increases
→ bowler conceded runs usually do not increase
→ batter gets 0
→ legal ball count increases
```

So the scoring engine must distinguish extra types.

---

## 3. Legality should be derived

A delivery is illegal if it contains a:

```text
wide
or
no-ball
```

So avoid storing:

```text
extras.no_balls = 1
is_legal = True
```

That is contradictory.

Prefer:

```python
@property
def is_legal(self):
    return (
        self.extras.wides == 0
        and self.extras.no_balls == 0
    )
```

One source of truth.

---

## 4. Batter runs vs team runs

These are not always the same.

Example:

```text
batter hits FOUR
```

```text
batter_runs = 4
extras = 0
team_runs = 4
```

But:

```text
wide
```

```text
batter_runs = 0
extras = 1
team_runs = 1
```

And:

```text
no-ball + FOUR off bat
```

```text
batter_runs = 4
no_ball = 1
team_runs = 5
```

Therefore:

```python
team_runs = batter_runs + extras.total()
```

---

## 5. DeliveryResult

A useful structure:

```python
@dataclass(frozen=True)
class DeliveryResult:
    batter_runs: int
    extras: Extras
    wicket: WicketInfo | None = None

    @property
    def team_runs(self):
        return self.batter_runs + self.extras.total()

    @property
    def is_legal(self):
        return (
            self.extras.wides == 0
            and self.extras.no_balls == 0
        )
```

This keeps delivery outcome cohesive.

---

## 6. Why WicketInfo is separate

A wicket has multiple pieces of information:

```text
dismissal type
dismissed player
fielder
whether bowler receives credit
```

So:

```python
@dataclass(frozen=True)
class WicketInfo:
    kind: WicketKind
    dismissed_player: Player
    fielder: Player | None = None
```

---

## 7. Wicket kinds

Examples:

```python
class WicketKind(Enum):
    BOWLED = "bowled"
    CAUGHT = "caught"
    LBW = "lbw"
    RUN_OUT = "run_out"
    STUMPED = "stumped"
    HIT_WICKET = "hit_wicket"
    RETIRED_OUT = "retired_out"
```

A controlled enum prevents arbitrary string values.

---

## 8. Bowler credit is not the same as wicket event

A team wicket may happen without the bowler receiving credit.

For example:

```text
RUN_OUT
→ team wicket +1
→ bowler wicket +0
```

Whereas:

```text
BOWLED
CAUGHT
LBW
STUMPED
HIT_WICKET
→ usually bowler credited
```

So do not equate:

```text
wicket happened
=
bowler gets wicket
```

---

## 9. Derive bowler credit from wicket kind

For example:

```python
BOWLER_CREDITED_WICKETS = {
    WicketKind.BOWLED,
    WicketKind.CAUGHT,
    WicketKind.LBW,
    WicketKind.STUMPED,
    WicketKind.HIT_WICKET,
}
```

Then:

```python
def credited_to_bowler(wicket_info):
    return (
        wicket_info.kind
        in BOWLER_CREDITED_WICKETS
    )
```

This avoids manually storing:

```text
credited_to_bowler = True
```

when it can be derived.

---

## 10. Striker is not always dismissed

Do not assume:

```python
dismissed_player = delivery.striker
```

Run-out can dismiss:

```text
striker
or
non-striker
```

So WicketInfo must explicitly identify the dismissed player.

---

## 11. Wide + wicket

A delivery can be:

```text
wide + run-out
```

Possible effects:

```text
team runs + wide extras
wicket +1
legal ball count unchanged
bowler wicket credit may be 0 depending on dismissal
```

This is why a delivery result must support extras and wicket simultaneously.

---

## 12. No-ball + wicket

A no-ball can also have a wicket event, but not all dismissal types are valid on a no-ball.

This means validation may depend on:

```text
extras
+
wicket kind
```

That is cross-field domain validation.

---

## 13. Cross-field validation

A value object can reject impossible combinations.

Example idea:

```python
@dataclass(frozen=True)
class DeliveryResult:
    batter_runs: int
    extras: Extras
    wicket: WicketInfo | None = None

    def __post_init__(self):
        if self.batter_runs < 0:
            raise ValueError(
                "Batter runs cannot be negative"
            )

        if self.extras.wides > 0 and self.extras.no_balls > 0:
            raise ValueError(
                "A delivery cannot be both wide and no-ball"
            )
```

You can add more rules as the domain requires them.

---

## 14. Why validation belongs close to the value

If invalid combinations can exist, every caller must remember to validate.

Better:

```text
DeliveryResult creation
→ guarantees a valid result
```

Then the rest of the domain can trust it.

This is another example of:

> Make invalid states hard to represent.

---

## 15. ScoringImpact should separate team, batter and bowler effects

A strong scoring output might be:

```python
@dataclass(frozen=True)
class ScoringImpact:
    team_runs: int
    batter_runs: int
    bowler_runs: int
    team_wicket: bool
    bowler_wicket: bool
    legal_delivery: bool
```

Why separate fields?

Because one delivery can affect each perspective differently.

---

## 16. Example: normal FOUR

```text
batter_runs = 4
team_runs = 4
bowler_runs = 4
team_wicket = false
bowler_wicket = false
legal_delivery = true
```

---

## 17. Example: one wide

```text
batter_runs = 0
team_runs = 1
bowler_runs = 1
team_wicket = false
bowler_wicket = false
legal_delivery = false
```

---

## 18. Example: four byes

```text
batter_runs = 0
team_runs = 4
bowler_runs = 0
team_wicket = false
bowler_wicket = false
legal_delivery = true
```

This shows why team runs and bowler runs must be separate.

---

## 19. Example: no-ball + batter FOUR

```text
batter_runs = 4
team_runs = 5
bowler_runs = 5
legal_delivery = false
```

---

## 20. Example: run-out

```text
team_wicket = true
bowler_wicket = false
```

Again, different projections.

---

## 21. ScoringEngine responsibility

The ScoringEngine can transform:

```text
DeliveryResult
```

into:

```text
ScoringImpact
```

Conceptually:

```python
class ScoringEngine:

    def calculate(self, result):
        ...
        return ScoringImpact(...)
```

Then Innings applies the result.

---

## 22. Why Innings should not know every extra rule

Avoid:

```python
if result.extras.wides:
    ...
elif result.extras.no_balls:
    ...
elif result.extras.byes:
    ...
```

inside a huge Innings method.

Innings should own state.

ScoringEngine can own delivery-effect calculation.

---

## 23. Wicket application flow

Conceptually:

```text
DeliveryResult contains WicketInfo
        ↓
ScoringEngine calculates impact
        ↓
Innings increments team wicket
        ↓
dismissed player identified
        ↓
next batter selected
        ↓
striker/non-striker updated
```

Do not bury all of this inside DeliveryResult.

---

## 24. Selecting the next batter

The domain needs to know batting order / remaining eligible batters.

Possible owner:

```text
Innings batting lineup
```

or a dedicated batting-order object if complexity grows.

The key point is:

```text
Delivery does not choose the next batter
```

because that is higher-level innings behavior.

---

## 25. Wicket as event vs dismissal record

A wicket can be treated as a value object inside Delivery when it has no independent lifecycle.

If later the system needs:

```text
review history
correction history
audit identity
independent event references
```

then Wicket may become entity-like.

Classification depends on requirements.

---

## 26. Avoid duplicated truth

Bad:

```text
wicket.kind = RUN_OUT
bowler_credit = True
```

Those values disagree.

Better:

derive bowler credit from wicket kind.

Bad:

```text
no_ball = 1
is_legal = True
```

Better:

derive legality.

The general rule is:

> Store causes; derive consequences where practical.

---

## 27. Source-of-truth hierarchy

A useful mental model:

```text
DeliveryResult
  |
  +-- batter runs
  +-- extras
  +-- wicket info
```

Then derive:

```text
team runs
legal/illegal
bowler conceded
team wicket
bowler wicket
```

This reduces contradictory state.

---

## 28. Current object picture

```text
Delivery
   |
   +-- DeliveryResult
         |
         +-- batter_runs
         |
         +-- Extras
         |     +-- wides
         |     +-- no_balls
         |     +-- byes
         |     +-- leg_byes
         |     +-- penalty
         |
         +-- WicketInfo
               +-- kind
               +-- dismissed_player
               +-- fielder
```

Then:

```text
ScoringEngine
      |
      v
ScoringImpact
      |
      +-- team_runs
      +-- batter_runs
      +-- bowler_runs
      +-- team_wicket
      +-- bowler_wicket
      +-- legal_delivery
```

---

## 29. Interview explanation

A strong answer:

> I would keep extras as a structured value object because different extra types affect team score, bowler figures and ball legality differently. WicketInfo would explicitly identify dismissal type and dismissed player. I would derive consequences such as legality and bowler wicket credit instead of storing duplicate flags that can contradict the source data.

---

## Key takeaway

```text
Extras are not one number.

Wicket event != bowler wicket.

Striker != always dismissed player.

Store the cause.
Derive the consequences.
```
