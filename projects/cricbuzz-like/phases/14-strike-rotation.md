# Phase 14 — Strike Rotation in Depth

## Goal

Model striker/non-striker changes correctly after a delivery.

The simple rule:

```text
odd runs
→ swap strike
```

is useful, but incomplete.

Strike can also change because of:

- end of over
- run-out
- wicket context
- completed runs on extras
- no-ball/wide situations

So we need to separate:

```text
what happened on the delivery
```

from:

```text
who should face the next delivery
```

---

## 1. Basic batting state

Innings owns:

```text
current_striker
current_non_striker
```

Example:

```text
Striker     = Kohli
Non-striker = Rohit
```

If one run is completed:

```text
Striker     = Rohit
Non-striker = Kohli
```

So we need a strike transition.

---

## 2. Simple rotation method

```python
def rotate_strike(self):
    self.current_striker, self.current_non_striker = (
        self.current_non_striker,
        self.current_striker,
    )
```

This method is fine.

The difficult question is:

> When should we call it?

---

## 3. The naive rule

A common first version is:

```python
if total_runs % 2 == 1:
    innings.rotate_strike()
```

For normal scoring:

```text
0 runs → no swap
1 run  → swap
2 runs → no swap
3 runs → swap
4 runs → no swap
```

This works for many normal deliveries.

---

## 4. Why total team runs can be misleading

Suppose:

```text
1 wide
```

Team gets 1 run.

If we blindly do:

```python
team_runs % 2 == 1
```

we would swap strike.

But the batters may not have changed ends.

So:

```text
team runs
!= always physical runs completed by batters
```

That distinction matters.

---

## 5. Better concept: completed runs

For strike purposes, what matters is usually:

```text
how many times the batters changed ends
```

So a scoring result can expose:

```text
completed_runs
```

separately from:

```text
team_runs
```

Example:

```text
FOUR boundary
team_runs = 4
completed_runs = 0

single
team_runs = 1
completed_runs = 1

1 wide without running
team_runs = 1
completed_runs = 0
```

This is much more precise.

---

## 6. StrikeChange value object

Instead of returning only:

```text
rotate_strike = True/False
```

we can model a richer result:

```python
@dataclass(frozen=True)
class StrikeChange:
    swap_before_next_ball: bool
    swap_at_over_end: bool
```

This already separates two causes of swapping.

But we can go further when needed.

---

## 7. Better scoring impact

A stronger `ScoringImpact` could include:

```python
@dataclass(frozen=True)
class ScoringImpact:
    team_runs: int
    batter_runs: int
    bowler_runs: int
    completed_runs: int
    legal_delivery: bool
    team_wicket: bool
    bowler_wicket: bool
```

Then Innings can reason about strike from:

```text
completed_runs
+
over completion
+
wicket context
```

instead of only team_runs.

---

## 8. Normal strike rule

If there is no wicket complication:

```python
if impact.completed_runs % 2 == 1:
    self.rotate_strike()
```

This handles actual end changes.

---

## 9. End-of-over rotation

Suppose the delivery itself causes one run:

```text
before ball:
A striker
B non-striker

1 run completed
→ A/B swap

ball is sixth legal ball
→ ends swap again for new over
```

So two swaps happen:

```text
delivery swap
+
over-end swap
```

Two swaps cancel out.

The same batter may therefore face the first ball of the next over.

This is why order matters.

---

## 10. Processing order matters

A clean sequence can be:

```text
1. apply completed-run strike change
2. handle wicket-specific batter changes
3. add delivery to over
4. if over completed, perform end-of-over swap
5. select next bowler
```

The exact order must be consistent with cricket rules and your domain representation.

---

## 11. Example: sixth ball, zero runs

Before:

```text
A striker
B non-striker
```

Ball:

```text
0 runs
6th legal ball
```

No delivery swap.

Then over completes:

```text
swap ends
```

Next over:

```text
B striker
A non-striker
```

---

## 12. Example: sixth ball, one run

Before:

```text
A striker
B non-striker
```

One run:

```text
A/B swap
```

Then over ends:

```text
swap again
```

Next over:

```text
A striker
B non-striker
```

This is a great example of why:

```text
odd run → swap
```

is not the whole story.

---

## 13. Wicket complication

Suppose striker is dismissed.

We cannot simply:

```text
increment wicket
bring next batter as striker
```

because the dismissed batter could be:

```text
striker
or
non-striker
```

and completed runs may have changed ends.

WicketInfo must tell us:

```text
dismissed_player
```

---

## 14. Run-out example

Before:

```text
A striker
B non-striker
```

They attempt a run.

B is run out.

The next batter position depends on:

```text
who was dismissed
how many runs were completed
which end each batter reached
whether over ended
```

So:

```text
wicket = true
```

alone is insufficient to determine the next striker.

---

## 15. Why ScoringEngine should not choose actual next Player

The ScoringEngine usually knows:

