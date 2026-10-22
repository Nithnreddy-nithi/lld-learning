class TicTacToeError(Exception):
    """Base exception for game-domain failures."""

class InvalidConfigurationError(TicTacToeError): pass
class InvalidGameStateError(TicTacToeError): pass
class UnknownPlayerError(TicTacToeError): pass
class NotYourTurnError(TicTacToeError): pass
class InvalidPositionError(TicTacToeError): pass
class CellOccupiedError(TicTacToeError): pass
