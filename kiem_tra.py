"""Play through the visible board and check the computer's decisions."""

from pathlib import Path
import runpy
import tkinter as tk


module = runpy.run_path(str(Path(__file__).with_name("Co Caro.pyw")))
App = module["CaroApp"]
MARGIN = module["MARGIN"]
CELL = module["CELL"]

root = tk.Tk()
app = App(root)
root.update()


def click(row, col):
    app.canvas.event_generate("<Button-1>", x=MARGIN + col * CELL,
                              y=MARGIN + row * CELL)
    root.update()


def setup(xs, os, turn):
    app.new_game()
    for row, col in xs:
        app.board[row][col] = "X"
    for row, col in os:
        app.board[row][col] = "O"
    app.move_count = len(xs) + len(os)
    app.current_player = turn
    app.refresh()
    root.update()


try:
    click(7, 7)
    assert app.board[7][7] == "X" and app.current_player == "O"
    click(7, 8)
    assert app.move_count == 1, "player was allowed to play during computer turn"
    root.after(350, root.quit)
    root.mainloop()
    assert app.move_count == 2 and app.current_player == "X"
    assert sum(cell == "O" for row in app.board for cell in row) == 1
    print("PASS: human click, computer reply, locked computer turn")

    setup([(5, c) for c in range(4)], [(10, 1), (10, 3), (11, 1), (11, 3)], "O")
    app.computer_turn()
    assert app.board[5][4] == "O" and app.winner is None
    print("PASS: computer blocks immediate human win")

    setup([(1, 1), (1, 3), (2, 1), (2, 3), (3, 1)],
          [(9, c) for c in range(4)], "O")
    app.computer_turn()
    assert app.winner == "O" and app.win_line == [(9, c) for c in range(5)]
    count = app.move_count
    click(14, 14)
    assert app.move_count == count
    print("PASS: computer takes winning move; no move after defeat")

    setup([(6, c) for c in range(4)], [(12, 1), (12, 3), (13, 1), (13, 3)], "X")
    click(6, 4)
    assert app.winner == "X" and app.win_line == [(6, c) for c in range(5)]
    assert app.ai_job is None
    print("PASS: human win ends game before computer reply")

    for game_number, opening in enumerate(((0, 0), (14, 14), (0, 14)), start=1):
        app.new_game()
        root.update()
        human_choices = [opening] + [
            (r, c) for r in (0, 14, 2, 12, 4, 10)
            for c in (0, 14, 2, 12, 4, 10)
            if (r, c) != opening
        ]
        for row, col in human_choices:
            if app.game_over:
                break
            if app.board[row][col] is not None:
                continue
            click(row, col)
            if app.current_player == "O":
                app.computer_turn()
            assert app.current_player == "X" or app.game_over
        assert app.winner == "O", (game_number, app.winner, app.move_count)
        print(f"PASS: complete human-versus-computer game {game_number}")

    app.new_game()
    click(7, 7)
    assert app.ai_job is not None
    app.new_game()
    assert app.ai_job is None and app.move_count == 0 and app.current_player == "X"
    print("PASS: new game cancels pending computer move")
finally:
    root.destroy()
