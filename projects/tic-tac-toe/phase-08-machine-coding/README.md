# Phase 08 — Complete Tic-Tac-Toe Machine Coding

Python 3.10+; no third-party dependencies.

## Run
From the directory containing tic_tac_toe:

```bash
python -m tic_tac_toe.cli
python -m unittest discover -s tests -v
```

## Project layout
- tic_tac_toe/models.py — Symbol and GameStatus enums; immutable Player, Move, Position, MoveResult.
- tic_tac_toe/errors.py — domain exceptions.
- tic_tac_toe/board.py — validated NxN grid; safe snapshot.
- tic_tac_toe/strategy.py — replaceable winning rule; O(1) accepted-move win detection.
- tic_tac_toe/game.py — orchestrates turns, state, validation, restart.
- tic_tac_toe/cli.py — terminal UI and rendering.
- tests/test_game.py — runnable unittest suite.

## How the machine coding fits the class design
Player is immutable and identity-comparable by id. Position is an immutable pair of zero-based coordinates. Move contains player ID and Position. MoveResult returns accepted move, final GameStatus, next-player ID or winner ID.

Board.__init__ validates size and initializes N rows. Board.is_inside enforces integer indices in [0,N), including rejecting bool. Board.is_empty validates before accessing grid. Board.place_symbol rejects occupied destinations before mutation, increments occupied_count once. Board.is_full compares occupied_count against N*N. Board.get_snapshot produces tuple of tuples, preventing client modification.

StandardWinningStrategy constructs per-symbol row/column counters of length N and diagonal counters. validate_move is side-effect-free. record_move is invoked once after successful board placement. It increments at most four counts and checks whether a relevant count equals N: O(1) per accepted move and O(N) extra space for fixed two players.

Game.__init__ validates exactly two different Player IDs and Symbols, board size, starter membership, and strategy factory. It sets NOT_STARTED, creates independent Board and strategy state. Game.start permits only NOT_STARTED -> IN_PROGRESS. Game.make_move validates state and turn, checks Board vacancy, preflights strategy, places the symbol, updates winning counts, determines WON before DRAW, and only advances turn after a nonterminal successful move. Invalid requests raise domain exceptions and retain current turn/board.

Game.restart constructs a new board and strategy instance before swapping references. It resets winner, move count and current player, preserving the original player objects and configured starter. Its resulting state is IN_PROGRESS.

Unexpected custom-strategy failures are not ordinary invalid moves. The implementation aborts the current round and reinitializes session state to NOT_STARTED before raising. This is a simple failure policy, not a distributed transaction or general exception-safety guarantee for adversarial factories.

CLI contains no game rules: it renders snapshots, gets user input, displays game results and lets users restart. This isolation allows eventual DRF/GUI adaptation.

## Sample Python use

```python
from tic_tac_toe import Game, Player, Symbol
alice = Player("a", "Alice", Symbol.X)
bob = Player("b", "Bob", Symbol.O)
game = Game([alice, bob])
game.start()
result = game.make_move("a", 0, 0)
print(result.status, result.next_player_id)
print(game.get_board())
```

## Complexity
- Board initialization: O(N²) time and memory.
- Strategy initialization: O(N) auxiliary time and memory for two players.
- Accepted move with winner check: expected O(1).
- Creating a complete board snapshot for display: O(N²).
- Restart: O(N²) to create the board.
- Full game: at most N² accepted moves.

## Interview notes
No Cell class, manager, State pattern, database or event bus: those do not yet have justified responsibilities. Game composes Board; players are independent; strategy is replaceable. Multi-thread/process requests still need synchronization in Phase 12.

## Tests
Run the standard-library unittest suite. Covers state, turn, invalid moves, row/column/diagonal wins, draw, restart, N=1, invalid dimensions, read-only snapshot and independence of games.

## Next
Phase 09 — thorough tests, boundary-value analysis, mock/fake strategies, CI.
