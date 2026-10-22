# Phase 07 — Winning Algorithms: O(N) Scan vs O(1) Counters

## Goal

After every **accepted** move, determine whether the mover completed any full row, full column, main diagonal or anti-diagonal on an N × N board. The implementation must be independent of display, turns and GameStatus. Invalid moves must NEVER update winning counters.

## 1. Observe what can change after one move

If an accepted mark was placed at (r,c), any new winning line must include (r,c), because only one previously empty cell changed.

Therefore only these lines need consideration:
- Row r
- Column c
- Main diagonal if r == c
- Anti-diagonal if r + c == N - 1

For N=3, main diagonal positions are (0,0), (1,1), (2,2). Anti-diagonal positions are (0,2), (1,1), (2,0). Center (1,1) belongs to both diagonals. For N=1 the only cell belongs to all four types.

## 2. Approach A — Scan relevant lines

Assume the game has already validated row/col/symbol, accepted and placed the move, and provides the current square board:

```python
from collections.abc import Sequence

def is_winning_move(
    board: Sequence[Sequence[str | None]],
    row: int,
    col: int,
    symbol: str,
) -> bool:
    n = len(board)

    if all(board[row][c] == symbol for c in range(n)):
        return True

    if all(board[r][col] == symbol for r in range(n)):
        return True

    if row == col and all(board[i][i] == symbol for i in range(n)):
        return True

    if row + col == n - 1 and all(
        board[i][n - 1 - i] == symbol for i in range(n)
    ):
        return True

    return False
```

Time O(N) per move: at most four scans of length N. Extra checker space O(1) using generators. Board occupies O(N²). Across at most N² valid moves, total worst-case checker work is O(N³). For an ordinary 3x3 game this simple approach is fine, but requested optimized interface motivates counters.

## 3. Approach B — Separate per-player counters

For each symbol maintain:
- row_counts[symbol][r] — count of that symbol in row r.
- col_counts[symbol][c] — count of that symbol in column c.
- main_diag_counts[symbol] — count on main diagonal.
- anti_diag_counts[symbol] — count on anti-diagonal.

On a valid move at (r,c) by s:
1. Increment row_counts[s][r].
2. Increment col_counts[s][c].
3. If r == c, increment main_diag_counts[s].
4. If r + c == N-1, increment anti_diag_counts[s].
5. Return True if any of these four relevant counts == N.

Do NOT use a single counter for both players; Bob's O cannot count toward Alice's X win.

## 4. Executable Python reference for the strategy

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

class Symbol(Enum):
    X = "X"
    O = "O"

@dataclass(frozen=True)
class Position:
    row: int
    col: int

class WinningStrategy(ABC):
    @abstractmethod
    def validate_move(self, symbol: Symbol, position: Position) -> None:
        pass

    @abstractmethod
    def record_move(self, symbol: Symbol, position: Position) -> bool:
        pass

class StandardWinningStrategy(WinningStrategy):
    def __init__(self, board_size: int):
        if type(board_size) is not int or board_size < 1:
            raise ValueError("Board size must be a positive integer")

        self.n = board_size
        self.row_counts = {symbol: [0] * board_size for symbol in Symbol}
        self.col_counts = {symbol: [0] * board_size for symbol in Symbol}
        self.main_diag_counts = {symbol: 0 for symbol in Symbol}
        self.anti_diag_counts = {symbol: 0 for symbol in Symbol}

    def validate_move(self, symbol: Symbol, position: Position) -> None:
        if not isinstance(symbol, Symbol):
            raise ValueError("Invalid symbol")
        if (
            type(position.row) is not int
            or type(position.col) is not int
            or not 0 <= position.row < self.n
            or not 0 <= position.col < self.n
        ):
            raise ValueError("Invalid position")

    def record_move(self, symbol: Symbol, position: Position) -> bool:
        self.validate_move(symbol, position)
        row, col = position.row, position.col

        self.row_counts[symbol][row] += 1
        self.col_counts[symbol][col] += 1

        if row == col:
            self.main_diag_counts[symbol] += 1
        if row + col == self.n - 1:
            self.anti_diag_counts[symbol] += 1

        return (
            self.row_counts[symbol][row] == self.n
            or self.col_counts[symbol][col] == self.n
            or self.main_diag_counts[symbol] == self.n
            or self.anti_diag_counts[symbol] == self.n
        )
