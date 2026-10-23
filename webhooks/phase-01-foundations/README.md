# Phase 1 — Webhook foundations
Simple explanations using a parking lot payment example.

## 1. What is an event?
An event is something that has happened.
Examples: a payment succeeded, a car entered, an order was cancelled.
"Pay this bill" is a request to do something. "Payment succeeded" describes something that already happened.
An event in one system does not automatically inform other systems.

## 2. What is a webhook?
A webhook is an HTTP request sent by one system to another when an event occurs.
HTTP is the communication method used by websites and APIs.
Imagine telling a restaurant: "Call me when my order is ready."
You give it a phone number. With webhooks, you give another system a URL instead.

For your parking lot:
1. Your backend creates a payment with a payment provider.
2. The customer completes the payment.
3. The provider records that the payment succeeded.
4. The provider sends a webhook request to your backend.
5. Your backend verifies it and records the successful payment.
6. Your application can then allow the parking session to proceed through its exit rules.

The provider handles payment. Your application handles parking. The webhook connects the two.

## 3. Why do we need webhooks?
Your database and the payment provider's database are separate.
A successful payment at the provider does not automatically update your Payment table.
A webhook carries the news to your application, even if the customer closes the browser.
It helps your application react without repeatedly asking for updates.

## 4. Webhook versus an ordinary API request
A webhook uses an API endpoint; it is not a separate network protocol.
The difference is why the request is sent.

| Situation | Who starts the request? | Purpose |
| --- | --- | --- |
| Your backend creates a payment | Your backend | Ask the provider to do something |
| Your backend fetches payment status | Your backend | Ask for current information |
| Provider sends a payment webhook | Provider | Tell your backend an event happened |

An API is an interface through which programs communicate.
A webhook is an event-triggered use of an HTTP interface.
Not every webhook must use POST, but POST is common.

## 5. Webhook versus polling
Polling means asking repeatedly.
Your backend asks: "Has payment succeeded?" Then asks again after a few seconds.
A webhook means the provider sends a notification when the event happens.

| Polling | Webhook |
| --- | --- |
| You repeatedly ask for status | The other system sends an update |
| Requests may return unchanged information | Requests are triggered by events |
| Delay depends on the polling interval | Delivery can be quick, but delays still happen |
| Requires a status API | Requires a reachable receiver URL |

Polling is still useful when webhooks are unavailable or when checking for missed updates.
Real systems can use both.

## 6. Webhook versus WebSocket
A WebSocket is a connection kept open so two sides can exchange messages.
It is useful for live browser updates, such as chat or a live parking dashboard.
A webhook is usually a separate HTTP request for each notification.

Example:
- Payment provider to your backend: webhook.
- Your backend to the open browser's live display: WebSocket, if you choose to build that feature.
Webhooks do not require the customer's browser to stay open.

## 7. Webhook versus a message queue
A message queue holds work for a worker to process.
A worker is a separate program that handles background tasks.
Example: after receiving a webhook, your backend can place a task in a queue. A worker then updates records or sends a receipt.
The queue's durability depends on its configuration; merely adding a queue does not guarantee no data loss.

A webhook brings information across an HTTP boundary. A queue helps move work between producers and workers.
They can work together.

## 8. Synchronous versus asynchronous communication
Synchronous: you make a request and wait for its response before continuing that operation.
Example: your backend requests payment details and waits for the provider's response.

Asynchronous: work or notification happens separately, and the result can arrive later.
Example: payment completion is reported later through a webhook.

Important: the webhook delivery itself is still an HTTP request with a response.
The overall workflow is asynchronous because the payment result arrives separately from the earlier payment-creation request.
Asynchronous does not mean instant, parallel, or impossible to fail.

## 9. Event producer and consumer
Producer: the system that creates an event.
Consumer: the system that receives and uses it.

For payment.succeeded:
- Producer: payment provider.
- Consumer: your parking backend.

For parking.session.completed sent to a business customer:
- Producer: your parking backend.
- Consumer: the customer's backend.

These are roles in a particular interaction. The same application can play both roles.

## 10. Webhook sender and receiver
Sender: the system that sends the HTTP request.
Receiver: the system that accepts it at a URL.

