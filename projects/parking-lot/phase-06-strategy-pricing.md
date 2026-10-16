# Phase 06 — Pricing Strategy

Pricing can vary: hourly, weekend, lost ticket, event/surge.

```python
class PricingStrategy:
    def calculate_fee(self, ticket, exit_time):
        raise NotImplementedError
```

The exit workflow depends on this abstraction rather than a giant conditional. Prefer returning a Money value object, not float. Use Strategy for a real policy/algorithm variation axis.
