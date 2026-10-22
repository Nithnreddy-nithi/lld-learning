from abc import ABC, abstractmethod
from .errors import InvalidPositionError
from .models import Position, Symbol

class WinningStrategy(ABC):
    @abstractmethod
    def validate_move(self, symbol: Symbol, position: Position) -> None:
        """Pure preflight: must not mutate state."""

    @abstractmethod
    def record_move(self, symbol: Symbol, position: Position) -> bool:
        """Record precisely one accepted move; return whether it wins."""

class StandardWinningStrategy(WinningStrategy):
    def __init__(self, board_size: int) -> None:
        self._n = board_size
        self._rows = {s: [0] * board_size for s in Symbol}
        self._cols = {s: [0] * board_size for s in Symbol}
        self._main = {s: 0 for s in Symbol}
        self._anti = {s: 0 for s in Symbol}

    def validate_move(self, symbol: Symbol, position: Position) -> None:
        if not isinstance(symbol, Symbol) or not isinstance(position, Position):
            raise InvalidPositionError("Invalid symbol or position")
        if (type(position.row) is not int or type(position.col) is not int
                or not 0 <= position.row < self._n
                or not 0 <= position.col < self._n):
            raise InvalidPositionError("Position is outside the board")

    def record_move(self, symbol: Symbol, position: Position) -> bool:
        self.validate_move(symbol, position)
        row, col = position.row, position.col
        self._rows[symbol][row] += 1
        self._cols[symbol][col] += 1
        if row == col:
            self._main[symbol] += 1
        if row + col == self._n - 1:
            self._anti[symbol] += 1
        return (
            self._rows[symbol][row] == self._n
            or self._cols[symbol][col] == self._n
            or self._main[symbol] == self._n
            or self._anti[symbol] == self._n
        )
