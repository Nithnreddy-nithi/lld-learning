# Phase 02 — Object Identification

## Goal
Discover appropriate objects from requirements, distinguish identity and value, and avoid needless abstractions.

## Discover candidate objects
From "two players alternate placing symbols on an N x N board; after each move check win/draw; allow restart":
- Nouns: Game, Player, Board, Cell, Move, Position, Symbol, GameStatus, WinningRule.
- Actions: start, restart, validate move, place symbol, change turn, check winner, detect draw.

A noun is only a candidate class. Ask whether it has identity, related state, meaningful behavior, a distinct responsibility, or useful testability.

## Entity vs value object
Entity identity persists despite attribute changes. Two people named Alex are different players when player IDs differ. Two sessions with the same players are separate Games.

Value object equality is based on values, generally immutable. Position(row=1,col=2) equals another position with those values.

## Entities
### Player
- Fields: id, name, symbol.
- Identity: unique player ID.
- Different players can have same names, but within a game must have unique IDs and symbols.
- Do not conflate player identity with move-selection strategy (human versus computer).

### Game
- Fields: game_id (useful for APIs/multiple games), players, board, current_player, status, winner, move_count, winning_rule.
- Owns gameplay lifecycle and is the aggregate root.
- Independent Game instances must never share mutable board or counter state.

## Board — stateful domain component
- Fields: size, private N x N grid, optionally occupied_count.
- Operations: check bounds, validate empty cell, place symbol, provide defensive read-only snapshot.
- Its lifetime is owned by the game; it does NOT need a global Board ID.
- It does NOT decide whose turn it is, print the board, or determine game status.
- A separate Cell class is not required yet: a grid of optional symbols suffices.

## Value objects
### Position
Immutable row and col, no ID. A frozen Python dataclass is suitable.
Example: Position(0,2) == Position(0,2).
Board checks whether coordinates are inside its specific size; a Position alone cannot know board boundaries.

### Move
Immutable player_id and Position; represents proposed/accepted action *data*.
It needn't have an independent ID in the initial version.
If persisting a history of separate move occurrences, introduce MoveRecord with sequence/ID, timestamp and game reference.

## Enums
- Symbol = X, O.
- GameStatus = NOT_STARTED, IN_PROGRESS, WON, DRAW.
Explicit game.start() motivates NOT_STARTED prior to IN_PROGRESS.
If custom player counts/symbols are introduced later, reconsider fixed Symbol enum.

## Winning-rule strategy
Keep win-checking separate from Game's coordination.
- WinningStrategy is a possible replaceable boundary.
- StandardWinningStrategy supports full row, column, main diagonal and anti-diagonal.
- For O(1) detection per accepted move, a stateful strategy may update per-player row, column and two diagonal counters.
- Counters reset on a new game; with fixed two players, they need O(N) auxiliary memory.
- Board needs O(N^2) memory.
- A stateless strategy that scans a line takes O(N) per move; do not inaccurately claim O(1).
- Custom K-in-a-row may need different algorithms and complexity.

## Relationships
- Game associates with exactly two Players.
- Game composes one Board.
- Game delegates win evaluation to a WinningStrategy.
- Player carries Symbol.
- Move carries player ID and a Position.
- Board holds optional Symbols.
- Game owns current turn, status and winner.

## Avoid premature classes
Do not automatically introduce Cell, factories, GameManager, event publisher, persistence repository or computer player. Add them when behavior requires them.
Class != entity; stateful Board is not necessarily an independent entity.
An abstraction is justified by responsibility, not by its name.

## Suggested code examples (conceptual only)
    @dataclass(frozen=True)
    class Position:
        row: int
        col: int

    @dataclass(frozen=True)
    class Move:
        player_id: str
        position: Position

    class Symbol(Enum):
        X = "X"
        O = "O"

    class GameStatus(Enum):
        NOT_STARTED = "NOT_STARTED"
        IN_PROGRESS = "IN_PROGRESS"
        WON = "WON"
        DRAW = "DRAW"

## Interview questions and answers
1. Why is Player an entity? Stable ID distinguishes participants even if names are equal.
2. Why is Position a value? Coordinates entirely determine meaning; no ID needed.
3. Is Board an entity? It is an encapsulated stateful component owned by Game and needs no independent identity in scope.
4. Why not create Cell? No cell-specific behavior beyond occupancy.
5. Why separate WinningStrategy? Custom winning rules should not force rewriting Game.
6. Is every strategy stateless? No: O(1) standard win detection can use counters updated per move.
7. What if a final-cell move wins? Check win before draw.
8. Does the core engine print? No; display belongs to a CLI/presentation adapter.

## Phase 03 preview
Assign exact responsibilities: turn validation and state transitions to Game; bounds and placement to Board; winner evaluation to strategy; representation to value objects/enums; printing to presentation.
