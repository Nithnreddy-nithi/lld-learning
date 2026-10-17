# Phase 08 — Factory Pattern

## Goal

Understand why factories exist, when to use them, and the difference between:

- Simple Factory
- Factory Method
- Abstract Factory

We will use the Cricbuzz-like system to make the differences concrete.

---

## 1. Why do we need a factory?

In Phase 7, Match depended on a strategy:

```text
Match
  |
  v
MatchRules
  |
  +-- T20Rules
  +-- ODIRules
  +-- TestRules
```

The remaining question is:

> Who creates the correct MatchRules object?

Without a factory, callers may do:

```python
if match_format == MatchFormat.T20:
    rules = T20Rules()
elif match_format == MatchFormat.ODI:
    rules = ODIRules()
elif match_format == MatchFormat.TEST:
    rules = TestRules()
```

If this construction logic appears in controllers, services, commands, tests, or jobs, duplication grows.

A factory centralizes object creation.

---

## 2. Simple Factory

A Simple Factory is just one object/function that decides which concrete object to construct.

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

        raise ValueError("Unsupported match format")
```

Usage:

```python
rules = MatchRulesFactory.create(MatchFormat.T20)
match = Match(rules)
```

### What problem did it solve?

Before:

```text
Controller knows T20Rules
Service knows ODIRules
Job knows TestRules
Tests duplicate construction
```

After:

```text
Controller / Service
        |
        v
MatchRulesFactory
        |
        v
concrete strategy
```

The caller asks for:

```text
rules for T20
```

instead of knowing exactly how to construct them.

---

## 3. Is Simple Factory a GoF pattern?

Strictly speaking, **Simple Factory is not one of the original GoF design patterns**.

But it is extremely common and useful.

Think of it as:

```text
centralized conditional object creation
```

This is often all you need.

---

## 4. When Simple Factory is enough

Use it when:

- one place chooses among concrete implementations
- construction is straightforward
- callers should not know concrete classes
- you do not need subclass-based creation hooks

For our Cricbuzz rules, Simple Factory is enough initially.

---

## 5. Factory Method

Factory Method is different.

The key idea is:

> A parent class defines the creation workflow, but subclasses decide which concrete object gets created.

Example:

```python
from abc import ABC, abstractmethod


class MatchCreator(ABC):

    def create_match(self):
        rules = self.create_rules()

        return Match(rules=rules)

    @abstractmethod
    def create_rules(self):
        pass
```

Now concrete creators:

```python
class T20MatchCreator(MatchCreator):

    def create_rules(self):
        return T20Rules()
```

```python
class ODIMatchCreator(MatchCreator):

    def create_rules(self):
        return ODIRules()
```

```python
class TestMatchCreator(MatchCreator):

    def create_rules(self):
        return TestRules()
```

Usage:

```python
creator = T20MatchCreator()

match = creator.create_match()
```

Here:

```text
create_match()
```

is the common workflow.

But:

```text
create_rules()
```

is delegated to subclasses.

That is Factory Method.

---

## 6. Why is it called Factory Method?

Because the varying creation point is a **method** that subclasses override.

```text
MatchCreator
   |
   +-- create_match()
   |
   +-- create_rules()   ← factory method
```

Concrete subclass decides:

```text
T20MatchCreator
   create_rules() → T20Rules
```

So the factory decision happens through polymorphism instead of one `if/elif` block.

---

## 7. Simple Factory vs Factory Method

### Simple Factory

```python
MatchRulesFactory.create(format)
```

internally:

```text
if T20 → T20Rules
if ODI → ODIRules
if TEST → TestRules
```

One factory decides everything.

### Factory Method

```text
T20MatchCreator
ODIMatchCreator
TestMatchCreator
```

Each subclass overrides:

```text
create_rules()
```

Creation varies through inheritance/polymorphism.

---

## 8. Which one should we use for Cricbuzz right now?

Simple Factory.

Why?

Because this:

```python
rules = MatchRulesFactory.create(match_format)
```

is simple, readable, and sufficient.

Using Factory Method here would add extra classes:

```text
T20MatchCreator
ODIMatchCreator
TestMatchCreator
```

without enough benefit yet.

Important LLD rule:

> Do not choose the more complicated pattern just because you know it.

---

## 9. What if match creation becomes complex?

Suppose creating a T20 match requires:

```text
T20Rules
T20ScoreCalculator
T20ResultCalculator
T20PowerplayPolicy
```

And Test requires:

```text
TestRules
TestScoreCalculator
TestResultCalculator
FollowOnPolicy
```

Now creation is no longer about one object.

We may need to create a **family of related objects**.

That leads to Abstract Factory.

---

## 10. Abstract Factory

Abstract Factory means:

> Create families of related objects that are designed to work together.

Imagine this interface:

```python
class CricketFormatFactory(ABC):

    @abstractmethod
    def create_rules(self):
        pass

    @abstractmethod
    def create_result_calculator(self):
        pass

    @abstractmethod
    def create_powerplay_policy(self):
        pass
```

Then T20 family:

```python
class T20Factory(CricketFormatFactory):

    def create_rules(self):
        return T20Rules()

    def create_result_calculator(self):
        return T20ResultCalculator()

    def create_powerplay_policy(self):
        return T20PowerplayPolicy()
```

ODI family:

```python
class ODIFactory(CricketFormatFactory):

    def create_rules(self):
        return ODIRules()

    def create_result_calculator(self):
        return ODIResultCalculator()

    def create_powerplay_policy(self):
        return ODIPowerplayPolicy()
