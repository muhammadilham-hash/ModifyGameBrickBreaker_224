import tkinter as tk
import random


# ==============================
# GAME OBJECT
# ==============================

class GameObject:
    def __init__(self, canvas, item):
        self.canvas = canvas
        self.item = item

    def get_position(self):
        return self.canvas.coords(self.item)

    def move(self, x, y):
        self.canvas.move(self.item, x, y)

    def delete(self):
        self.canvas.delete(self.item)


# ==============================
# BALL CLASS
# ==============================

class Ball(GameObject):
    def __init__(self, canvas, x, y, speed_x=5, speed_y=-5):
        self.radius = 9
        self.speed_x = speed_x
        self.speed_y = speed_y
        self.speed_scale = 1.0  # dipakai power-up slow

        item = canvas.create_oval(
            x - self.radius,
            y - self.radius,
            x + self.radius,
            y + self.radius,
            fill="#00ffff",
            outline="white",
            width=2
        )

        super().__init__(canvas, item)

    def update(self):
        coords = self.get_position()

        width = self.canvas.winfo_width()

        # Collision dengan dinding
        if coords[0] <= 0:
            self.speed_x = abs(self.speed_x)

        elif coords[2] >= width:
            self.speed_x = -abs(self.speed_x)

        # Collision dengan bagian atas
        if coords[1] <= 60:
            self.speed_y = abs(self.speed_y)

        self.move(
            self.speed_x * self.speed_scale,
            self.speed_y * self.speed_scale
        )

    def reverse_y(self):
        self.speed_y *= -1

    def reverse_x(self):
        self.speed_x *= -1


# ==============================
# PADDLE CLASS
# ==============================

class Paddle(GameObject):
    DEFAULT_WIDTH = 110

    def __init__(self, canvas, x, y):
        self.width = self.DEFAULT_WIDTH
        self.height = 15
        self.speed = 9

        item = canvas.create_rectangle(
            x - self.width / 2,
            y - self.height / 2,
            x + self.width / 2,
            y + self.height / 2,
            fill="#00ff99",
            outline="white",
            width=2
        )

        super().__init__(canvas, item)

    def move_paddle(self, direction):
        coords = self.get_position()
        width = self.canvas.winfo_width()

        offset = direction * self.speed

        if coords[0] + offset >= 0 and coords[2] + offset <= width:
            self.move(offset, 0)

    def set_width(self, new_width):
        coords = self.get_position()
        canvas_width = self.canvas.winfo_width()

        center = (coords[0] + coords[2]) / 2
        left = center - new_width / 2

        # Jaga supaya tidak keluar layar
        left = max(0, min(left, canvas_width - new_width))

        self.canvas.coords(
            self.item,
            left, coords[1],
            left + new_width, coords[3]
        )

        self.width = new_width


# ==============================
# BRICK CLASS
# ==============================

class Brick(GameObject):

    COLORS = {
        1: "#ff4757",
        2: "#ffa502",
        3: "#2ed573"
    }

    def __init__(self, canvas, x, y, hits):
        self.width = 70
        self.height = 22
        self.hits = hits

        item = canvas.create_rectangle(
            x,
            y,
            x + self.width,
            y + self.height,
            fill=self.COLORS[hits],
            outline="white",
            width=1
        )

        super().__init__(canvas, item)

    def hit(self):
        self.hits -= 1

        if self.hits <= 0:
            self.delete()
            return True

        self.canvas.itemconfig(
            self.item,
            fill=self.COLORS[self.hits]
        )

        return False


# ==============================
# POWER UP CLASS
# ==============================

class PowerUp(GameObject):

    # kode: (warna, nama)
    TYPES = {
        "W": ("#3498db", "WIDE"),
        "M": ("#e84393", "MULTI"),
        "S": ("#f1c40f", "SLOW"),
        "L": ("#ff6b81", "LIFE"),
    }

    def __init__(self, canvas, x, y, kind):
        self.kind = kind
        self.speed = 3

        color = self.TYPES[kind][0]

        item = canvas.create_rectangle(
            x - 17, y - 10,
            x + 17, y + 10,
            fill=color,
            outline="white",
            width=2
        )

        self.label = canvas.create_text(
            x, y,
            text=kind,
            fill="black",
            font=("Arial", 10, "bold")
        )

        super().__init__(canvas, item)

    def move(self, x, y):
        self.canvas.move(self.item, x, y)
        self.canvas.move(self.label, x, y)

    def delete(self):
        self.canvas.delete(self.item)
        self.canvas.delete(self.label)

    def update(self):
        self.move(0, self.speed)


# ==============================
# MAIN GAME CLASS
# ==============================