```text
delivery outcome
completed runs
wicket type
```

But choosing the next batter requires:

```text
batting order
remaining players
innings state
```

That belongs to Innings or a batting-order component.

So keep:

```text
ScoringEngine
→ calculate movement/effects

Innings
→ choose next batter and update active pair
```

---

## 16. BattingOrder concept

If batting-order behavior grows, we could introduce:

```text
BattingOrder
------------
players
next_batter()
is_available(player)
mark_dismissed(player)
```

Then Innings can ask:

```python
new_batter = self.batting_order.next_batter()
```

Do not add this abstraction until needed, but it is a natural extension.

---

## 17. Wide and strike

A simple wide may add one team run without the batters changing ends.

So:

```text
team_runs = 1
completed_runs = 0
```

No strike swap.

If the batters also run on the wide:

```text
wide extras
+
completed runs
```

then strike depends on the physical completed runs.

Again:

```text
team_runs alone is not enough
```

---

## 18. No-ball and strike

No-ball can produce:

```text
automatic no-ball run
+
batter runs
+
possibly completed runs
```

Strike should be based on end changes, not simply total score added.

This is another reason to carry:

```text
completed_runs
```

explicitly.

---

## 19. Boundary runs

A FOUR or SIX normally does not require the batters to physically complete odd runs.

So:

```text
FOUR
team_runs = 4
completed_runs = 0
```

```text
SIX
team_runs = 6
completed_runs = 0
```

No strike change due to running.

---

## 20. A cleaner transition object

As complexity grows, we can create:

```python
@dataclass(frozen=True)
class BattingTransition:
    completed_runs: int
    dismissed_player: Player | None
    over_completed: bool
```

Then Innings owns:

```python
def apply_batting_transition(self, transition):
    ...
```

This keeps batting-state changes together.

---

## 21. Possible Innings flow

```python
def record_delivery(self, delivery, impact):

    self.apply_score(impact)

    self._apply_completed_runs(
        impact.completed_runs
    )

    if impact.team_wicket:
        self._handle_wicket(
            delivery.result.wicket
        )

    self.current_over.add_delivery(
        delivery
    )

    if self.current_over.is_complete():
        self._handle_over_completion()
```

This is conceptual code, not final cricket-rule completeness.

---

## 22. `_apply_completed_runs`

```python
def _apply_completed_runs(self, completed_runs):

    if completed_runs % 2 == 1:
        self.rotate_strike()
```

Simple and focused.

---

## 23. `_handle_over_completion`

```python
def _handle_over_completion(self):

    self.rotate_strike()

    self.current_over = None
    self.current_bowler = None
```

Then the application/domain flow chooses the next bowler and starts the next over.

---

## 24. Avoid duplicated strike state

Do not store:

```text
delivery.next_striker
innings.current_striker
over.next_striker
```

as independent truths unless there is a good historical reason.

The live source of truth should be:

```text
Innings.current_striker
Innings.current_non_striker
```

Historical deliveries store who participated in that event.

---

## 25. Delivery stores historical participants

Each Delivery should still contain:

```text
striker at time of ball
non-striker at time of ball
bowler
```

This is important because current Innings state changes later.

So:

```text
Innings
→ current state

Delivery
→ historical snapshot
```

---

## 26. Why this helps correction/replay

If deliveries preserve:

```text
participants
result
completed runs
wicket info
```

we can replay them to reconstruct:

```text
score
strike
wickets
stats
```

That supports controlled corrections.

---

## 27. State ownership

```text
ScoringEngine
→ calculates delivery effects

Over
→ decides whether over is complete

Innings
→ owns striker/non-striker

BattingOrder
→ optionally owns next-batter selection
```

This avoids circular responsibilities.

---

## 28. Do not over-model too early

For a basic machine-coding interview, this may be enough:

```python
if runs_completed % 2 == 1:
    rotate_strike()

if over.is_complete():
    rotate_strike()
```

Then verbally explain:

> For production cricket scoring I would model run-outs and extras with a richer batting transition because team runs alone do not determine end changes.

That is a strong interview tradeoff.

---

## 29. Interview explanation

A strong answer:

> I would not derive strike purely from total team runs because wides, no-balls and run-outs can make that incorrect. I would track the number of completed physical runs separately, let Innings own striker/non-striker state, and perform a separate end-of-over swap after the sixth legal delivery. Wicket handling would use the explicitly dismissed player and batting order to determine the next active pair.

---

## 30. Mental model

```text
DeliveryResult
      |
      v
ScoringEngine
      |
      v
completed_runs
wicket effects
      |
      v
Innings
      |
      +-- delivery-level strike change
      +-- wicket handling
      +-- over-end strike change
```

---

## Key takeaway

```text
Team runs
!=
completed physical runs
```

and:

```text
delivery strike change
+
wicket transition
+
over-end strike change
```

together determine who faces the next ball.
