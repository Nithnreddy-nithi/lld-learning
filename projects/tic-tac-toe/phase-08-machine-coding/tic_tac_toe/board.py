from .errors import CellOccupiedError, InvalidConfigurationError, InvalidPositionError
from .models import Position, Symbol

class Board:
    def __init__(self, size: int = 3) -> None:
        if type(size) is not int or size < 1:
            raise InvalidConfigurationError("Board size must be a positive integer")
        self._size = size
        self._cells: list[list[Symbol | None]] = [[None] * size for _ in range(size)]
        self._occupied_count = 0

    @property
    def size(self) -> int:
        return self._size

    @property
    def occupied_count(self) -> int:
        return self._occupied_count

    def is_inside(self, position: Position) -> bool:
        return (
            isinstance(position, Position)
            and type(position.row) is int and type(position.col) is int
            and 0 <= position.row < self._size
            and 0 <= position.col < self._size
        )

    def _require_inside(self, position: Position) -> None:
        if not self.is_inside(position):
            raise InvalidPositionError("Position is outside the board")

    def is_empty(self, position: Position) -> bool:
        self._require_inside(position)
        return self._cells[position.row][position.col] is None

    def place_symbol(self, position: Position, symbol: Symbol) -> None:
        self._require_inside(position)
        if not isinstance(symbol, Symbol):
            raise InvalidConfigurationError("Invalid board symbol")
        if not self.is_empty(position):
            raise CellOccupiedError("The selected cell is occupied")
        self._cells[position.row][position.col] = symbol
        self._occupied_count += 1

    def remove_symbol(self, position: Position) -> None:
        """Internal rollback helper."""
        self._require_inside(position)
        if self._cells[position.row][position.col] is None:
            raise InvalidPositionError("Cannot remove an empty cell")
        self._cells[position.row][position.col] = None
        self._occupied_count -= 1

    def is_full(self) -> bool:
        return self._occupied_count == self._size * self._size

    def get_snapshot(self) -> tuple[tuple[Symbol | None, ...], ...]:
        return tuple(tuple(row) for row in self._cells)
