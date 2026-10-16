# Phase 19 — Facade Pattern

Facade gives one simple front door to multiple subsystem services.

```text
Controller
   -> ParkingFacade
        -> PricingService
        -> PaymentService
        -> SpotService
        -> TicketService
```

```python
class ParkingFacade:
    def exit_vehicle(self, ticket, spot, method):
        amount = self.pricing.calculate(ticket)
        self.payment.pay(ticket, amount, method)
        self.spot.release(spot)
        self.ticket.close(ticket)
```

Do not dump all business logic into the facade. If an Application Service already gives a clean boundary, another facade may be unnecessary.
