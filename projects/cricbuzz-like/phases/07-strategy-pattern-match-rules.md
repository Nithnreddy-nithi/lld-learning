# Phase 07 — Strategy Pattern for Match Rules

## Goal

Use Strategy Pattern when the same operation has different rule implementations depending on match format.

For Cricbuzz-like scoring:

```text
T20
ODI
TEST
```

share the same overall match flow, but some rules differ.

Examples:

```text
maximum overs
maximum overs per bowler
powerplay rules
follow-on rules
result rules
innings limits
```

## The naive approach

A common first implementation is:

```python
def get_max_overs(match_format):
    if match_format == "T20":
        return 20

    elif match_format == "ODI":
        return 50

    elif match_format == "TEST":
        return None
```

Then another function:

```python
def max_overs_per_bowler(match_format):
    if match_format == "T20":
        return 4

    elif match_format == "ODI":
        return 10

    elif match_format == "TEST":
        return None
```

Then again:

```python
def supports_follow_on(match_format):
    if match_format == "T20":
        return False

    elif match_format == "ODI":
        return False

    elif match_format == "TEST":
        return True
```

Now format checks are spread everywhere.

## The problem

Whenever a new format is introduced, such as:

```text
T10
The Hundred
```

many functions need modification.

That creates:

```text
if format == ...
elif format == ...
elif format == ...
```

throughout the codebase.

The varying behavior should be grouped by rule-set instead.

## Strategy Pattern idea

Strategy Pattern means:

> Put each interchangeable algorithm/rule-set in its own object, and let the caller work through one common contract.

Conceptually:

```text
MatchRules
   ↑
   |
   +---- T20Rules
   +---- ODIRules
   +---- TestRules
```

The Match does not need to ask:

```text
Am I T20?
Am I ODI?
Am I Test?
```

It asks its configured rules object.

## Strategy contract

For teaching purposes, a base class can define operations expected from every match rule-set:

```python
from abc import ABC, abstractmethod


class MatchRules(ABC):

    @abstractmethod
    def max_overs(self):
        pass

    @abstractmethod
    def max_overs_per_bowler(self):
        pass

    @abstractmethod
    def supports_follow_on(self):
        pass
```

Unlike the State example, this contract makes sense because every strategy answers the same questions.

A Test strategy may return `None` for "no fixed limit", but it still meaningfully answers the question.

## T20 strategy

```python
class T20Rules(MatchRules):

    def max_overs(self):
        return 20

    def max_overs_per_bowler(self):
        return 4

    def supports_follow_on(self):
        return False
```

## ODI strategy

```python
class ODIRules(MatchRules):

    def max_overs(self):
        return 50

    def max_overs_per_bowler(self):
        return 10

    def supports_follow_on(self):
        return False
```

## Test strategy

```python
class TestRules(MatchRules):

    def max_overs(self):
        return None

    def max_overs_per_bowler(self):
        return None

    def supports_follow_on(self):
        return True
```

## Match uses the strategy

```python
class Match:

    def __init__(self, rules: MatchRules):
        self.rules = rules

    def maximum_overs(self):
        return self.rules.max_overs()

    def maximum_overs_per_bowler(self):
        return self.rules.max_overs_per_bowler()
```

Usage:

```python
match = Match(T20Rules())

print(match.maximum_overs())
# 20
```

Or:

```python
match = Match(ODIRules())

print(match.maximum_overs())
# 50
```

The Match code stays unchanged.

Only the strategy object changes.

## Why this is better

Without Strategy:

```text
Match
  |
  └── checks format everywhere
```

With Strategy:

```text
Match
  |
  └── MatchRules
        |
        +-- T20Rules
        +-- ODIRules
        +-- TestRules
```

The Match depends on behavior, not on a particular format.

## Runtime selection

A factory can select the correct strategy:

```python
class MatchRulesFactory:

    @staticmethod
    def create(match_format):
        if match_format == MatchFormat.T20:
            return T20Rules()

        if match_format == MatchFormat.ODI:
            return ODIRules()

        if match_format == MatchFormat.TEST:
            return TestRules()

        raise ValueError("Unsupported format")
```

Then:

```python
rules = MatchRulesFactory.create(MatchFormat.T20)

match = Match(rules)
```

Notice the format conditional now exists in one construction location instead of everywhere in the domain.

## Strategy vs State

They look structurally similar because both use polymorphism.

But the reason for switching behavior is different.

```text
STATE

Match:
Scheduled → InProgress → Completed

Behavior changes because the SAME object moves through lifecycle states.
```

```text
STRATEGY

T20Rules
ODIRules
TestRules

Behavior changes because we SELECT a rule-set/algorithm.
```

A match normally does not become:

```text
T20 → ODI → Test
```

during its lifecycle.

Its format strategy is usually chosen at creation and remains stable.

## Composition over inheritance

We do not want:

```python
class T20Match(Match):
    ...

class ODIMatch(Match):
    ...

class TestMatch(Match):
    ...
```

unless the entire Match object truly behaves differently.

Usually:

```python
class Match:
    def __init__(self, rules):
        self.rules = rules
```

is cleaner.

This is composition:

```text
Match HAS-A MatchRules
```

instead of inheritance:

```text
T20Match IS-A Match
```

The varying concern is the rule-set, so extract that concern.

## Open/Closed Principle connection

Suppose we add:

```text
T10
```

With Strategy:

```python
class T10Rules(MatchRules):

    def max_overs(self):
        return 10

    def max_overs_per_bowler(self):
        return 2

    def supports_follow_on(self):
        return False
```

Existing `Match` does not change.

That is the core Open/Closed Principle idea:

```text
open for extension
closed for modification
```

The factory may need registration/update, which we can improve later if needed.

## Dependency Inversion connection

Bad dependency:

```text
Match → T20-specific rules
Match → ODI-specific rules
Match → Test-specific rules
```

Better:

```text
Match → MatchRules abstraction
           ↑
           |
        concrete strategies
```

The high-level Match model depends on the abstraction.

## When not to use Strategy

Do not create strategies when the difference is trivial and unlikely to grow.

For example, if the only variation were:

```text
T20 max_overs = 20
ODI max_overs = 50
```

a configuration object could be enough.

Strategy becomes valuable when formats differ in real behavior/rules.

## Strategy vs configuration

Configuration:

```python
MatchConfig(
    max_overs=20,
    max_overs_per_bowler=4,
)
```

is good when differences are mainly data.

Strategy:

```python
class T20Rules:
    def validate_bowler_change(...):
        ...
```

is useful when differences contain behavior.

Often a real system uses both.

## Practical Cricbuzz design

A richer contract could eventually contain:

```text
max_innings_per_team()
max_overs()
max_overs_per_bowler()
validate_innings_completion()
validate_bowler_usage()
calculate_target()
supports_follow_on()
calculate_result()
```

But do not create every possible method before the requirement exists.

Grow the contract as real variation appears.

## Key takeaway

Strategy Pattern solves:

> The same business operation needs multiple interchangeable implementations.

For Cricbuzz:

```text
Match
   |
   v
MatchRules
   |
   +---- T20Rules
   +---- ODIRules
   +---- TestRules
```

The Match does not contain repeated format checks.

It delegates rule differences to the selected strategy.