class Game(tk.Frame):

    DROP_CHANCE = 0.25       # peluang power-up muncul saat brick hancur
    WIDE_DURATION = 600      # frame (~10 detik)
    SLOW_DURATION = 500      # frame (~8 detik)
    WIDE_SIZE = 180
    SLOW_FACTOR = 0.6
    MAX_BALLS = 6
    MAX_LIVES = 5

    def __init__(self, master):

        super().__init__(master)

        self.width = 800
        self.height = 600

        self.score = 0
        self.lives = 3
        self.level = 1

        self.running = False
        self.paused = False
        self.game_over = False

        self.keys = set()

        # Power-up state
        self.powerups = []
        self.wide_timer = 0
        self.slow_timer = 0

        # Canvas
        self.canvas = tk.Canvas(
            self,
            width=self.width,
            height=self.height,
            bg="#101820",
            highlightthickness=0
        )

        self.canvas.pack()
        self.pack()

        # Game objects
        self.balls = []
        self.paddle = None
        self.bricks = []

        # HUD
        self.create_hud()

        # Paddle
        self.create_paddle()

        # Bricks
        self.create_bricks()

        # Ball
        self.create_ball()

        # Instructions
        self.message = self.canvas.create_text(
            self.width / 2,
            300,
            text="PRESS SPACE TO START",
            fill="white",
            font=("Arial", 24, "bold")
        )

        self.canvas.create_text(
            self.width / 2,
            335,
            text="Use LEFT / RIGHT or A / D to move",
            fill="#aaaaaa",
            font=("Arial", 12),
            tags="hint"
        )

        # Keyboard controls
        self.canvas.focus_set()

        self.canvas.bind("<KeyPress>", self.key_press)
        self.canvas.bind("<KeyRelease>", self.key_release)

        # Start game loop
        self.after(16, self.game_loop)

    # ==============================
    # HUD
    # ==============================

    def create_hud(self):

        self.canvas.create_rectangle(
            0, 0, self.width, 60,
            fill="#202b38",
            outline=""
        )

        self.score_text = self.canvas.create_text(
            100, 30,
            text="SCORE: 0",
            fill="#00ffff",
            font=("Arial", 15, "bold")
        )

        self.lives_text = self.canvas.create_text(
            400, 30,
            text="LIVES: 3",
            fill="#ff4757",
            font=("Arial", 15, "bold")
        )

        self.level_text = self.canvas.create_text(
            690, 30,
            text="LEVEL: 1",
            fill="#2ed573",
            font=("Arial", 15, "bold")
        )

        # Indikator power-up yang sedang aktif
        self.effect_text = self.canvas.create_text(
            400, 78,
            text="",
            fill="#f1c40f",
            font=("Arial", 11, "bold")
        )

    def update_hud(self):

        self.canvas.itemconfig(
            self.score_text,
            text=f"SCORE: {self.score}"
        )

        self.canvas.itemconfig(
            self.lives_text,
            text=f"LIVES: {self.lives}"
        )

        self.canvas.itemconfig(
            self.level_text,
            text=f"LEVEL: {self.level}"
        )

    def update_effect_text(self):

        parts = []

        if self.wide_timer > 0:
            parts.append(f"WIDE {self.wide_timer // 62 + 1}s")

        if self.slow_timer > 0:
            parts.append(f"SLOW {self.slow_timer // 62 + 1}s")

        self.canvas.itemconfig(
            self.effect_text,
            text="   ".join(parts)
        )

    # ==============================
    # CREATE OBJECTS
    # ==============================

    def create_paddle(self):

        self.paddle = Paddle(
            self.canvas,
            self.width / 2,
            550
        )

    def create_ball(self):

        for ball in self.balls:
            ball.delete()

        self.balls = []

        paddle_coords = self.paddle.get_position()

        x = (paddle_coords[0] + paddle_coords[2]) / 2

        self.balls.append(Ball(
            self.canvas,
            x,
            530
        ))

    def create_bricks(self):

        self.bricks = []

        rows = 5
        columns = 9

        brick_width = 70
        gap = 10

        start_x = 45
        start_y = 100

        for row in range(rows):

            for col in range(columns):

                x = start_x + col * (brick_width + gap)
                y = start_y + row * 32

                hits = ((row + self.level - 1) % 3) + 1

                brick = Brick(
                    self.canvas,
                    x,
                    y,
                    hits
                )

                self.bricks.append(brick)

    # ==============================
    # POWER UP LOGIC
    # ==============================

    def spawn_powerup(self, x, y):

        kind = random.choice(list(PowerUp.TYPES.keys()))

        self.powerups.append(PowerUp(self.canvas, x, y, kind))

    def clear_powerups(self):

        for p in self.powerups:
            p.delete()

        self.powerups = []

    def reset_effects(self):
        """Matikan semua efek aktif dan hapus power-up yang sedang jatuh."""

        self.clear_powerups()

        self.wide_timer = 0
        self.slow_timer = 0

        if self.paddle is not None and self.paddle.get_position():
            self.paddle.set_width(Paddle.DEFAULT_WIDTH)

    def activate_powerup(self, kind):

        self.score += 5

        if kind == "W":
            self.wide_timer = self.WIDE_DURATION
            self.paddle.set_width(self.WIDE_SIZE)

        elif kind == "M":
            self.activate_multiball()

        elif kind == "S":
            self.slow_timer = self.SLOW_DURATION

        elif kind == "L":
            self.lives = min(self.lives + 1, self.MAX_LIVES)

        self.update_hud()
