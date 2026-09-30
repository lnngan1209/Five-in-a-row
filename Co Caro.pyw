"""Co Caro: play five-in-a-row against the computer."""

import ctypes
import tkinter as tk
from tkinter import font


BOARD_SIZE = 15
CELL = 38
MARGIN = 34
CANVAS_SIZE = MARGIN * 2 + CELL * (BOARD_SIZE - 1)
DIRECTIONS = ((0, 1), (1, 0), (1, 1), (1, -1))


def winning_cells(board, row, col, player):
    """Return the complete winning run through the last move, if any."""
    for dr, dc in DIRECTIONS:
        cells = [(row, col)]
        for sign in (-1, 1):
            rr, cc = row + sign * dr, col + sign * dc
            while 0 <= rr < BOARD_SIZE and 0 <= cc < BOARD_SIZE and board[rr][cc] == player:
                cells.append((rr, cc))
                rr += sign * dr
                cc += sign * dc
        if len(cells) >= 5:
            return sorted(cells, key=lambda pos: pos[0] * dr + pos[1] * dc)
    return []


def candidate_moves(board):
    occupied = [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE)
                if board[r][c] is not None]
    if not occupied:
        return [(BOARD_SIZE // 2, BOARD_SIZE // 2)]
    candidates = set()
    for row, col in occupied:
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                rr, cc = row + dr, col + dc
                if 0 <= rr < BOARD_SIZE and 0 <= cc < BOARD_SIZE and board[rr][cc] is None:
                    candidates.add((rr, cc))
    return sorted(candidates)


def move_score(board, row, col, player):
    """Score runs created by placing a stone at an empty intersection."""
    board[row][col] = player
    total = 0
    for dr, dc in DIRECTIONS:
        count = 1
        open_ends = 0
        for sign in (-1, 1):
            rr, cc = row + sign * dr, col + sign * dc
            while 0 <= rr < BOARD_SIZE and 0 <= cc < BOARD_SIZE and board[rr][cc] == player:
                count += 1
                rr += sign * dr
                cc += sign * dc
            if 0 <= rr < BOARD_SIZE and 0 <= cc < BOARD_SIZE and board[rr][cc] is None:
                open_ends += 1
        if count >= 5:
            total += 1_000_000
        elif count == 4:
            total += 80_000 if open_ends == 2 else 10_000 if open_ends == 1 else 0
        elif count == 3:
            total += 5_000 if open_ends == 2 else 450 if open_ends == 1 else 0
        elif count == 2:
            total += 300 if open_ends == 2 else 40 if open_ends == 1 else 0
        elif open_ends:
            total += 8
    board[row][col] = None
    return total


def choose_computer_move(board):
    moves = candidate_moves(board)
    if not moves:
        return None

    # Finish a winning line first; otherwise stop the player's next winning move.
    for player in ("O", "X"):
        for row, col in moves:
            board[row][col] = player
            wins = bool(winning_cells(board, row, col, player))
            board[row][col] = None
            if wins:
                return row, col

    center = (BOARD_SIZE - 1) / 2
    return max(moves, key=lambda pos: (
        move_score(board, pos[0], pos[1], "O") * 1.15
        + move_score(board, pos[0], pos[1], "X"),
        -(abs(pos[0] - center) + abs(pos[1] - center)),
        -pos[0], -pos[1]))


class CaroApp:
    def __init__(self, root):
        self.root = root
        root.title("Cờ Caro — 5 quân thẳng hàng")
        root.configure(bg="#f4efe6")
        root.resizable(False, False)

        self.board = [[None] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.current_player = "X"
        self.winner = None
        self.game_over = False
        self.move_count = 0
        self.last_move = None
        self.win_line = []
        self.scores = {"X": 0, "O": 0}
        self.ai_job = None

        self.heading_font = font.Font(family="Segoe UI", size=21, weight="bold")
        self.body_font = font.Font(family="Segoe UI", size=11)
        self.strong_font = font.Font(family="Segoe UI", size=12, weight="bold")

        header = tk.Frame(root, bg="#f4efe6")
        header.pack(fill="x", padx=24, pady=(18, 8))
        tk.Label(header, text="CỜ CARO", font=self.heading_font,
                 fg="#25334a", bg="#f4efe6").pack(side="left")
        tk.Button(header, text="Ván mới", command=self.new_game,
                  font=self.body_font, fg="white", bg="#245c86",
                  activebackground="#164566", activeforeground="white",
                  relief="flat", padx=18, pady=7, cursor="hand2").pack(side="right")

        self.status_var = tk.StringVar()
        tk.Label(root, textvariable=self.status_var, font=self.strong_font,
                 fg="#36475b", bg="#f4efe6", anchor="w").pack(fill="x", padx=25)

        self.canvas = tk.Canvas(root, width=CANVAS_SIZE, height=CANVAS_SIZE,
                                bg="#e9c98e", highlightthickness=1,
                                highlightbackground="#b89259", cursor="hand2")
        self.canvas.pack(padx=24, pady=(12, 10))
        self.canvas.bind("<Button-1>", self.on_board_click)

        self.score_var = tk.StringVar()
        tk.Label(root, textvariable=self.score_var, font=self.body_font,
                 fg="#36475b", bg="#f4efe6").pack(pady=(0, 3))
        tk.Label(root, text="Bạn: X (xanh)  •  Máy: O (đỏ)  •  5 quân liên tiếp sẽ thắng",
                 font=font.Font(family="Segoe UI", size=9), fg="#6d7580",
                 bg="#f4efe6").pack(pady=(0, 15))
        self.refresh()

    def new_game(self):
        if self.ai_job is not None:
            self.root.after_cancel(self.ai_job)
            self.ai_job = None
        self.board = [[None] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.current_player = "X"
        self.winner = None
        self.game_over = False
        self.move_count = 0
        self.last_move = None
        self.win_line = []
        self.refresh()

    def on_board_click(self, event):
        if self.current_player != "X" or self.game_over:
            return
        col = round((event.x - MARGIN) / CELL)
        row = round((event.y - MARGIN) / CELL)
        if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
            return
        if abs(event.x - (MARGIN + col * CELL)) > CELL * 0.46:
            return
        if abs(event.y - (MARGIN + row * CELL)) > CELL * 0.46:
            return
        if self.play(row, col) and not self.game_over:
            self.ai_job = self.root.after(180, self.computer_turn)

    def computer_turn(self):
        if self.ai_job is not None:
            self.root.after_cancel(self.ai_job)
            self.ai_job = None
        if self.game_over or self.current_player != "O":
            return
        move = choose_computer_move(self.board)
        if move is not None:
            self.play(*move)

    def play(self, row, col):
        if self.game_over or not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
            return False
        if self.board[row][col] is not None:
            return False
        player = self.current_player
        self.board[row][col] = player
        self.last_move = (row, col)
        self.move_count += 1
        self.win_line = winning_cells(self.board, row, col, player)
        if self.win_line:
            self.winner = player
            self.game_over = True
            self.scores[player] += 1
        elif self.move_count == BOARD_SIZE * BOARD_SIZE:
            self.game_over = True
        else:
            self.current_player = "O" if player == "X" else "X"
        self.refresh()
        return True

    def refresh(self):
        if self.winner:
            result = "Bạn thắng!" if self.winner == "X" else "Máy thắng!"
            self.status_var.set(f"{result} Nhấn ‘Ván mới’ để chơi tiếp.")
        elif self.game_over:
            self.status_var.set("Hòa! Bàn cờ đã đầy.")
        else:
            self.status_var.set("Lượt của bạn (X)" if self.current_player == "X" else "Máy đang đi (O)…")
        self.score_var.set(f"Tỉ số     Bạn: {self.scores['X']}      Máy: {self.scores['O']}")
        self.draw_board()

    def draw_board(self):
        c = self.canvas
        c.delete("all")
        start = MARGIN
        end = MARGIN + CELL * (BOARD_SIZE - 1)
        for i in range(BOARD_SIZE):
            at = MARGIN + CELL * i
            c.create_line(start, at, end, at, fill="#836b45", width=1)
            c.create_line(at, start, at, end, fill="#836b45", width=1)
        for row, col in ((3, 3), (3, 11), (7, 7), (11, 3), (11, 11)):
            x, y = MARGIN + col * CELL, MARGIN + row * CELL
            c.create_oval(x - 3, y - 3, x + 3, y + 3, fill="#836b45", outline="")

        if self.win_line:
            first, last = self.win_line[0], self.win_line[-1]
            c.create_line(MARGIN + first[1] * CELL, MARGIN + first[0] * CELL,
                          MARGIN + last[1] * CELL, MARGIN + last[0] * CELL,
                          fill="#f7f0b7", width=31, capstyle="round")

        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                player = self.board[row][col]
                if player is None:
                    continue
                x, y = MARGIN + col * CELL, MARGIN + row * CELL
                color = "#1d537e" if player == "X" else "#b3443e"
                c.create_oval(x - 14, y - 14, x + 14, y + 14,
                              fill="#fdf9f1", outline=color, width=2)
                c.create_text(x, y, text=player, fill=color,
                              font=("Segoe UI", 16, "bold"))
        if self.last_move:
            row, col = self.last_move
            x, y = MARGIN + col * CELL, MARGIN + row * CELL
            c.create_oval(x + 9, y - 14, x + 15, y - 8,
                          fill="#e5a838", outline="#fdf9f1")


def main():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        pass
    root = tk.Tk()
    CaroApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
