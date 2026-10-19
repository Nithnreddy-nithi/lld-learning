# 4. Checkpoints

## The problem: how much log must recovery inspect?

Imagine a database has been running for months. Replaying every log record from the day it was created would be expensive.

A **checkpoint** records recovery progress and coordinates persistence of relevant database state, allowing recovery to use an appropriate later starting point.

Exact checkpoint contents and rules differ by engine.

## A simplified example

Treat these as illustrative log positions:

| Position | Event |
|---|---|
| 100 | Earlier changes |
| 200 | Earlier changes |
| 300 | Checkpoint's associated recovery position |
| 400 | New transfer |
| 500 | Another committed update |
| 550 | Crash |

The checkpoint tells recovery enough about persisted state and outstanding work to avoid starting at position 0. Recovery examines the required log from its designated recovery starting position.

The starting position can precede the final checkpoint record. Do not assume “find the latest checkpoint record and replay only bytes after it” is universally correct.

## What happens during a checkpoint?

Conceptually, an engine may:
1. Identify a checkpoint/recovery position.
2. Write necessary dirty pages and coordinate required log persistence.
3. Record checkpoint metadata durably.
4. Use that metadata during recovery.

A **dirty page** is a memory page modified since its stored version was written. “Dirty” does not mean corrupt.

Many engines perform checkpoints gradually while transactions continue. These are often described as fuzzy or non-blocking checkpoint designs. A checkpoint need not freeze all writes.

## Does a checkpoint commit transactions?

No.

COMMIT decides a transaction's outcome. A checkpoint manages database persistence and recovery progress.

A transaction may already be durable through its log even when its data pages have not reached their final files.

## Can old logs now be deleted?

Only when all consumers no longer need them. Logs may still be required for:
- Crash recovery.
- Replicas that are behind.
- Backup recovery and archiving.
- Other engine-specific consumers.

Checkpoint completion alone is not a safe manual log-deletion instruction.

## Frequency trade-off

| More frequent checkpoints | Less frequent checkpoints |
|---|---|
| Can reduce required crash-recovery work | Can increase recovery work |
| Can create more checkpoint write activity | Can spread or defer some page-writing work |
| May affect latency depending on design | Can increase retained log requirements |

These effects depend on implementation and tuning. Checkpoint frequency is not a substitute for durable commit flushing.

## SDE1 takeaway

**WAL makes recovery possible; checkpoints help make recovery manageable.** A checkpoint is neither a user transaction nor a backup.

Next: [Incomplete page writes](05-torn-page-protection.md).
