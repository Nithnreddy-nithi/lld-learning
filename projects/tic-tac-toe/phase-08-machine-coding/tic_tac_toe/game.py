from collections.abc import Callable, Sequence
from .board import Board
from .errors import (CellOccupiedError, InvalidConfigurationError, InvalidGameStateError,
                     NotYourTurnError, UnknownPlayerError)
from .models import GameStatus, Move, MoveResult, Player, Position, Symbol
from .strategy import StandardWinningStrategy, WinningStrategy

StrategyFactory = Callable[[int], WinningStrategy]

class Game:
    def __init__(self, players: Sequence[Player], board_size: int = 3,
                 starting_player_id: str | None = None,
                 winning_strategy_factory: StrategyFactory | None = None) -> None:
        if type(board_size) is not int or board_size < 1:
            raise InvalidConfigurationError("Board size must be a positive integer")
        if not isinstance(players, (tuple, list)) or len(players) != 2:
            raise InvalidConfigurationError("Exactly two players are required")
        if not all(isinstance(p, Player) for p in players):
            raise InvalidConfigurationError("Players must be Player objects")
        if players[0].id == players[1].id or players[0].symbol == players[1].symbol:
            raise InvalidConfigurationError("Player IDs and symbols must differ")
        self._players = tuple(players)
        self._starting_index = 0
        if starting_player_id is not None:
            ids = [p.id for p in self._players]
            if starting_player_id not in ids:
                raise InvalidConfigurationError("Unknown starting player")
            self._starting_index = ids.index(starting_player_id)
        self._board_size = board_size
        self._strategy_factory = winning_strategy_factory or StandardWinningStrategy
        if not callable(self._strategy_factory):
            raise InvalidConfigurationError("Winning strategy factory must be callable")
        self._board = Board(board_size)
        self._strategy = self._new_strategy()
        self._status = GameStatus.NOT_STARTED
        self._winner: Player | None = None
        self._current_index = self._starting_index
        self._move_count = 0

    def _new_strategy(self) -> WinningStrategy:
        strategy = self._strategy_factory(self._board_size)
        if not isinstance(strategy, WinningStrategy):
            raise InvalidConfigurationError("Factory must produce a WinningStrategy")
        return strategy

    def start(self) -> None:
        if self._status != GameStatus.NOT_STARTED:
            raise InvalidGameStateError("Game has already started")
        self._status = GameStatus.IN_PROGRESS

    def make_move(self, player_id: str, row: int, col: int) -> MoveResult:
        if self._status != GameStatus.IN_PROGRESS:
            raise InvalidGameStateError("The game is not in progress")
        if player_id not in (self._players[0].id, self._players[1].id):
            raise UnknownPlayerError("Player is not in this game")
        player = self._players[self._current_index]
        if player.id != player_id:
            raise NotYourTurnError("It is not this player's turn")
        position = Position(row, col)
        if not self._board.is_empty(position):
            raise CellOccupiedError("The selected cell is occupied")
        self._strategy.validate_move(player.symbol, position)
        self._board.place_symbol(position, player.symbol)
        try:
            did_win = self._strategy.record_move(player.symbol, position)
        except Exception:
            # An unexpected strategy failure invalidates its counter state.
            # Abort the current round to a fresh consistent NOT_STARTED state.
            self._board = Board(self._board_size)
            self._winner = None
            self._current_index = self._starting_index
            self._move_count = 0
            self._status = GameStatus.NOT_STARTED
            self._strategy = self._new_strategy()
            raise
        self._move_count += 1
        if did_win:
            self._winner = player
            self._status = GameStatus.WON
        elif self._board.is_full():
            self._status = GameStatus.DRAW
        else:
            self._current_index = 1 - self._current_index
        return MoveResult(
            Move(player_id, position), self._status,
            self._players[self._current_index].id if self._status == GameStatus.IN_PROGRESS else None,
            self._winner.id if self._winner is not None else None,
        )

    def get_board(self) -> tuple[tuple[Symbol | None, ...], ...]:
        return self._board.get_snapshot()

    def get_current_player(self) -> Player | None:
        return self._players[self._current_index] if self._status == GameStatus.IN_PROGRESS else None

    def get_status(self) -> GameStatus:
        return self._status

    def get_winner(self) -> Player | None:
        return self._winner

    def restart(self) -> None:
        new_board = Board(self._board_size)
        new_strategy = self._new_strategy()
        self._board = new_board
        self._strategy = new_strategy
        self._winner = None
        self._move_count = 0
        self._current_index = self._starting_index
        self._status = GameStatus.IN_PROGRESS
