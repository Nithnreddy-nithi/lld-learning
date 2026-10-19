# 6. Group commit

## The problem: durable flushes can be expensive

Suppose three transactions finish almost together. Each needs its commit record persisted.

If each performs a completely separate durable flush, the storage pays repeated synchronization costs.

**Group commit lets multiple transactions share a log flush while preserving their required durability guarantee.**

## Worked example

Assume the records are in order:

| Transaction | Commit record ends at log position |
|---|---:|
| A | 110 |
| B | 120 |
| C | 130 |

A flush that durably persists the continuous log through position 130 also persists the required records through 110 and 120.

After the flush completes, A, B, and C can each receive success, provided their other commit requirements are met.

They share the expensive persistence operation.

## Step by step

1. Transactions generate their own log and commit records.
2. The engine coordinates transactions waiting for durability.
3. One flush persists the necessary range.
4. Each waiting transaction whose required position is durable is released.

They do not become one transaction. A, B, and C retain independent outcomes and transaction boundaries.

## A performance illustration

Assume, purely for illustration, one flush takes 2 milliseconds.

Three separate serial flushes:
- A: 2 ms.
- B: another 2 ms.
- C: another 2 ms.
- Total storage synchronization time: about 6 ms.

One shared flush can cover all three in roughly one synchronization operation, though actual timing also includes coordination, writes, and queueing.

These are teaching numbers, not a hardware benchmark.

## Does group commit weaken durability?

Not if success waits until each transaction's required log position is durable.

Compare:

| Behavior | Durability |
|---|---|
| Share one flush, acknowledge afterward | Preserves the configured durable-commit guarantee |
| Acknowledge first, flush later | Can lose acknowledged transactions after a crash |

Grouping and asynchronous acknowledgement are different ideas.

## Latency versus throughput

**Latency** is how long one operation takes. **Throughput** is how many operations complete in a period.

Brief batching or natural coordination can improve throughput, but waiting for a batch can affect latency. Engines implement different coordination strategies; some use explicit delay options, while grouping can also arise naturally under load.

## SDE1 takeaway

Group commit is an efficiency technique for durability: **many transactions can share the same persistence work without sharing one business transaction.**

Next: [Reliable storage](07-storage-and-redundancy.md).
