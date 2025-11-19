import pygame
import sys
import random
import os

# -------------------------
# Configuration / Constants
# -------------------------
WIDTH, HEIGHT = 400, 640
FPS = 60

BIRD_X = 80
BIRD_WIDTH, BIRD_HEIGHT = 34, 24  # visual size (rectangle)
GRAVITY = 0.45
FLAP_STRENGTH = -9.5
PIPE_WIDTH = 70
PIPE_GAP = 150  # vertical gap between top and bottom pipe
PIPE_SPACING = 150  # horizontal spacing between consecutive pipes
PIPE_SPEED_BASE = 3
FLOOR_HEIGHT = 100

FONT_NAME = None  # default system font
HIGHSCORE_FILE = "highscore.txt"

# New constants for coins
COIN_RADIUS = 10
COIN_BONUS = 5  # points per coin

# Particle effect for coins
PARTICLE_LIFETIME = 30  # frames

# -------------------------
# Helper functions
# -------------------------
def load_highscore():
    if not os.path.exists(HIGHSCORE_FILE):
        return 0
    try:
        with open(HIGHSCORE_FILE, "r") as f:
            return int(f.read().strip() or 0)
    except Exception:
        return 0

def save_highscore(score):
    try:
        with open(HIGHSCORE_FILE, "w") as f:
            f.write(str(score))
    except Exception:
        pass

def load_image(path, fallback_color, size=None):
    try:
        img = pygame.image.load(path).convert_alpha()
        if size:
            img = pygame.transform.scale(img, size)
        return img
    except:
        surf = pygame.Surface(size or (BIRD_WIDTH, BIRD_HEIGHT))
        surf.fill(fallback_color)
        return surf

def load_sound(path):
    try:
        return pygame.mixer.Sound(path)
    except:
        return None  # Silent fallback

