import os
import random
import array
import pygame

WIDTH, HEIGHT, CUBE_W, CUBE_H = 720, 560, 72, 42
SIDE = 21
ROWS, TARGET = 7, 2
HOP_TIME, HOP_HEIGHT = 0.28, 26
CELLS = {(r, c) for r in range(ROWS) for c in range(r + 1)}
DEFAULT_PALETTE = [(90, 160, 220), (190, 120, 70), (100, 210, 140)]
KEY_HOPS = {pygame.K_LEFT: (-1, -1), pygame.K_UP: (-1, 0), pygame.K_DOWN: (1, 0), pygame.K_RIGHT: (1, 1)}

COMPLETED_FLASHES = {}


# --- Sound Effect Manager ---
class SoundManager:
    def __init__(self):
        self.enabled = False
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            self.enabled = True
            self.hop_snd = self.make_synth_sound(440, 0.08, "square")
            self.paint_snd = self.make_synth_sound(660, 0.12, "sine")
            self.freeze_snd = self.make_synth_sound(880, 0.25, "sine")
            self.die_snd = self.make_synth_sound(180, 0.35, "saw")
        except Exception:
            self.enabled = False

    def make_synth_sound(self, freq, duration, wave_type="sine"):
        if not self.enabled:
            return None
        sample_rate = 22050
        n_samples = int(sample_rate * duration)
        buf = array.array('h')
        for i in range(n_samples):
            t = float(i) / sample_rate
            if wave_type == "sine":
                val = math_sin(2.0 * 3.14159 * freq * t)
            elif wave_type == "square":
                val = 1.0 if (int(2.0 * freq * t) % 2 == 0) else -1.0
            else:
                val = 2.0 * (t * freq - math_floor(0.5 + t * freq))
            fade = 1.0 - (i / n_samples)
            buf.append(int(val * 12000 * fade))
        return pygame.mixer.Sound(buffer=buf)

    def play(self, snd):
        if self.enabled and snd:
            snd.play()


def math_sin(x):
    import math
    return math.sin(x)


def math_floor(x):
    import math
    return math.floor(x)


SOUNDS = None


def cube_palette(level):
    palettes = [
        [(90, 160, 220), (190, 120, 70), (100, 210, 140)],   # Level 1: Default
        [(70, 70, 180), (220, 100, 180), (240, 220, 80)],   # Level 2: Neon
        [(50, 140, 120), (210, 130, 60), (220, 70, 70)],    # Level 3: Autumn
        [(100, 100, 100), (180, 180, 180), (255, 215, 0)],  # Level 4+: Gold
    ]
    return palettes[(level - 1) % len(palettes)]


def on_cube_completed(cell):
    COMPLETED_FLASHES[cell] = 0.2


def bonus_life_threshold():
    return 1000


def cube_center(row, col):
    return pygame.Vector2(WIDTH / 2 + (col - row / 2) * CUBE_W, 90 + row * CUBE_H)


def neighbors(row, col):
    return [(row - 1, col - 1), (row - 1, col), (row + 1, col), (row + 1, col + 1)]


def shade(color, factor):
    return tuple(int(v * factor) for v in color)


class Hopper:
    def __init__(self, cell, kind="normal"):
        self.cell, self.target, self.t, self.fall = cell, None, 0.0, None
        self.kind = kind

    @property
    def busy(self):
        return self.target is not None or self.fall is not None

    def start(self, target):
        self.target, self.t = target, 0.0

    def update(self, dt):
        if self.fall is not None:
            self.fall += 420 * dt
            return None
        if self.target is None:
            return None
        self.t += dt / HOP_TIME
        if self.t < 1:
            return None
        self.cell, self.target = self.target, None
        if self.cell not in CELLS:
            self.fall = 0.0
            return None
        return self.cell

    def pos(self):
        if self.target is None:
            base = cube_center(*self.cell)
            if self.fall is not None:
                base.y += self.fall
            return base
        start, end = cube_center(*self.cell), cube_center(*self.target)
        point = start.lerp(end, self.t)
        point.y -= HOP_HEIGHT * 4 * self.t * (1 - self.t)
        return point


