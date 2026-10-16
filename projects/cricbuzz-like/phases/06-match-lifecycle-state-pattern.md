# Phase 06 — Match Lifecycle & State Pattern

## Goal

Model the match lifecycle cleanly and decide when a simple enum is enough versus when the State Pattern is justified.

## Match lifecycle

```text
SCHEDULED
    ↓
TOSS_COMPLETED
    ↓
IN_PROGRESS
    ↓
COMPLETED

Possible side transitions:
SCHEDULED → CANCELLED
IN_PROGRESS → ABANDONED
```

## Start simple: enum + guards

```python
class MatchStatus(Enum):
    SCHEDULED = "scheduled"
    TOSS_COMPLETED = "toss_completed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    CANCELLED = "cancelled"
```

Then let Match protect transitions:

```python
class Match:
    def start(self):
        if self.status != MatchStatus.TOSS_COMPLETED:
            raise InvalidMatchState()

        self.status = MatchStatus.IN_PROGRESS
```

This is often enough at first.

## When enum checks start becoming noisy

If many methods look like this:

```python
def record_toss(self, ...):
    if self.status != MatchStatus.SCHEDULED:
        ...

def start(self):
    if self.status != MatchStatus.TOSS_COMPLETED:
        ...

def record_delivery(self, ...):
    if self.status != MatchStatus.IN_PROGRESS:
        ...

def complete(self):
    if self.status != MatchStatus.IN_PROGRESS:
        ...
```

then state-specific behavior is spreading everywhere.

That is the signal for the State Pattern.

## State Pattern idea

Instead of one status value plus many conditionals:

```text
Match
  |
  └── current_state
        |
        ├── ScheduledState
        ├── TossCompletedState
        ├── InProgressState
        ├── CompletedState
        ├── AbandonedState
        └── CancelledState
```

Each state object defines which operations are valid.

## Base state

```python
class MatchState:
    def record_toss(self, match, toss):
        raise InvalidMatchState()

    def start(self, match):
        raise InvalidMatchState()

    def record_delivery(self, match, delivery):
        raise InvalidMatchState()

    def complete(self, match):
        raise InvalidMatchState()

    def abandon(self, match):
        raise InvalidMatchState()
```

Unsupported actions fail by default.

## ScheduledState

```python
class ScheduledState(MatchState):
    def record_toss(self, match, toss):
        match.toss = toss
        match.state = TossCompletedState()
```

## TossCompletedState

```python
class TossCompletedState(MatchState):
    def start(self, match):
        match.state = InProgressState()
```

## InProgressState

```python
class InProgressState(MatchState):
    def record_delivery(self, match, delivery):
        match.current_innings.record_delivery(delivery)

    def complete(self, match):
        if not match.can_complete():
            raise MatchCannotComplete()

        match.state = CompletedState()

    def abandon(self, match):
        match.state = AbandonedState()
```

## CompletedState

```python
class CompletedState(MatchState):
    pass
```

The base class already rejects invalid mutations.

## Match as the context

```python
class Match:
    def __init__(self, ...):
        self.state = ScheduledState()

    def record_toss(self, toss):
        self.state.record_toss(self, toss)

    def start(self):
        self.state.start(self)

    def record_delivery(self, delivery):
        self.state.record_delivery(self, delivery)

    def complete(self):
        self.state.complete(self)
```

Match stays the main entity; it delegates state-specific behavior.

## Transition picture

```text
ScheduledState
   |
   | record_toss
   v
TossCompletedState
   |
   | start
   v
InProgressState
   |
   | complete
   v
CompletedState
```

Side transitions:

```text
ScheduledState ------> CancelledState
TossCompletedState --> CancelledState
InProgressState -----> AbandonedState
```

## Enum vs State Pattern

Use enum + guards when:

- Few states exist
- State-specific behavior is small
- Rules remain easy to read
- New states are unlikely

Use State Pattern when:

- Many operations depend on current state
- Status checks appear across many methods
- Transitions are complex
- New states are added often
- Different states have strongly different behavior

## Important rule

Do not use State Pattern just because a `status` field exists.

Patterns should solve actual complexity.

## State vs Strategy

```text
State
→ behavior changes because the object moves through lifecycle states

Strategy
→ behavior changes because an algorithm/rule-set is selected
```

Cricbuzz examples:

```text
Match lifecycle
→ State Pattern

T20 / ODI / Test rules
→ Strategy Pattern
```

## Persistence

In memory:

```text
match.state = InProgressState()
```

Database:

```text
match.status = "in_progress"
```

On load:

```text
"in_progress" → InProgressState()
```

The State objects do not need their own database rows.

## State reconstruction

```python
def state_from_status(status):
    mapping = {
        MatchStatus.SCHEDULED: ScheduledState,
        MatchStatus.TOSS_COMPLETED: TossCompletedState,
        MatchStatus.IN_PROGRESS: InProgressState,
        MatchStatus.COMPLETED: CompletedState,
        MatchStatus.ABANDONED: AbandonedState,
        MatchStatus.CANCELLED: CancelledState,
    }

    return mapping[status]()
```

## Interview reasoning

A strong answer is:

> I would begin with an enum and guarded transitions. If state checks spread across many operations, I would move state-specific behavior into State objects so each lifecycle state defines valid operations and transitions. Persistence can still store only a status value.

## Key takeaway

```text
Enum
→ represents state

State Pattern
→ represents state-specific behavior
```
