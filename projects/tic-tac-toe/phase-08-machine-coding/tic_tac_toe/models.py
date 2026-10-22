from dataclasses import dataclass
from enum import Enum

class Symbol(Enum):
    X = "X"
    O = "O"

class GameStatus(Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    WON = "WON"
    DRAW = "DRAW"

@dataclass(frozen=True)
class Position:
    row: int
    col: int

@dataclass(frozen=True)
class Move:
    player_id: str
    position: Position

@dataclass(frozen=True, eq=False)
class Player:
    id: str
    name: str
    symbol: Symbol

    def __post_init__(self):
        if not isinstance(self.id, str) or not self.id.strip():
            raise ValueError("Player ID must be nonempty")
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Player name must be nonempty")
        if not isinstance(self.symbol, Symbol):
            raise ValueError("Player symbol must be a Symbol")

    def __eq__(self, other):
        return self.id == other.id if isinstance(other, Player) else NotImplemented

    def __hash__(self):
        return hash(self.id)

@dataclass(frozen=True)
class MoveResult:
    move: Move
    status: GameStatus
    next_player_id: str | None
    winner_id: str | None