Usually the producer is also the sender. Sometimes another delivery service sends the event on the producer's behalf.
The receiver may save the event and let a background worker consume it later.

For the basic payment example:
- Sender: payment provider.
- Receiver: your webhook endpoint.

## 11. Event time versus delivery time
Event time: when something happened.
Delivery time: when the notification reached your backend.

Example:
- 10:00:00 — payment succeeds.
- 10:00:05 — webhook reaches your backend.
The event happened five seconds before delivery.

Delivery may be delayed because of network problems or retries.
Therefore, arrival time is not necessarily event time.
Events may also arrive in a different order from the order in which they happened.

## 12. Endpoint and subscription
An endpoint is a URL that accepts requests.
Example: https://parking.example.com/webhooks/payments/
This is an illustrative URL.

A subscription is a configuration saying which events should be sent to which endpoint.
For example:
- Destination: your payment webhook URL.
- Selected events: payment success and payment failure.

The exact registration process depends on the provider.
Creating a Django URL alone does not tell the provider that the URL exists.

## 13. Push-based communication
Push: "I will tell you when something happens."
Pull: "I will ask you whether something happened."

A webhook is push-based from the sender's point of view.
Polling is pull-based from the receiver's point of view.
"Push" here does not mean a mobile push notification.

## 14. Why webhook delivery can fail
Examples:
- Your server is down.
- The network connection fails.
- The sender uses an incorrect URL.
- Your server takes too long to respond.
- Your application returns an error.
- A certificate or DNS problem prevents connection.

A particularly important case:
1. Your backend receives and processes the event.
2. Its response is lost on the network.
3. The sender cannot tell that processing succeeded.
4. If its policy allows, it retries.
5. Your backend receives the same event again.

Retry means trying delivery again.
Duplicate means receiving the same event more than once.
Do not assume every provider retries, or that every failure is retried. Rules differ.

## 15. Receiving is different from completing business work
There are separate milestones:
1. The HTTP request reaches your server.
2. Your application accepts or stores it.
3. Your application finishes the business work.

Example: your endpoint stores the event and responds successfully. Later, a worker fails while updating the payment.
The delivery was accepted, but business processing is unfinished.

A success response should have a clear meaning in your design. For a reliable background design, it can mean "verified and durably stored for processing."
It should not be mistaken for proof that the parking gate physically opened.

## Complete parking lot example
1. Customer requests to pay a parking bill.
2. Your backend creates a payment at the provider.
3. Customer pays.
4. Provider records a successful payment event.
5. Provider sends the event to your registered endpoint.
6. Your backend verifies the sender and validates the payment details.
7. Your backend safely records the event.
8. Your application processes the event and updates the local payment.
9. Your exit workflow checks the updated payment and applies its exit rules.

Steps 6–8 need careful implementation. Later phases cover signatures, duplicates, background work, and failures.
This phase establishes the meaning of the pieces.

## Common misunderstandings
- A webhook is not a database automatically syncing with another database.
- A webhook does not require an open customer browser.
- Delivery is not guaranteed to be immediate.
- Receiving an event twice must not create two business effects.
- Receiving an HTTP request does not prove who sent it.
- A successful delivery response does not necessarily mean all business work is complete.
- Webhooks, queues, and WebSockets solve different communication needs and can be combined.

## Quick self-check
1. What is the event when a customer finishes paying?
2. Who sends the payment webhook?
3. What URL receives it?
4. How does polling differ from a webhook?
5. Can the webhook arrive after the customer closes the browser?
6. Why might the same event arrive twice?
7. Does storing the event guarantee that the gate opened?

Answers:
1. Payment succeeded.
2. The payment provider, or a delivery service acting for it.
3. Your configured webhook endpoint.
4. Polling repeatedly asks; a webhook sends a notification after an event.
5. Yes. It is a server-to-server request.
6. A retry can happen when the sender does not receive a successful response.
7. No. Storing, processing, and physical actions are separate steps.

## Progress
Phase 1 explained: 15 of 15 foundation topics.
Phases completed in the roadmap: 1 of 17.
Phases remaining: 16.
Next: Phase 2 — HTTP knowledge required for webhooks.
