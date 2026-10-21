# Phase 03 — Assigning Responsibilities

## Objective
Assign each game behavior to the object that has the information and authority to enforce it. Learn Single Responsibility Principle (SRP), cohesion, coupling, encapsulation, ownership, and runtime collaboration before full implementation.

## 1. What is a responsibility?
A responsibility is something an object *knows* or *does*.
- Board knows its size, occupancy, cells.
- Board can validate coordinates and place a symbol.
- Game knows whose turn it is and the lifecycle state.
- Game coordinates an attempted move.
- WinningStrategy knows how a victory is detected.

Do not infer responsibilities from nouns alone. Ask: "Which object owns the necessary information, and which object must protect the invariant?"

## 2. Single Responsibility Principle
A module/class should have one reason to change — not necessarily only one method.

Bad Game class:
- stores grid,
- checks bounds,
- enforces turns,
- scans winning lines,
- prints,
- persists data,
- broadcasts events.

This couples board storage, winning rules, presentation and persistence changes.

Better: Game coordinates; Board owns grid integrity; WinningStrategy checks winning rules; CLI/presenter formats output; persistence and notifications are future adapters.

## 3. Ownership table
| Concern | Owner | Why | Does NOT own |
|---|---|---|---|
| Player ID, name, symbol | Player | Participant identity | Turns, placement, winning |
| Board size, grid, occupancy | Board | Controls grid invariants | Player turn, game status |
| Row/column bounds check | Board | Knows valid range | Turn order |
| Occupied-cell rejection | Board | Owns cell state | Player authorization |
| Symbol placement | Board | Only Board mutates grid | Winner decision |
| Start and restart | Game | Lifecycle owner | Board internal indexing |
| Current player and alternation | Game | Game-specific rules | Grid storage |
| Reject moves before/after gameplay | Game | Knows status | Rendering |
| Reject out-of-turn moves | Game | Knows participants/current turn | Grid storage |
| Win evaluation | WinningStrategy | Encapsulates rule and algorithm | Set GameStatus |
| Mark WON, DRAW and winner | Game | Owns state transitions | Counter implementation |
| Detect board full | Board exposes is_full(); Game chooses DRAW | Board knows occupancy, Game knows precedence | Winning strategy changes status |
| Represent coordinates | Position | Immutable value | Board-specific bounds |
| Represent attempted action | Move | Immutable data | Execute game actions |
| Enum literals | Symbol, GameStatus | Shared domain vocabulary | State transitions |
| ASCII/JSON display | CLI/Presenter | Presentation concerns | Game engine |
| Save/load, REST, events | Future adapters/services | External concerns | Board logic |

## 4. Proposed conceptual interfaces (not full code)
    Player(id, name, symbol)
    Position(row, col)
    Move(player_id, position)

    Board(size)
        is_inside(position)
        is_empty(position)
        place_symbol(position, symbol)
        is_full()
        get_snapshot()

    WinningStrategy
        record_move(symbol, position) -> bool
        reset(size)

    Game(players, size=3, starting_player_id=...)
        start()
        make_move(player_id, row, col)
        get_current_player()
        get_status()
        get_winner()
        get_board()
        restart()

Actual winning-strategy API will be finalized in Phase 5 and Phase 7. With stateful O(1) counters, strategy should only consume an *accepted* board move.

## 5. Successful move collaboration
Initial state: Alice's X occupies (0,0), (0,1); Bob's O occupies (1,0), (1,1); Alice to play (0,2).

1. Client calls Game.make_move("P101", 0, 2).
2. Game checks IN_PROGRESS and P101 is current player.
3. Game constructs Position(0,2), gets Alice's Symbol.X.
4. Game asks Board.place_symbol(Position, Symbol.X).
5. Board validates bounds and empty destination, then commits placement.
6. Game calls WinningStrategy.record_move(X, Position).
7. WinningStrategy increments row/column/diagonal counters and returns true because row 0 is complete.
8. Game stores Alice as winner and sets WON. It does not change current turn to Bob.
9. Presenter renders a snapshot supplied by Game/Board.

If Board rejects the placement, winning counters, turn, status and grid remain unchanged.

Important concurrency qualification: this in-memory synchronous operation does NOT make distributed online requests atomic by itself. That is handled in Phase 12.

## 6. Decision order
- Validate game's lifecycle state.
- Validate player identity and turn.
- Validate board bounds and occupancy before mutating.
- Place accepted symbol.
- Update winning rule.
- If win, set WON and winner.
- Else if board full, set DRAW.
- Else advance player.

Win takes priority over draw when a final square also creates a winning line.

## 7. Encapsulation
Never leak writable board grid. Return a defensive copy, tuple of tuples, or immutable snapshot.
Bad: client modifies game.board.cells[0][0] directly.
Good: Board.place_symbol() enforces its invariants.

The game can own the board but should use its methods rather than modify _cells itself.

## 8. Restart and ownership
Game owns Board and WinningStrategy session state. On restart, it must clear/reset or replace both, as well as winner, status, turn and move count.
Resetting grid alone is wrong: old winning counters would contaminate the new game.
Restart semantics here: restart creates a fresh IN_PROGRESS session, preserving configured players and starter. If desired, a different API can distinguish reset() and start().

## 9. Cohesion
High cohesion means a class's behaviors address one closely related concern.
Board.is_inside, Board.place_symbol and Board.is_full jointly maintain board integrity.
Putting save_to_postgresql() or print_as_html() in Board would reduce cohesion.

## 10. Coupling
Low coupling means Game depends on Board's public operations, not its internal representation.
Good: board.place_symbol(position, symbol).
Bad: board._cells[position.row][position.col] = symbol.
WinningStrategy is a clear extensibility seam. Avoid needless interfaces for tiny immutable values.

## 11. SRP review — reasons to change
- Player: participant representation.
- Board: board storage/placement rules.
- Game: lifecycle and turn coordination.
- WinningStrategy: winning definition/algorithm.
- Position: coordinate representation.
- Move: move data contract.
- Presenter: formatting.

## 12. Why no TurnManager, Validator, CellFactory or GameManager yet?
A class should exist when it owns a distinct meaningful responsibility. Simple alternating turns are coherent inside Game. Board and Game validate different invariants; a universal Validator would obscure ownership.
Introduce turn policies, AI move selection, persistence, game registry and events only when actual requirements motivate them.

## 13. Practice examples
- Out-of-bounds (5,5) on 3x3: Board rejects.
- Alice plays twice: Game rejects.
- New K-consecutive rule: change winning-rule implementation, not Board storage.
- Switch console display to JSON: change Presenter/adapter, not engine.
- Restart after winning: Game coordinates fresh grid and fresh counter state.
- Draw: Board knows full; Game decides terminal DRAW only after winning check.

## 14. Interview explanation
"Game is the aggregate root and coordinates turns and state. Board owns grid integrity and exposes a safe snapshot. Player has stable identity. Move and Position are immutable data. I isolate winning logic into a strategy because it may vary, and I keep rendering outside the engine. That gives high cohesion, controlled coupling and testability without introducing unnecessary managers or factories."

## Next
Phase 04: Relationships and communication — composition vs association, object lifetime, dependencies, who creates whom, and sequence diagrams.
