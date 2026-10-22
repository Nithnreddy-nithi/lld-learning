import unittest
from tic_tac_toe import Game, GameStatus, Player, Symbol
from tic_tac_toe.errors import (CellOccupiedError, InvalidConfigurationError,
                                InvalidGameStateError, InvalidPositionError, NotYourTurnError)

def make_game(n=3):
    game = Game([Player("a", "Alice", Symbol.X), Player("b", "Bob", Symbol.O)], n)
    game.start()
    return game

class GameTests(unittest.TestCase):
    def test_start_and_turn(self):
        g = Game([Player("a", "Alice", Symbol.X), Player("b", "Bob", Symbol.O)])
        self.assertEqual(g.get_status(), GameStatus.NOT_STARTED)
        with self.assertRaises(InvalidGameStateError):
            g.make_move("a", 0, 0)
        g.start()
        self.assertEqual(g.make_move("a", 0, 0).next_player_id, "b")
        with self.assertRaises(NotYourTurnError):
            g.make_move("a", 0, 1)

    def test_bad_moves_unchanged(self):
        g = make_game()
        with self.assertRaises(InvalidPositionError):
            g.make_move("a", 3, 0)
        self.assertEqual(g.get_current_player().id, "a")
        g.make_move("a", 0, 0)
        with self.assertRaises(CellOccupiedError):
            g.make_move("b", 0, 0)
        self.assertEqual(g.get_current_player().id, "b")
        self.assertEqual(sum(x is not None for row in g.get_board() for x in row), 1)

    def test_row_win_and_restart(self):
        g = make_game()
        for who,r,c in [("a",0,0),("b",1,0),("a",0,1),("b",1,1),("a",0,2)]:
            result = g.make_move(who,r,c)
        self.assertEqual(result.status, GameStatus.WON)
        self.assertEqual(g.get_winner().id, "a")
        self.assertIsNone(g.get_current_player())
        with self.assertRaises(InvalidGameStateError):
            g.make_move("b", 2, 2)
        g.restart()
        self.assertEqual(g.get_status(), GameStatus.IN_PROGRESS)
        self.assertTrue(all(v is None for row in g.get_board() for v in row))
        self.assertEqual(g.get_current_player().id, "a")
        g.make_move("a",0,0)

    def test_main_diagonal(self):
        g=make_game()
        for w,r,c in [("a",0,0),("b",0,1),("a",1,1),("b",1,0),("a",2,2)]:
            g.make_move(w,r,c)
        self.assertEqual(g.get_status(),GameStatus.WON)

    def test_anti_diagonal(self):
        g=make_game()
        for w,r,c in [("a",0,2),("b",0,0),("a",1,1),("b",0,1),("a",2,0)]:
            g.make_move(w,r,c)
        self.assertEqual(g.get_status(),GameStatus.WON)

    def test_column_win(self):
        g=make_game()
        for w,r,c in [("a",0,1),("b",0,0),("a",1,1),("b",1,0),("a",2,1)]:
            g.make_move(w,r,c)
        self.assertEqual(g.get_status(),GameStatus.WON)

    def test_draw(self):
        g=make_game()
        for w,r,c in [("a",0,0),("b",0,1),("a",0,2),("b",1,1),("a",1,0),("b",1,2),("a",2,1),("b",2,0),("a",2,2)]:
            result=g.make_move(w,r,c)
        self.assertEqual(result.status,GameStatus.DRAW)
        self.assertIsNone(g.get_winner())

    def test_one_cell_and_invalid_size(self):
        with self.assertRaises(InvalidConfigurationError):
            make_game(True)
        g=make_game(1)
        self.assertEqual(g.make_move("a",0,0).status,GameStatus.WON)

    def test_snapshot_immutable(self):
        g=make_game()
        snap=g.get_board()
        with self.assertRaises(TypeError):
            snap[0][0]=Symbol.X

    def test_independent_games(self):
        a=make_game()
        b=make_game()
        a.make_move("a",0,0)
        self.assertIsNone(b.get_board()[0][0])

if __name__ == "__main__":
    unittest.main()
