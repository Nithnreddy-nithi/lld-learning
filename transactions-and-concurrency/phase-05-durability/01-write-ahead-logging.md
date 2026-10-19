# 1. Write-ahead logging (WAL)

## Start with the problem

Nithin transfers ₹200 to Ravi.

| Account | Before | After |
|---|---:|---:|
| Nithin | ₹1,000 | ₹800 |
| Ravi | ₹500 | ₹700 |

The database typically modifies pages in RAM. A **page** is a block of stored records. The two accounts may be on different pages.

Suppose Nithin's updated page reaches storage, Ravi's page does not, and power fails. Table files alone can contain only part of the transfer.

The database needs persisted information from which to recover the correct outcome.

## What WAL means

**Write-ahead logging persists necessary recovery records before the corresponding changed data pages are written to their final locations.**

Conceptually:

~~~text
Transaction 42:
    Change Nithin balance from 1000 to 800
    Change Ravi balance from 500 to 700
    COMMIT
~~~

Real logs can record low-level page changes rather than readable SQL or complete before-and-after values. This is an illustration, not a universal log format.

## A durable commit step by step

1. Execute the updates in memory and generate log records.
2. Generate the transaction's commit record.
3. Flush the required log through that commit record to persistent storage.
4. Confirm success to the application.
5. Write changed data pages to their final locations over time.

Some data pages may be written before commit. That is compatible with WAL if the necessary log records become durable first and recovery can handle unfinished work.

Two rules matter:

- **Required log records before their changed data page.**
- **Durable commit records before acknowledging a durable commit.**

## Recovery after a crash

Suppose the commit record is durable but Ravi's new page is missing.

Recovery reads the log, recognizes the committed transaction, and reapplies required changes not present in the data files.

Reapplying logged work is called **redo**. The result becomes ₹800 and ₹700.

Unfinished transactions must not become visible as committed work; engines handle them through their recovery and visibility design. The next recovery lesson explains why “every engine simply reverses every uncommitted page” would be inaccurate.

## Why not write every data page before commit?

A transaction can change many table and index pages scattered across storage. Logs are generally append-oriented, making sequential persistence efficient. A small durable record can be enough to recover larger changes.

WAL therefore supports correctness while allowing efficient page writing.

## What WAL does not provide alone

- It cannot restore a destroyed disk if the only log and data copies were on it.
- It cannot make an unflushed RAM buffer durable.
- It does not undo an already sent email.
- It is not automatically a complete backup.
- It does not tell the client whether a lost commit response meant success or failure.

## Check your understanding

If COMMIT was durably recorded but the table page was not written, is the transaction necessarily lost? No: recovery can redo it.

Next: [Flushing](02-flushing-and-fsync.md).
