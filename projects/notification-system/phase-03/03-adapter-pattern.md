# Phase 3, Concept 3 — Adapter Pattern

## Goal

Translate incompatible vendor APIs into the stable interface expected by the notification workflow.

## Provider differences

Vendors may use `send_mail`, `messages.create`, or `send`; identifiers may be named `message_id`, `sid`, or `name`; and every SDK exposes different exceptions. These details should not leak into `NotificationService`.

## Stable application contract

```python
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ProviderResult:
    provider_message_id: str
    provider_name: str


class ChannelSender(Protocol):
    def send(
        self,
        destination: str,
        content: RenderedContent,
    ) -> ProviderResult:
        ...
```

## Example adapter

```python
class ProviderDeliveryError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        retryable: bool = False,
    ) -> None:
        self.code = code
        self.message = message
        self.retryable = retryable
        super().__init__(message)


class TwilioSmsAdapter:
    def __init__(self, client, sender_number: str) -> None:
        self._client = client
        self._sender_number = sender_number

    def send(self, destination, content) -> ProviderResult:
        try:
            response = self._client.messages.create(
                from_=self._sender_number,
                to=destination,
                body=content.body,
            )
        except Exception as error:
            raise ProviderDeliveryError(
                code="SMS_PROVIDER_ERROR",
                message=str(error),
            ) from error

        return ProviderResult(
            provider_message_id=response.sid,
            provider_name="twilio",
        )
```

The adapter translates request fields, response fields and error categories.

```mermaid
flowchart LR
    S[NotificationService] --> C[ChannelSender contract]
    C --> A[TwilioSmsAdapter]
    A --> SDK[Twilio SDK]
```

## Error normalization

An adapter can map rate limiting to a retryable application error and an invalid address to a permanent error. Preserve useful diagnostic fields, but never persist secrets or unfiltered provider responses.

## Strategy versus Adapter

| Pattern | Purpose |
|---|---|
| Strategy | Interchangeable delivery behavior |
| Adapter | Translation at an external integration boundary |

One class can play both roles: it is a sender strategy to the workflow and a provider adapter at the boundary.

## Provider replacement

Replacing SendGrid with SES changes the email adapter and startup composition. It must not require rewriting the delivery workflow.

## Exercise and answers

1. An adapter translates application input/output/errors to and from provider forms.
2. `NotificationService` should never read `twilio_response.sid` directly.
3. Vendor exceptions are normalized inside the adapter.
4. Switching vendors changes the concrete adapter and composition.

## Takeaway

> Keep provider peculiarities at the boundary so the application speaks a stable, vendor-neutral language.