class Game:
    def __init__(self):
        self.font = pygame.font.Font(None, 26)
        self.level, self.score, self.lives = 1, 0, 3
        self.high_score = self.load_high_score()
        self.freeze_timer = 0.0
        self.respawn_grace = 0.0
        self.reset()

    def load_high_score(self):
        if os.path.exists("highscore.txt"):
            try:
                with open("highscore.txt", "r") as f:
                    return int(f.read().strip())
            except Exception:
                return 0
        return 0

    def save_high_score(self):
        if self.score > self.high_score:
            self.high_score = self.score
            try:
                with open("highscore.txt", "w") as f:
                    f.write(str(self.high_score))
            except Exception:
                pass

    def reset(self, full=True):
        if full:
            self.level, self.score, self.lives = 1, 0, 3
            self.bonus_awarded = 0
        self.stages = {cell: 0 for cell in CELLS}
        self.state = "play"
        self.freeze_timer = 0.0
        COMPLETED_FLASHES.clear()
        self.respawn()

    def respawn(self):
        self.player = Hopper((0, 0))
        self.coily, self.balls = None, []
        self.coily_timer, self.ball_timer, self.enemy_hop = 4.0, 2.0, 0.0
        self.respawn_grace = 2.0  # 2 seconds invincibility/grace window on spawn

    def paint(self, cell):
        if cell not in self.stages or self.stages[cell] >= TARGET:
            return
        self.stages[cell] += 1
        self.score += 25
        self.save_high_score()
        if SOUNDS:
            SOUNDS.play(SOUNDS.paint_snd)
        if self.stages[cell] == TARGET:
            on_cube_completed(cell)

    def hop(self, key):
        if self.state != "play" or self.player.busy:
            return
        delta = KEY_HOPS[key]
        candidate = (self.player.cell[0] + delta[0], self.player.cell[1] + delta[1])
        self.player.start(candidate)
        if SOUNDS:
            SOUNDS.play(SOUNDS.hop_snd)

    def move_enemies(self):
        if self.freeze_timer > 0:
            return
        if self.coily and not self.coily.busy:
            # Filter options so Coily never hops into top node (0, 0)
            options = [n for n in neighbors(*self.coily.cell) if n in CELLS and n != (0, 0)]
            if not options:
                options = [n for n in neighbors(*self.coily.cell) if n in CELLS]
            goal = cube_center(*self.player.cell)
            if options:
                self.coily.start(min(options, key=lambda n: cube_center(*n).distance_squared_to(goal)))
        for ball in self.balls:
            if not ball.busy:
                ball.start((ball.cell[0] + 1, ball.cell[1] + random.randint(0, 1)))

    def lose_life(self):
        if SOUNDS:
            SOUNDS.play(SOUNDS.die_snd)
        self.lives -= 1
        if self.lives <= 0:
            self.state = "lose"
        else:
            self.respawn()

    def update(self, dt):
        if self.state != "play":
            return

        if self.respawn_grace > 0:
            self.respawn_grace -= dt

        if self.freeze_timer > 0:
            self.freeze_timer -= dt

        for cell in list(COMPLETED_FLASHES.keys()):
            COMPLETED_FLASHES[cell] -= dt
            if COMPLETED_FLASHES[cell] <= 0:
                del COMPLETED_FLASHES[cell]

        landed = self.player.update(dt)
        if landed:
            self.paint(landed)

        threshold = bonus_life_threshold()
        if threshold and self.score // threshold > self.bonus_awarded:
            self.bonus_awarded = self.score // threshold
            self.lives += 1

        if self.player.fall is not None and self.player.fall > 260:
            self.lose_life()
            return

        if self.freeze_timer <= 0:
            self.coily_timer -= dt
            if self.coily is None and self.coily_timer <= 0:
                # Spawn Coily at row 4
                self.coily = Hopper((4, random.randint(0, 4)))

            self.ball_timer -= dt
            if self.ball_timer <= 0:
                kind = "green" if random.random() < 0.25 else "normal"
                self.balls.append(Hopper((2, random.randint(0, 2)), kind=kind))
                self.ball_timer = 5.0

            self.enemy_hop -= dt
            if self.enemy_hop <= 0:
                self.enemy_hop = 0.35
                self.move_enemies()

        enemies = ([self.coily] if self.coily else []) + self.balls
        for enemy in enemies:
            if self.freeze_timer <= 0 or enemy == self.player:
                enemy.update(dt)

        self.balls = [b for b in self.balls if b.fall is None or b.fall < 260]

        if self.player.target is None and self.player.fall is None and self.respawn_grace <= 0:
            for ball in list(self.balls):
                if ball.kind == "green" and ball.fall is None and ball.pos().distance_to(self.player.pos()) < 26:
                    self.freeze_timer = 3.5
                    self.score += 100
                    self.save_high_score()
                    if SOUNDS:
                        SOUNDS.play(SOUNDS.freeze_snd)
                    self.balls.remove(ball)
                    break

            for enemy in enemies:
                if enemy.fall is None and enemy.kind != "green" and enemy.pos().distance_to(self.player.pos()) < 26:
                    self.lose_life()
                    return

        if all(stage >= TARGET for stage in self.stages.values()):
            self.score += 500
            self.save_high_score()
            self.state = "win"

    def draw_cube(self, screen, cell, colors):
        cx, cy = cube_center(*cell)
        top = [(cx, cy - CUBE_H / 2), (cx + CUBE_W / 2, cy), (cx, cy + CUBE_H / 2), (cx - CUBE_W / 2, cy)]

        if cell in COMPLETED_FLASHES:
            color = (255, 255, 255)
        else:
            color = colors[self.stages[cell]]

        left = [top[3], top[2], (cx, cy + CUBE_H / 2 + SIDE), (cx - CUBE_W / 2, cy + SIDE)]
        right = [top[1], top[2], (cx, cy + CUBE_H / 2 + SIDE), (cx + CUBE_W / 2, cy + SIDE)]

        pygame.draw.polygon(screen, shade(DEFAULT_PALETTE[0], 0.45), left)
        pygame.draw.polygon(screen, shade(DEFAULT_PALETTE[0], 0.3), right)
        pygame.draw.polygon(screen, color, top)
        pygame.draw.polygon(screen, (240, 240, 240), top, 1)

    def draw(self, screen):
        screen.fill((18, 20, 38))
        colors = cube_palette(self.level) or DEFAULT_PALETTE
        for cell in sorted(CELLS):
            self.draw_cube(screen, cell, colors)

        for enemy in self.balls:
            ball_color = (60, 230, 90) if enemy.kind == "green" else (230, 60, 60)
            pygame.draw.circle(screen, ball_color, enemy.pos() - (0, 12), 9)

        if self.coily:
            pos = self.coily.pos() - (0, 14)
            pygame.draw.circle(screen, (170, 80, 220), pos, 11)
            pygame.draw.circle(screen, (255, 255, 255), pos + (0, -2), 3)

        pos = self.player.pos() - (0, 14)
        # Blink player during spawn grace period
        if self.respawn_grace <= 0 or int(self.respawn_grace * 10) % 2 == 0:
            pygame.draw.circle(screen, (250, 150, 40), pos, 13)
            pygame.draw.circle(screen, (255, 255, 255), pos + (-5, -3), 3)
            pygame.draw.circle(screen, (255, 255, 255), pos + (5, -3), 3)
            pygame.draw.circle(screen, (250, 90, 40), pos + (0, 6), 5)

        hud_str = f"Score {self.score}  High {self.high_score}  Lives {self.lives}  Level {self.level}"
        if self.freeze_timer > 0:
            hud_str += f"  [FROZEN: {self.freeze_timer:.1f}s]"
        hud = self.font.render(hud_str, True, (240, 240, 240))
        screen.blit(hud, (10, 8))

        if self.state != "play":
            text = "LEVEL CLEAR! Press Space" if self.state == "win" else "GAME OVER - Press R"
            label = self.font.render(text, True, (255, 255, 120))
            screen.blit(label, label.get_rect(center=(WIDTH // 2, HEIGHT - 40)))


def main():
    global SOUNDS
    pygame.init()
    SOUNDS = SoundManager()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Q*bert")
    clock = pygame.time.Clock()
    game = Game()
    running = True
    while running:
        dt = min(clock.tick(60) / 1000, 0.05)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in KEY_HOPS:
                    game.hop(event.key)
                elif event.key == pygame.K_r:
                    game.reset()
                elif event.key == pygame.K_SPACE and game.state == "win":
                    game.level += 1
                    game.reset(full=False)
        game.update(dt)
        game.draw(screen)
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()