# -------------------------
# Game classes
# -------------------------
class Bird:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.w = BIRD_WIDTH
        self.h = BIRD_HEIGHT
        self.vel = 0.0
        self.rect = pygame.Rect(self.x, self.y, self.w, self.h)
        self.rotation = 0
        self.image = load_image('bird.png', (255, 210, 0), (self.w, self.h))  # Yellow fallback

    def flap(self):
        self.vel = FLAP_STRENGTH
        if jump_sound:
            jump_sound.play()

    def update(self):
        self.vel += GRAVITY
        self.y += self.vel
        self.rotation = max(-25, min(90, -self.vel * 3))
        self.rect.topleft = (self.x, self.y)

    def draw(self, surf):
        rotated_image = pygame.transform.rotate(self.image, self.rotation)
        rect = rotated_image.get_rect(center=(self.x + self.w // 2, self.y + self.h // 2))
        surf.blit(rotated_image, rect)

class Pipe:
    def __init__(self, x):
        self.x = x
        self.w = PIPE_WIDTH
        self.gap_y = random.randint(int(HEIGHT * 0.2), int(HEIGHT - FLOOR_HEIGHT - PIPE_GAP - 20))
        self.passed = False

    def update(self, speed):
        self.x -= speed

    def offscreen(self):
        return self.x + self.w < 0

    def top_rect(self):
        return pygame.Rect(self.x, 0, self.w, self.gap_y)

    def bottom_rect(self):
        return pygame.Rect(self.x, self.gap_y + PIPE_GAP, self.w, HEIGHT - FLOOR_HEIGHT - (self.gap_y + PIPE_GAP))

    def draw(self, surf):
        pygame.draw.rect(surf, (34, 139, 34), self.top_rect())
        pygame.draw.rect(surf, (34, 139, 34), self.bottom_rect())

class Coin:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = COIN_RADIUS
        self.rect = pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)

    def update(self, speed):
        self.x -= speed
        self.rect.center = (self.x, self.y)

    def offscreen(self):
        return self.x + self.radius < 0

    def draw(self, surf):
        pygame.draw.circle(surf, (255, 215, 0), (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surf, (255, 255, 255), (int(self.x - 3), int(self.y - 3)), 3)

class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.lifetime = PARTICLE_LIFETIME
        self.color = (255, 215, 0)  # Gold

    def update(self):
        self.lifetime -= 1
        self.y -= 1  # Rise up

    def draw(self, surf):
        if self.lifetime > 0:
            alpha = int(255 * (self.lifetime / PARTICLE_LIFETIME))
            color = (self.color[0], self.color[1], self.color[2], alpha)
            pygame.draw.circle(surf, color, (int(self.x), int(self.y)), 2)

# -------------------------
# Main Game Functions
# -------------------------
def draw_text_center(surf, text, size, y, color=(255,255,255)):
    font = pygame.font.SysFont(FONT_NAME, size)
    txt = font.render(text, True, color)
    rect = txt.get_rect(center=(WIDTH//2, y))
    surf.blit(txt, rect)

def main():
    pygame.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    pygame.display.set_caption("Flappy (Pygame) — Pro Version")

    # Load assets
    global jump_sound, score_sound, hit_sound, coin_sound
    jump_sound = load_sound('jump.wav')
    score_sound = load_sound('score.wav')
    hit_sound = load_sound('hit.wav')
    coin_sound = load_sound('coin.wav')
    bg_image = load_image('background.png', (135, 206, 235), (WIDTH, HEIGHT))  # Sky blue fallback

    # Colors
    GROUND_COLOR = (222, 184, 135)

    highscore = load_highscore()

    # Game states: 'menu', 'playing', 'gameover', 'paused'
    state = 'menu'
    score = 0
    paused = False

    # Particles for effects
    particles = []

    def reset_game():
        nonlocal bird, pipes, coins, particles, score, state, paused
        bird = Bird(BIRD_X, HEIGHT//2 - BIRD_HEIGHT//2)
        pipes = []
        coins = []
        particles = []
        for i in range(2):
            pipes.append(Pipe(WIDTH + i * PIPE_SPACING + 200))
        score = 0
        state = 'playing'
        paused = False

    bird = Bird(BIRD_X, HEIGHT//2 - BIRD_HEIGHT//2)
    pipes = [Pipe(WIDTH + 150), Pipe(WIDTH + 150 + PIPE_SPACING)]
    coins = []
    particles = []
    running = True

    just_started_cooldown = 0

    while running:
        dt = clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_SPACE, pygame.K_UP):
                    if state == 'menu':
                        reset_game()
                        just_started_cooldown = 10
                    elif state == 'playing' and just_started_cooldown == 0 and not paused:
                        bird.flap()
                    elif state == 'gameover':
                        reset_game()
                        just_started_cooldown = 10
                if event.key == pygame.K_p and state == 'playing':
                    paused = not paused
                if event.key == pygame.K_ESCAPE:
                    running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if state == 'menu':
                        reset_game()
                        just_started_cooldown = 10
                    elif state == 'playing' and just_started_cooldown == 0 and not paused:
                        bird.flap()
                    elif state == 'gameover':
                        reset_game()
                        just_started_cooldown = 10

        # Update
        if state == 'playing' and not paused:
            if just_started_cooldown > 0:
                just_started_cooldown -= 1
            bird.update()

            # Difficulty scaling
            pipe_speed = PIPE_SPEED_BASE + score // 10

            # Spawn pipes
            if len(pipes) == 0 or (pipes[-1].x < WIDTH - PIPE_SPACING):
                pipes.append(Pipe(WIDTH + 20))
                # Spawn coin per pipe
                if random.random() < 0.5:
                    coin_y = random.randint(pipes[-1].gap_y + 20, pipes[-1].gap_y + PIPE_GAP - 20)
                    coins.append(Coin(WIDTH + 20, coin_y))

            # Update pipes
            for p in pipes:
                p.update(pipe_speed)
            pipes = [p for p in pipes if not p.offscreen()]

            # Update coins
            for c in coins:
                c.update(pipe_speed)
            coins = [c for c in coins if not c.offscreen()]

            # Update particles
            for p in particles:
                p.update()
            particles = [p for p in particles if p.lifetime > 0]

            # Collisions: bird with pipes
            bird_rect = pygame.Rect(int(bird.x), int(bird.y), bird.w, bird.h)
            hit = False
            for p in pipes:
                if bird_rect.colliderect(p.top_rect()) or bird_rect.colliderect(p.bottom_rect()):
                    hit = True
                if not p.passed and p.x + p.w < bird.x:
                    p.passed = True
                    score += 1
                    if score_sound:
                        score_sound.play()

            # Collisions: bird with coins
            for c in coins[:]:
                if bird_rect.colliderect(c.rect):
                    score += COIN_BONUS
                    coins.remove(c)
                    particles.extend([Particle(c.x, c.y) for _ in range(5)])  # Spark effect
                    if coin_sound:
                        coin_sound.play()

            # Collisions: floor/ceiling
            if bird.y + bird.h >= HEIGHT - FLOOR_HEIGHT or bird.y <= 0:
                hit = True

            if hit:
                state = 'gameover'
                if hit_sound:
                    hit_sound.play()
                if score > highscore:
                    highscore = score
                    save_highscore(highscore)

        # Draw
        screen.blit(bg_image, (0, 0))  # Background
        pygame.draw.circle(screen, (255, 255, 0), (WIDTH - 60, 60), 28)  # Sun

        # Draw pipes
        for p in pipes:
            p.draw(screen)

        # Draw coins
        for c in coins:
            c.draw(screen)

        # Draw particles
        for p in particles:
            p.draw(screen)

        # Draw ground
        pygame.draw.rect(screen, GROUND_COLOR, (0, HEIGHT - FLOOR_HEIGHT, WIDTH, FLOOR_HEIGHT))

        # Draw bird
        bird.draw(screen)

        # HUD
        if state == 'menu':
            draw_text_center(screen, "Flappy (Pygame) - Pro", 36, HEIGHT//3)
            draw_text_center(screen, "Press SPACE or Click to start", 20, HEIGHT//2)
            draw_text_center(screen, f"High score: {highscore}", 20, HEIGHT//2 + 40)
            draw_text_center(screen, "P to pause, ESC to quit", 14, HEIGHT - 20, color=(50,50,50))
        elif state == 'playing':
            draw_text_center(screen, str(score), 48, 60)
            if paused:
                draw_text_center(screen, "Paused - Press P to resume", 24, HEIGHT//2, color=(255,0,0))
        elif state == 'gameover':
            draw_text_center(screen, "Game Over", 42, HEIGHT//3)
            draw_text_center(screen, f"Score: {score}", 28, HEIGHT//2)
            draw_text_center(screen, f"High Score: {highscore}", 22, HEIGHT//2 + 40)
            draw_text_center(screen, "Press SPACE or Click to restart", 18, HEIGHT//2 + 100)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()  