```

Now the caller gets a compatible family from one factory.

---

## 11. Why Abstract Factory can matter

Without it, you could accidentally combine incompatible components:

```text
T20Rules
+
ODIPowerplayPolicy
+
TestResultCalculator
```

Abstract Factory groups compatible implementations:

```text
T20Factory
  |
  +-- T20Rules
  +-- T20ResultCalculator
  +-- T20PowerplayPolicy
```

and:

```text
ODIFactory
  |
  +-- ODIRules
  +-- ODIResultCalculator
  +-- ODIPowerplayPolicy
```

---

## 12. Factory Method vs Abstract Factory

This is often confusing.

### Factory Method

Usually one creation method varies through subclassing.

```text
Creator
  |
  +-- create_product()
```

### Abstract Factory

Creates a family of related products.

```text
FormatFactory
  |
  +-- create_rules()
  +-- create_result_calculator()
  +-- create_powerplay_policy()
```

So:

```text
Factory Method
→ one product creation hook

Abstract Factory
→ family of related product creation methods
```

---

## 13. Factory does NOT mean business logic

A factory should mainly construct/configure objects.

Bad:

```python
class MatchFactory:

    def create_match(...):
        ...
        calculate_score()
        publish_websocket()
        complete_match()
```

That is mixing creation with use-case behavior.

Factory responsibility:

```text
construct valid object
choose implementation
wire dependencies
```

Not:

```text
run the whole business workflow
```

---

## 14. Factory and dependency injection

Suppose Match needs:

```python
Match(
    rules=...,
    result_calculator=...,
)
```

The factory can build and inject those dependencies:

```python
class MatchFactory:

    def create(self, match_format):

        rules = MatchRulesFactory.create(
            match_format
        )

        result_calculator = (
            ResultCalculatorFactory.create(
                match_format
            )
        )

        return Match(
            rules=rules,
            result_calculator=result_calculator,
        )
```

The Match receives dependencies; it does not construct them itself.

That improves separation.

---

## 15. Bad dependency direction

Avoid:

```python
class Match:

    def __init__(self, match_format):

        if match_format == MatchFormat.T20:
            self.rules = T20Rules()

        elif match_format == MatchFormat.ODI:
            self.rules = ODIRules()
```

Why?

Because now Match directly knows every concrete implementation.

Better:

```python
rules = MatchRulesFactory.create(match_format)

match = Match(rules)
```

Now Match depends on the MatchRules abstraction.

---

## 16. Factory and OCP

Suppose we add:

```text
T10
```

We can create:

```python
class T10Rules(MatchRules):
    ...
```

and update one construction point.

Match itself does not change.

This isolates object-creation changes.

---

## 17. Registration-based factory

If formats grow a lot, even the factory's if/elif can be replaced with a registry.

```python
class MatchRulesFactory:

    _registry = {}

    @classmethod
    def register(cls, match_format, rules_cls):
        cls._registry[match_format] = rules_cls

    @classmethod
    def create(cls, match_format):
        rules_cls = cls._registry.get(match_format)

        if rules_cls is None:
            raise ValueError("Unsupported format")

        return rules_cls()
```

Register:

```python
MatchRulesFactory.register(
    MatchFormat.T20,
    T20Rules,
)

MatchRulesFactory.register(
    MatchFormat.ODI,
    ODIRules,
)
```

Now creation can be extended without editing a long conditional chain.

But use this only when needed.

---

## 18. Factory vs Strategy

These patterns often work together.

```text
Factory
→ decides WHICH strategy object to create

Strategy
→ performs the varying behavior
```

Example:

```text
MatchFormat.T20
      |
      v
MatchRulesFactory
      |
      v
T20Rules
      |
      v
Match uses T20 behavior
```

Factory solves creation.

Strategy solves behavior.

Do not confuse them.

---

## 19. Factory vs Builder

Another common confusion.

Factory:

```text
Which object/implementation should I create?
```

Builder:

```text
How do I construct one complex object step by step?
```

Example:

```text
Factory
→ choose T20Rules vs ODIRules

Builder
→ construct Match with venue, teams, squad, toss config, officials, etc.
```

We can introduce Builder later if Match construction becomes complex.

---

## 20. Factory mental model

When you see:

```python
if type == A:
    return AImpl()

if type == B:
    return BImpl()

if type == C:
    return CImpl()
```

ask:

> Should object creation be centralized?

If yes, a factory may help.

---

## 21. What should we use in this project?

Current recommendation:

```text
Strategy Pattern
→ MatchRules behavior

Simple Factory
→ select T20Rules / ODIRules / TestRules
```

Do NOT introduce Abstract Factory yet unless we genuinely have families such as:

```text
rules
result calculator
powerplay policy
target calculator
```

that vary together by format.

---

## 22. Interview explanation

A strong answer:

> Match should not construct concrete rule implementations itself. I would use a small factory at the application/composition boundary to translate MatchFormat into a MatchRules strategy. If format-specific construction later expands into families of compatible policies, I would consider an Abstract Factory. I would not introduce that complexity up front.

---

## Key takeaway

```text
Simple Factory
→ centralize creation choice

Factory Method
→ subclass decides which product to create

Abstract Factory
→ create a family of related products
```

For our current Cricbuzz design:

```text
MatchFormat
    |
    v
MatchRulesFactory
    |
    +-- T20Rules
    +-- ODIRules
    +-- TestRules
```

The factory decides what to create.

The strategy decides how the rule behaves.
