from .errors import TicTacToeError
from .game import Game
from .models import GameStatus, Player, Symbol

def format_board(board) -> str:
    lines = [" | ".join(cell.value if cell else "_" for cell in row) for row in board]
    separator = "-" * len(lines[0])
    return ("\n" + separator + "\n").join(lines)

def main() -> None:
    print("Tic-Tac-Toe (enter row and column with zero-based indices)")
    size_text = input("Board size [3]: ").strip()
    try:
        size = int(size_text) if size_text else 3
        p1 = Player("P1", input("First player name [Alice]: ").strip() or "Alice", Symbol.X)
        p2 = Player("P2", input("Second player name [Bob]: ").strip() or "Bob", Symbol.O)
        game = Game([p1, p2], board_size=size)
        game.start()
    except (ValueError, TicTacToeError) as exc:
        print(f"Unable to start: {exc}")
        return
    while True:
        print("\n" + format_board(game.get_board()))
        if game.get_status() == GameStatus.WON:
            print(f"Winner: {game.get_winner().name}")
        elif game.get_status() == GameStatus.DRAW:
            print("Game is a draw!")
        if game.get_status() != GameStatus.IN_PROGRESS:
            answer = input("Play again? [y/N]: ").strip().lower()
            if answer != "y":
                return
            game.restart()
            continue
        player = game.get_current_player()
        entry = input(f"{player.name} ({player.symbol.value}), row col (or q): ").strip()
        if entry.lower() in ("q", "quit", "exit"):
            return
        try:
            pieces = entry.split()
            if len(pieces) != 2:
                raise ValueError("Enter exactly two integers, such as: 0 2")
            row, col = map(int, pieces)
            game.make_move(player.id, row, col)
        except (ValueError, TicTacToeError) as exc:
            print(f"Invalid move: {exc}")

if __name__ == "__main__":
    main()
