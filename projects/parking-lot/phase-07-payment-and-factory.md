# Phase 07 — Payment + Factory

Separate Payment entity from PaymentProcessor behavior.

Concrete processors: CashProcessor, CardProcessor, UpiProcessor.

```python
class PaymentProcessorFactory:
    @staticmethod
    def create(method):
        if method == "cash":
            return CashProcessor()
        if method == "card":
            return CardProcessor()
        if method == "upi":
            return UpiProcessor()
        raise ValueError("Unsupported method")
```

Factory = which concrete object? Strategy = which algorithm? Payment failure must stop spot release/ticket close.