```

The reference demonstrates win detection, not the complete Game or occupancy system. Calling record_move twice for the same accepted cell corrupts counters; the Game/Board layer must guarantee a unique, valid placement and call record_move exactly once.

## 5. Full dry run

Accepted moves:
1. Alice X at (0,0)
2. Bob O at (1,0)
3. Alice X at (0,1)
4. Bob O at (1,1)
5. Alice X at (0,2)

Alice's values by accepted move:
- Move 1: rows [1,0,0], cols [1,0,0], main=1, anti=0; no win.
- Move 2: Alice unchanged (Bob has separate counters).
- Move 3: rows [2,0,0], cols [1,1,0], main=1, anti=0; no win.
- Move 4: Alice unchanged (Bob's center increments BOTH of Bob's diagonal counters).
- Move 5: rows [3,0,0], cols [1,1,1], main=1, anti=1; row 0 == N, Alice wins.

Final:
X X X
O O .
. . .

## 6. Complexity

| Cost | Scan relevant lines | Counter strategy |
|---|---|---|
| Per accepted move winner check | O(N) | O(1) expected |
| Checker initialization | O(1) | O(N) for two players |
| Extra checker memory | O(1) | O(N) for two players |
| Board allocation | O(N²) | O(N²) |
| Entire game winner-check upper bound | O(N³) | O(N²) after initialization |

Counter approach updates at most four counts and compares at most four integers irrespective of N. Dictionary lookups in Python are expected constant time; with two fixed enum members this is a natural choice.

Across an entire game, the board's N² allocation dominates initialization. Winner checking is O(1), but the overall make_move can have other costs outside this component, such as rendering a full N × N board.

## 7. Tests and edge cases

- Row win, column win, main-diagonal win, anti-diagonal win.
- Center square contributes to both diagonal counts.
- N=1 first valid move wins; N=2 works ordinarily.
- Interleaved X/O moves must maintain separate counters.
- Win on the last empty cell has priority over DRAW.
- Occupied, invalid or out-of-turn moves must not call record_move.
- Restart must create a new strategy or clear ALL counters.
- Independent games must not share mutable strategy instances.
- Custom K-consecutive winning rules are not solved in O(1) by full-line counters.

## 8. Trade-offs

For small boards, scanning is simpler and stateless, making undo or fault recovery easier. Counters trade O(N) auxiliary state and stronger synchronization obligations for O(1) detection. If undo is added, decrement the appropriate counters only when a valid accepted move is actually removed, or reconstruct counters from remaining history.

## 9. Failure-atomicity caveat

Board.place_symbol occurs before strategy.record_move. A custom strategy that raises after board placement can leave board and counters inconsistent. The completed engine must define a trusted non-throwing contract on accepted valid moves or provide rollback/recovery. WinningStrategy.validate_move should be side-effect-free and run before placement. This is not a concurrency solution; multi-process moves need synchronization and storage transactions later.

## 10. Interview questions

Q: Why only last move's lines? A: An unchanged line cannot become a new win.

Q: Why O(1)? A: Each accepted move changes at most one row count, one column count and two diagonal counts, followed by four comparisons.

Q: Why maintain per-player counters? A: The win requires N marks of the *same* player.

Q: What if N is even? A: Both diagonal conditions work with no special case; there is no single cell belonging to both diagonals.

Q: Why not check draw first? A: A final-cell winning move is WON, not DRAW.

Q: Does it generalize to K consecutive marks anywhere? A: No, a separate winning algorithm is needed.

## Next Phase

Phase 08: Implement the complete playable Python game, wiring Player, Board, Game, MoveResult, winning strategy, errors, and a CLI with a clean separation between engine and rendering.
