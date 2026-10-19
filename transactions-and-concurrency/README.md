# Transactions and concurrency — SDE1 backend learning

A language- and framework-independent course for Nithin. Read one lesson at a time. Examples use small numbers and explain the problem before the solution.

This folder preserves the material taught in our conversation: transaction foundations, boundaries, autocommit, every ACID property, six concurrency anomalies, four isolation levels, and the WAL lesson. It also expands **all ten durability techniques** into individual lessons.

The original 19-part SDE1 roadmap is preserved in [ROADMAP.md](ROADMAP.md). Roadmap topics beyond the lessons below remain future study; a roadmap entry is not presented as an already completed lesson.

## Phase-based reading order

| Phase | Material |
|---|---|
| [01 — Transaction foundations](phase-01-foundations/README.md) | Transactions, BEGIN/COMMIT/ROLLBACK, boundaries, autocommit, business failures |
| [02 — ACID](phase-02-acid/README.md) | Atomicity, consistency, isolation, durability and their differences |
| [03 — Read phenomena and write anomalies](phase-03-concurrency-anomalies/README.md) | Dirty read, non-repeatable read, phantom read, read skew, lost update, write skew |
| [04 — Isolation levels](phase-04-isolation-levels/README.md) | Read Uncommitted, Read Committed, Repeatable Read, Serializable, retries |
| [05 — Durability techniques](phase-05-durability/README.md) | Ten complete lessons from WAL to backups and point-in-time recovery |

## Important conventions

- SQL syntax and defaults vary by database and driver. Examples illustrate concepts unless explicitly labelled with a database.
- Python blocks labelled pseudocode illustrate control flow; they are not a ready-to-run database library.
- Money examples use whole rupees for clarity. Production systems normally use integer minor units or an appropriate exact decimal type, not binary floating-point.
- Ordinary snapshot reads, locking reads, and writes can follow different rules.
- A successful SQL statement can affect zero rows. Check affected-row counts when correctness depends on finding a record.
- A transaction does not automatically make application logic or concurrent interactions correct.
- Logs, replication, and backups solve different failure problems. They complement one another.
- None of the examples sends real payments or emails.

## What to practice

Explain and eventually implement safe transfers, inventory decrements, seat booking, unique record creation, version-based updates, and duplicate-request handling. For each, ask what happens when requests overlap, the process crashes, or the client retries.

## Documentation for further reading

These are reference links, not claims that the SQL exercises have been executed against every engine:

- [PostgreSQL transaction isolation](https://www.postgresql.org/docs/current/transaction-iso.html)
- [PostgreSQL WAL introduction](https://www.postgresql.org/docs/current/wal-intro.html)
- [PostgreSQL reliability and WAL configuration](https://www.postgresql.org/docs/current/runtime-config-wal.html)
- [PostgreSQL continuous archiving and PITR](https://www.postgresql.org/docs/current/continuous-archiving.html)
- [MySQL InnoDB transaction model](https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-model.html)
- [MySQL InnoDB doublewrite buffer](https://dev.mysql.com/doc/refman/8.4/en/innodb-doublewrite-buffer.html)
