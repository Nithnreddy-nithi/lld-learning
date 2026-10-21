# Phase 04 — Object Relationships and Communication

## Objective
Understand association, aggregation, composition, dependency, object creation, lifetime, and communication in Tic-Tac-Toe.

## Association
Game references two Player objects; players exist independently and do not require back-references to Game.
Example: alice = Player('P101','Alice',Symbol.X); bob = Player('P102','Bob',Symbol.O); game = Game([alice,bob]).
Storing a reference is an association; it does not imply lifecycle ownership.

## Shared aggregation
An optional whole-part way to describe Game with Players. UML uses an open diamond on Game.
Player Alice can participate in G001 and G002. Deleting a game does not conceptually delete the player.
UML shared aggregation is weakly defined: ordinary association is often preferable.

## Composition
Game exclusively owns a Board. UML uses a filled diamond on Game.
Each game creates its own Board and mutable grid. game1.board is game2.board must be False even if both games share the same Player instances.
Board's lifecycle is controlled by Game; a restart replaces the active Board.
Composition does not imply immediate Python deallocation: references to a former board can keep it alive.

## Dependency
Game relies on a WinningStrategy contract. A retained strategy field also represents an association.
The default StandardWinningStrategy may use row/column/two diagonal counters for O(1) win detection after a valid move.
Such mutable counters MUST be unique per game/round. Inject a strategy factory or provision a new instance when the game starts or restarts.
Changing to K-consecutive winning conditions should primarily require a new strategy, not replacing Game orchestration.

## Ownership and construction
- Application/CLI constructs Players and the Game.
- Game creates its own Board and session-winning state, optionally through a passed-in rule factory.
- Game owns current turn, winner and game status.
- Board owns cells, bounds validation, occupancy and placement.
- Strategy owns winning-rule algorithm/counters, not status transitions.
- Move carries player ID and Position; Position is immutable coordinates.
- Presenter/CLI renders a defensive board snapshot; core Game and Board do not print.

## Python conceptual examples
    class Board:
        def __init__(self, size):
            self.size = size
            self._cells = [[None for _ in range(size)] for _ in range(size)]

    class Game:
        def __init__(self, players, board_size=3):
            self.players = tuple(players)
            self.board_size = board_size
            self._board = Board(board_size)

    game1 = Game([alice, bob])
    game2 = Game([alice, bob])
    assert game1._board is not game2._board

Optional injectable strategy factory:
    game = Game([alice, bob], board_size=3, winning_strategy_factory=StandardWinningStrategy)

## Relationships
| From | To | Type | Reason |
|---|---|---|---|
| Game | Player | Association; possible shared aggregation | Independent participant identity |
| Game | Board | Composition | Exclusive state ownership |
| Game | WinningStrategy | Dependency and stored association | Rule substitution; fresh state per game |
| Player | Symbol | Value field | Player's mark |
| Move | Position | Value containment | Move coordinates |
| Board | Symbol | Stored value | Occupied square |
| Game | GameStatus | Enum field | Lifecycle |

## UML text
Game o---- Player (two independent players)
Game *---- Board (one composed board)
Game ----> WinningStrategy (interface dependency)
StandardWinningStrategy --|> WinningStrategy (implementation)
Move *---- Position (immutable component)

## Object lifetime
| Object | Created when | Lifetime |
|---|---|---|
| Player | Before game | May participate in many sessions |
| Game | Session starts | Session lifetime |
| Board | Initialization/restart | One active round |
| WinningStrategy state | Initialization/restart | One active round |
| Move / Position | Action requested | As long as referenced |
| Enum values | Defined by enum class | Shared constants |

## Collaboration for Alice's winning move (0,2)
1. Client calls Game.make_move('P101', 0, 2).
2. Game rejects if status is not IN_PROGRESS or it is not Alice's turn.
3. Game constructs Position(0,2) and asks Board to place X.
4. Board checks bounds and vacancy before writing to the grid.
5. On accepted placement only, Game calls WinningStrategy.record_move(X, position).
6. Strategy updates its counters, returns win=True.
7. Game sets winner=Alice and status=WON. It does not advance to Bob.
8. Client receives result and displays immutable board snapshot.
Invalid moves leave board, winning counters, turn and status unchanged.
A custom strategy throwing after placement needs an explicit atomicity/error-recovery contract; in-memory synchronous code does not automatically guarantee distributed atomicity.

## Restart
Game coordinates fresh Board, fresh winning-rule counters, cleared winner and move count, restored configured first player, and IN_PROGRESS status.
Old Board references may physically remain alive if other Python objects refer to them, but they are no longer part of the restarted session.

## Common errors
- Sharing mutable Board or stateful strategy instances between games.
- Letting Player mutate Board directly.
- Exposing a writable grid through get_board().
- Creating unnecessary bidirectional references.
- Confusing UML ownership with Python garbage-collector timing.
- Adding factories/managers/event buses without a requirement.

## Practice
1. Create two Games using the same Players and prove their Boards are distinct.
2. Explain why an old Board reference may live after its Game is deleted.
3. Describe how immutable snapshots protect Board invariants.
4. Sketch creation of a new strategy instance per round.
5. Draw the failed occupied-cell move sequence and explain why strategy is never called.

## Next
Phase 05: precise class APIs, constructor parameters, exception behavior, class diagram and strategy contract.