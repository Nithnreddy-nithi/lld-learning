# Phase 17 — Dependency Injection + Wiring

Supply collaborators from outside.

```python
class PaymentService:
    def __init__(self, gateway):
        self.gateway = gateway
```

Composition Root creates concrete repos, strategies, adapters, event handlers, and services.

DIP = dependency direction principle.
DI = construction/supply technique.

Do not hide dependencies in a Service Locator.
