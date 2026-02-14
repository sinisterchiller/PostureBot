import random
import pygame
import sys
import os
import subprocess

# -------- Config --------
W, H = 480, 720
FPS = 60

LANES = 3
LANE_W = W // LANES

PLAYER_W, PLAYER_H = 60, 100
ENEMY_W, ENEMY_H = 60, 100

BASE_SPEED = 6
SPEED_UP_PER_10S = 0.8
SPAWN_MS_START = 1000
SPAWN_MS_MIN = 900


def lane_center_x(lane_idx: int) -> int:
    return lane_idx * LANE_W + LANE_W // 2


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


class Car:
    def __init__(self, lane, y, color):
        self.lane = lane
        self.x = lane_center_x(lane) - ENEMY_W // 2
        self.y = y
        self.rect = pygame.Rect(self.x, self.y, ENEMY_W, ENEMY_H)
        self.color = color

    def update(self, speed):
        self.y += speed
        self.rect.y = int(self.y)

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect, border_radius=10)
        pygame.draw.rect(
            screen,
            (230, 230, 255),
            self.rect.inflate(-25, -55).move(0, -15),
            border_radius=8,
        )


def draw_hud(screen, score, best, speed):
    hud_rect = pygame.Rect(12, 12, W - 24, 72)
    pygame.draw.rect(screen, (0, 0, 0), hud_rect, border_radius=14)
    pygame.draw.rect(screen, (255, 255, 255), hud_rect, width=2, border_radius=14)

    max_vis_score = 50
    frac_score = min(1.0, score / max_vis_score)
    bar1 = pygame.Rect(24, 26, int((W - 48) * frac_score), 14)
    pygame.draw.rect(screen, (255, 255, 255), pygame.Rect(24, 26, W - 48, 14), width=2, border_radius=8)
    pygame.draw.rect(screen, (255, 255, 255), bar1, border_radius=8)

    if best > 0:
        frac_best = min(1.0, best / max_vis_score)
        x = 24 + int((W - 48) * frac_best)
        pygame.draw.line(screen, (255, 210, 90), (x, 24), (x, 44), width=3)

    max_speed = BASE_SPEED + 10
    frac_speed = clamp((speed - BASE_SPEED) / (max_speed - BASE_SPEED), 0.0, 1.0)
    pygame.draw.rect(screen, (255, 255, 255), pygame.Rect(24, 54, W - 48, 14), width=2, border_radius=8)
    bar2 = pygame.Rect(24, 54, int((W - 48) * frac_speed), 14)
    pygame.draw.rect(screen, (255, 255, 255), bar2, border_radius=8)

    for i in range(1, 10):
        tx = 24 + int((W - 48) * (i / 10))
        pygame.draw.line(screen, (180, 180, 180), (tx, 24), (tx, 40), 1)
        pygame.draw.line(screen, (180, 180, 180), (tx, 54), (tx, 68), 1)


def draw_game_over(screen):
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))
    screen.blit(overlay, (0, 0))

    cx, cy = W // 2, H // 2
    size = 70
    pygame.draw.line(screen, (255, 255, 255), (cx - size, cy - size), (cx + size, cy + size), 10)
    pygame.draw.line(screen, (255, 255, 255), (cx - size, cy + size), (cx + size, cy - size), 10)

    rx, ry = cx - 20, cy + 95
    pygame.draw.rect(screen, (255, 255, 255), (rx, ry, 12, 38), border_radius=4)
    pygame.draw.rect(screen, (255, 255, 255), (rx + 10, ry, 22, 18), border_radius=6)
    pygame.draw.line(screen, (255, 255, 255), (rx + 18, ry + 18), (rx + 32, ry + 38), 6)


def main():
    pygame.init()
    pygame.display.set_caption("Traffic Escape (Fontless)")
    screen = pygame.display.set_mode((W, H))
    pygame.init()
    pygame.display.set_caption("Traffic Escape (Fontless)")
    screen = pygame.display.set_mode((W, H))
    # Bring window to front on macOS when launched from another process
    try:
        pid = os.getpid()
        subprocess.run(
            ["osascript", "-e", f'tell application "System Events" to set frontmost of first process whose unix id is {pid} to true'],
            check=False, capture_output=True, timeout=1
        )
    except Exception:
        pass
    clock = pygame.time.Clock()

    player_lane = 1
    player_y = H - 140
    player = pygame.Rect(lane_center_x(player_lane) - PLAYER_W // 2, player_y, PLAYER_W, PLAYER_H)

    enemies = []
    score = 0
    best = 0
    game_over = False

    speed = BASE_SPEED
    spawn_ms = SPAWN_MS_START
    start_ticks = pygame.time.get_ticks()
    next_spawn_time = pygame.time.get_ticks() + SPAWN_MS_START

    def spawn_enemy():
        lane = random.randrange(LANES)
        color = random.choice([(255, 90, 90), (90, 255, 140), (90, 150, 255), (255, 210, 90)])
        enemies.append(Car(lane, y=-ENEMY_H - 20, color=color))

    def reset():
        nonlocal player_lane, enemies, score, speed, spawn_ms, game_over, start_ticks, next_spawn_time
        player_lane = 1
        player.x = lane_center_x(player_lane) - PLAYER_W // 2
        enemies = []
        score = 0
        speed = BASE_SPEED
        spawn_ms = SPAWN_MS_START
        game_over = False
        start_ticks = pygame.time.get_ticks()
        next_spawn_time = pygame.time.get_ticks() + SPAWN_MS_START

    running = True
    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                if not game_over:
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        player_lane = clamp(player_lane - 1, 0, LANES - 1)
                    if event.key in (pygame.K_RIGHT, pygame.K_d):
                        player_lane = clamp(player_lane + 1, 0, LANES - 1)
                else:
                    if event.key == pygame.K_r:
                        reset()

        if not game_over:
            now = pygame.time.get_ticks()
            elapsed_s = (now - start_ticks) / 1000.0

            # difficulty ramp
            speed = BASE_SPEED + (elapsed_s / 10.0) * SPEED_UP_PER_10S
            spawn_ms = max(SPAWN_MS_MIN, int(SPAWN_MS_START - elapsed_s * 20))

            # spawn traffic reliably
            if now >= next_spawn_time:
                spawn_enemy()
                next_spawn_time = now + spawn_ms

            # smooth lane move
            target_x = lane_center_x(player_lane) - PLAYER_W // 2
            player.x += int((target_x - player.x) * 0.25)

            # update enemies
            for e in enemies:
                e.update(speed)

            # remove passed enemies, add score
            before = len(enemies)
            enemies = [e for e in enemies if e.rect.top < H + 40]
            score += (before - len(enemies))

            # collision
            for e in enemies:
                if player.colliderect(e.rect):
                    game_over = True
                    best = max(best, score)
                    break

        # -------- Draw --------
        screen.fill((20, 20, 24))
        pygame.draw.rect(screen, (35, 35, 40), (0, 0, W, H))

        for i in range(1, LANES):
            x = i * LANE_W
            for y in range(0, H, 40):
                pygame.draw.rect(screen, (210, 210, 210), (x - 3, y, 6, 22), border_radius=3)

        pygame.draw.rect(screen, (255, 255, 255), player, border_radius=10)
        pygame.draw.rect(screen, (210, 240, 255), player.inflate(-25, -55).move(0, -15), border_radius=8)

        for e in enemies:
            e.draw(screen)

        draw_hud(screen, score, best, speed)

        if game_over:
            draw_game_over(screen)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()