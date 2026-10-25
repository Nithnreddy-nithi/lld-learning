# Notification System — Low-Level Design Learning Project

This project develops a notification system incrementally. The emphasis is not only on the final class diagram or code, but on the reasoning that turns an ambiguous product statement into an implementable design.

## Current scope

Phase 1 establishes what the system must do. Phase 2 turns that behavior into a small object model with clear ownership, responsibilities, and dependency boundaries.

- [Concept 1 — Requirement clarification](phase-01/01-requirement-clarification.md)
- [Concept 2 — Functional requirements and use cases](phase-01/02-functional-requirements.md)

### Phase 2 — Object modeling

- [Concept 1 — Identify core objects](phase-02/01-core-objects.md)
- [Concept 2 — Relationships and ownership](phase-02/02-relationships-and-ownership.md)
- [Concept 3 — Responsibilities and method placement](phase-02/03-responsibilities-and-method-placement.md)
- [Concept 4 — Interfaces, orchestration, and composition](phase-02/04-interfaces-orchestration-and-composition.md)

### Phase 3 — Design patterns

- [Concept 1 — Strategy for channel behavior](phase-03/01-strategy-pattern.md)
- [Concept 2 — Factory for sender selection](phase-03/02-factory-pattern.md)
- [Concept 3 — Adapter for provider integration](phase-03/03-adapter-pattern.md)
- [Concept 4 — Observer through domain events](phase-03/04-observer-and-domain-events.md)

### Phase 4 — Persistence and transaction boundaries

- [Concept 1 — Relational schema](phase-04/01-database-schema.md)
- [Concept 2 — Repository pattern](phase-04/02-repository-pattern.md)
- [Concept 3 — Transactions and Unit of Work](phase-04/03-transactions-and-unit-of-work.md)
- [Concept 4 — Transactional outbox](phase-04/04-transactional-outbox.md)

## Confirmed Phase 1 decisions

| Question | Decision | Design consequence |
|---|---|---|
| One recipient or many? | Multiple recipients | One request may expand into several recipient deliveries. |
| Are templates required? | Yes | Callers may identify a reusable template and provide variable data. |
| Initial channels | Email, SMS, and push | The requirements remain channel-neutral while allowing channel-specific addresses. |
| Delivery result | Track per recipient and channel | A batch can be partially successful. |

These are learning-scope decisions, not claims that every production system must make the same choices.

## Progress tracker

| Phase | Concept | Status | Evidence |
|---|---|---:|---|
| 1 | 1. Clarify the problem and scope | Complete | [Notes, examples, diagrams, and exercises](phase-01/01-requirement-clarification.md) |
| 1 | 2. Derive functional requirements and use cases | Complete | [Requirements, flows, examples, and exercises](phase-01/02-functional-requirements.md) |
| 2 | 1. Identify core objects | Complete | [Entities, values, services, and enums](phase-02/01-core-objects.md) |
| 2 | 2. Define relationships and ownership | Complete | [Lifecycle ownership and references](phase-02/02-relationships-and-ownership.md) |
| 2 | 3. Place responsibilities and methods | Complete | [Cohesive behavior and state transitions](phase-02/03-responsibilities-and-method-placement.md) |
| 2 | 4. Define interfaces and compose the workflow | Complete | [Ports, orchestration, test doubles, and composition](phase-02/04-interfaces-orchestration-and-composition.md) |
| 3 | 1. Apply Strategy to channel delivery | Complete | [Interchangeable sender behavior](phase-03/01-strategy-pattern.md) |
| 3 | 2. Apply Factory to sender selection | Complete | [Centralized strategy selection](phase-03/02-factory-pattern.md) |
| 3 | 3. Apply Adapter to provider APIs | Complete | [Vendor-neutral integration boundary](phase-03/03-adapter-pattern.md) |
| 3 | 4. Publish delivery domain events | Complete | [Observer, handlers, and event boundaries](phase-03/04-observer-and-domain-events.md) |
| 4 | 1. Design the relational schema | Complete | [Tables, constraints, versioning, and indexes](phase-04/01-database-schema.md) |
| 4 | 2. Map storage through repositories | Complete | [Repository contracts and row mapping](phase-04/02-repository-pattern.md) |
| 4 | 3. Define transaction boundaries | Complete | [Unit of Work and concurrency](phase-04/03-transactions-and-unit-of-work.md) |
| 4 | 4. Publish events reliably | Complete | [Transactional outbox and relay](phase-04/04-transactional-outbox.md) |
| 5+ | Asynchronous delivery, reliability, observability, and APIs | Not started | To be documented when each phase is completed |

## Phase 1 outcome

By the end of these two concepts, we can state the core contract in one sentence:

> Accept a notification request that names a template, supplies its data, selects one or more channels, and targets one or more recipients; validate it, render channel-appropriate content, attempt each recipient-channel delivery, and return or record the result of every attempt.

Phase 1 deliberately does **not** settle implementation choices such as Celery versus another worker, a particular database schema, or a vendor SDK. Those choices should follow the requirements instead of silently becoming requirements themselves.

## Phase 2 outcome

Phase 2 separates one business request from its many recipient-channel delivery attempts. Domain objects protect their own invariants, focused services render and send content, and repository/sender protocols keep the use case independent of infrastructure choices.

## Phase 3 outcome

Phase 3 applies patterns only where behavior genuinely varies: Strategy encapsulates channel delivery, Factory selects a configured strategy, Adapter contains vendor-specific translation, and domain events notify independent observers after important delivery transitions.

## Phase 4 outcome

Phase 4 stores requests, versioned templates and delivery attempts without losing their lifecycle distinctions. Repositories map domain objects to storage, a Unit of Work protects related local changes, and an outbox makes committed events recoverable for asynchronous publication.


