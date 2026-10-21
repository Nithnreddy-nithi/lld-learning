# Phase 01 — Requirements and System Boundaries

## Goal
Design a two-player Tic-Tac-Toe engine in Python. This phase intentionally contains no application code: clarify behavior before identifying classes.

## Scope
- N x N board, N >= 1, default N = 3. N = 1 is trivial but valid.
- Exactly two human players initially, each with a unique ID, name, and symbol.
- Selected starting player.
- Alternating moves, zero-based row/column indices.
- Win on completed row, column, main diagonal or anti-diagonal.
- Draw when the board is full and no winning line exists.
- Clean restart.
- Unit-testable engine, independent of CLI/HTTP/database.
- Future extensions: AI, arbitrary K-in-a-row, persistence, concurrent requests.

## Clarifications / interview decisions
| Question | Decision |
|---|---|
| Who starts? | Explicitly chosen, default first provided player if not specified |
| Is there a pre-start state? | Yes: NOT_STARTED is useful when start() is explicit |
| What happens on invalid moves? | Raise an appropriate domain exception; board/turn/move count unchanged |
| What happens after WON or DRAW? | No further moves permitted |
| Can both players use same symbol or ID? | No |
| Can a winning move fill the final cell? | Yes: win is evaluated BEFORE draw |
| Board size limit? | Positive integer; consider configurable upper bound if product requires it |
| Does the engine print after moves? | Engine returns/supplies board snapshot; CLI handles printing |
| Does restart preserve players? | Yes; clear game state and restore configured starter |
| Is N=1 allowed? | Yes unless interviewer chooses N >= 3 |

## Functional requirements
1. Construct validated empty board.
2. Register exactly two distinct players.
3. Start game with selected first player.
4. Validate turn, bounds and empty destination.
5. Place symbol atomically with respect to rule checks.
6. Test row, column, both diagonals after successful move.
7. Set WON and winner when a full line is formed.
8. Otherwise, set DRAW if the board is full.
9. Otherwise, advance turn.
10. Disallow moves outside IN_PROGRESS.
11. Restart without reusing previous mutable board state.
12. Expose read-only board, status, current player and winner.

## Critical invariants
- Board has N rows with N cells per row.
- Every cell contains empty or exactly one participant's symbol.
- Player IDs and symbols are unique.
- Only active player can move.
- A successful move fills exactly one empty cell.
- Failed moves have no side effects.
- Terminal states prohibit moves.
- Restart resets status, winner, turn and move count.

## Game lifecycle
NOT_STARTED --start()--> IN_PROGRESS
IN_PROGRESS --valid non-terminal move--> IN_PROGRESS (switch active player)
IN_PROGRESS --winning move--> WON
IN_PROGRESS --full board without winner--> DRAW
WON or DRAW --restart()--> IN_PROGRESS with a fresh empty board and configured starter.

If restart() means reset only, an alternate API can separate reset() and start(); select one contract and document it.

## Move-processing order
1. Ensure game is IN_PROGRESS.
2. Ensure caller is current player.
3. Validate row/column bounds and destination vacancy.
4. Apply move.
5. Evaluate win from the last accepted move.
6. If win, set winner and WON.
7. Else if full, set DRAW.
8. Else switch active player.
9. Return a result/snapshot; presentation layer prints board.

## Acceptance tests
- Valid first move is accepted.
- Same player cannot move twice.
- Occupied and out-of-range coordinates reject without side effects.
- Row, column, main diagonal and anti-diagonal wins work for N x N.
- Full board without winner is DRAW.
- Last empty square win resolves WON, not DRAW.
- Moves before start and after terminal state reject.
- Duplicate player ID or symbol rejects at initialization.
- Restart clears board, move history/counters, winner and status appropriately.
- Two independent Game instances do not share state.

## Nonfunctional / design expectations
- Separate board storage, turn/lifecycle coordination, and winner evaluation.
- Prefer composition over inheritance for the initial two human players.
- Don't introduce abstract factories, state pattern or observer without a requirement.
- Target O(1) winner checks for traditional full-row/column/diagonal rules using per-player counters, after O(N^2) board initialization. Store O(N^2) board and O(N) counters (for a fixed two-player count).
- Do not assume O(1) for arbitrary K-in-a-row custom rules; revisit algorithm when extending.

## Interview talking points
- The Game service orchestrates; it should not own raw board indexing and all winning algorithms.
- Separate engine data from rendering, to work with CLI, Django REST Framework and online multiplayer.
- Input validation should fail before mutation; restart must allocate fresh mutable structures.
- Preserve correctness before optimizing winner detection.

## Learning phases
01 Requirements and system boundaries
02 Identify entities, value objects and enums
03 Assign responsibilities
04 Model relationships and communication
05 Class interfaces and diagrams
06 Game lifecycle and state transitions
07 Winning algorithms
08 Python machine coding
09 Tests and edge cases
10 SOLID and refactoring
11 AI, history and custom rules
12 DRF, persistence, concurrency and events

Next: Phase 02 — Object Identification.
