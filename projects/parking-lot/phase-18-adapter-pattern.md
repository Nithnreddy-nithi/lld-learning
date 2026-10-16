# Phase 18 — Adapter Pattern

Application wants one PaymentGateway interface while providers expose incompatible SDKs.

```python
class PaymentGateway:
    def charge(self, payment_id, amount):
        raise NotImplementedError

@dataclass(frozen=True)
class PaymentGatewayResult:
    success: bool
    provider_reference: str | None
    failure_code: str | None = None
```

RazorpayPaymentGateway/StripePaymentGateway translate provider calls/statuses/errors into the app contract.

Roles: PaymentService=Client, PaymentGateway=Target, provider adapter=Adapter, provider SDK=Adaptee.

Adapter = compatibility/translation.
