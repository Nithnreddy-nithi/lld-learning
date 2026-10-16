# Cricbuzz-like Live Cricket System — LLD Learning Project

This project is intentionally built in phases. The emphasis is on **reasoning**: requirements → domain model → relationships → behavior → patterns → implementation.

## Current roadmap

```text
Phase 01  Requirements & system boundaries            ✅
Phase 02  Actors, use cases & object discovery         ✅
Phase 03  Entity / Value Object / Enum / Service       ✅
Phase 04  Relationships & ownership                    ✅
Phase 05  Core class state & behavior                  ⏳
Phase 06  Match lifecycle + State pattern              ⏳
Phase 07  Match rules + Strategy pattern               ⏳
Phase 08  Factories                                    ⏳
Phase 09  Team / Squad / Playing XI                    ⏳
Phase 10  Innings modelling                            ⏳
Phase 11  Over + Delivery modelling                    ⏳
Phase 12  Extras + wickets                             ⏳
Phase 13  Scoring engine                               ⏳
...
```

## Core object picture so far

```text
Series
  |
  v
Match ---------------- Venue
  |
  +---- MatchTeam ---- Team
  |        |
  |        +---- Squad / Playing XI ---- Player
  |
  +---- Innings
           |
           +---- Over
                  |
                  +---- Delivery
                         |
                         +---- DeliveryResult
                                |
                                +---- Extras
                                +---- WicketInfo
```

## Guiding questions

For every concept, ask:

1. Does identity matter?
2. What state does it own?
3. What behavior does it own?
4. Who controls its lifecycle?
5. What invariants must always hold?
6. Can it exist independently?
7. Is the relationship itself meaningful enough to become an object?
