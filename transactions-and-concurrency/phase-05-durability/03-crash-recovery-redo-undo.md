# 3. Crash recovery: redo and undo

## The problem

After a crash, memory is gone. Some data pages reached storage, some did not, and some transactions were unfinished.

Recovery must reconstruct a state that preserves committed transactions without exposing unfinished work as committed.

## Redo

**Redo reapplies logged changes needed to reconstruct database state.**

Example: transfer 42 committed durably, but only Nithin's page was written before the crash. Recovery restores the missing Ravi change from the log.

Real recovery algorithms may redo a broader history of page operations first and resolve transaction outcomes afterward. “Redo only committed records” is a useful intuition for the final outcome, not a universal algorithm.

## Undo

**Undo reverses changes that must not remain as completed transaction effects.**

Suppose transaction 43 deducted ₹100 but never committed. If its effects reached data pages, a recovery design using physical undo can reverse them.

Conceptual journal:

~~~text
Transaction 43:
    Old balance: 800
    New balance: 700
    No commit
~~~

Undo can restore 800.

## Not every engine uses the same undo procedure

Some designs maintain undo records that support rollback and version reconstruction.

Other designs can replay physical changes during recovery but use transaction status and MVCC visibility so uncommitted tuple versions never appear as committed rows. Their cleanup and rollback mechanisms need not physically restore every page to its earlier bytes.

Therefore:
- Redo and undo are recovery concepts.
- Do not claim every engine uses the same redo/undo log.
- The guarantee concerns the valid, visible result, not identical internal steps.

## Three crash positions

| Crash point | Required interpretation |
|---|---|
| Before a durable commit record | No confirmed durable commit; unfinished work must not appear committed |
| After durable commit, before acknowledgement | Transaction can be committed although client does not know |
| After successful durable acknowledgement | Committed result must survive covered failures |

The middle case is especially important for backend retries.

## Avoiding repeated application

Recovery must be safe if another crash interrupts recovery itself. Engines track recovery progress or page/log positions so replay does not blindly repeat business operations.

A **log sequence number**, often LSN, identifies a position in a log. Page metadata can indicate which logged work a page already contains. Exact replay checks vary.

Do not imagine recovery as rerunning “send ₹200” or “send email” at the application layer. It reconstructs database state using engine-defined records.

## Why this matters to backend developers

You normally do not implement recovery. You must still:
- Wait for the correct commit guarantee.
- Treat lost acknowledgement as uncertain.
- Make retries safe through identifiers and idempotency.
- Avoid external effects whose duplication cannot be handled.

Next: [Checkpoints](04-checkpoints.md).
