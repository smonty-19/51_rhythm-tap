import pygame
import random
from game.beat import Note, LANES, LANE_KEYS, LANE_LABELS, LANE_COLORS
from game.beat import HOLD_FRAMES  # Task 2: hold note duration
from game.sounds import load_hit_sounds  # Task 1: hit sound effects

WIDTH, HEIGHT = 480, 640
FPS = 60
HIT_Y = HEIGHT - 80
HIT_WINDOW = 30
HOLD_CHANCE = 0.2  # Task 2: fraction of spawned notes that are hold notes
HOLD_GRACE = 4  # Task 2: releasing this many frames early still counts as a full hold
HOLD_LANE_GAP = 15  # Task 2: extra frames a lane stays blocked after a hold note so notes don't overlap its tail
BG = (15, 10, 25)
LANE_W = WIDTH // LANES
BPM = 120  # Task 3: default tempo - one note spawns on every beat
SPEEDUP_EVERY_BEATS = 16  # Task 3: difficulty ramp now happens every 4 bars instead of on a frame timer

class GameEngine:
    def __init__(self, bpm=BPM):  # Task 3: tempo can be passed in (see main.py)
        self.bpm = bpm  # Task 3
        self.beat_frames = FPS * 60 / bpm  # Task 3: frames per beat (30.0 at 120 BPM, fractional for other tempos)
        pygame.mixer.pre_init(44100, -16, 2, 256)  # Task 1: small buffer so hit sounds play with low latency
        pygame.init()
        try:  # Task 1: keep the game playable (silently) if no audio device is available
            pygame.mixer.init()
        except pygame.error:
            pass
        self.hit_sounds = load_hit_sounds()  # Task 1: {"PERFECT"/"GREAT"/"OK": Sound}
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Rhythm Tap")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 26, bold=True)
        self.big_font = pygame.font.SysFont("monospace", 44, bold=True)
        self.reset()

    def reset(self):
        self.notes = []
        self.score = 0
        self.combo = 0
        self.max_combo = 0
        self.misses = 0
        self.next_beat = self.beat_frames  # Task 3: exact (fractional) frame of the next beat; replaces spawn_timer/spawn_interval
        self.beat_count = 0  # Task 3: beats elapsed since the start
        self.beat_flash = 0  # Task 3: frames left on the HUD beat indicator flash
        self.speed = 5
        self.frame = 0
        self.feedback = []  # (text, color, ttl, x, y)
        self.game_over = False
        self.lane_busy_until = [0] * LANES  # Task 2: frame until which each lane is blocked by a hold tail

    def spawn_note(self, late=0.0):  # Task 3: late = how many frames after the exact beat this spawn runs
        free = [l for l in range(LANES) if self.frame >= self.lane_busy_until[l]]  # Task 2: skip lanes under a hold tail
        if not free:  # Task 2
            return  # Task 2
        lane = random.choice(free)  # Task 2: was random.randint over all lanes
        hold = random.random() < HOLD_CHANCE  # Task 2
        y = -30 + self.speed * late  # Task 3: place the note where it would be had it spawned exactly on the beat
        self.notes.append(Note(lane, y=y, speed=self.speed, hold=hold))  # Task 2: pass hold flag / Task 3: beat-exact y
        if hold:  # Task 2
            self.lane_busy_until[lane] = self.frame + HOLD_FRAMES + HOLD_LANE_GAP  # Task 2

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.reset()
                elif not self.game_over:
                    for i, key in enumerate(LANE_KEYS):
                        if event.key == key:
                            self.process_tap(i)
            if event.type == pygame.KEYUP and not self.game_over:  # Task 2: releasing a key can end a hold
                for i, key in enumerate(LANE_KEYS):  # Task 2
                    if event.key == key:  # Task 2
                        self.process_release(i)  # Task 2
        return True

    def process_tap(self, lane):
        # Find closest note in this lane near hit zone
        best = None
        best_dist = 9999
        for note in self.notes:
            if note.lane == lane and not note.hit and not note.missed and not note.holding:  # Task 2: ignore notes already being held
                dist = abs(note.y + Note.HEIGHT//2 - HIT_Y)
                if dist < best_dist:
                    best_dist = dist
                    best = note
        lane_x = lane * LANE_W + LANE_W // 2
        if best and best_dist <= HIT_WINDOW:
            if best_dist < 8:
                grade, pts = "PERFECT", 300
                col = (255, 220, 0)
            elif best_dist < 18:
                grade, pts = "GREAT", 200
                col = (100, 220, 100)
            else:
                grade, pts = "OK", 100
                col = (180, 180, 255)
            if best.hold:  # Task 2: start holding - grade is locked in now but only scored after 1 second
                best.holding = True  # Task 2
                best.grade = (grade, pts, col)  # Task 2
                best.y = HIT_Y - Note.HEIGHT // 2  # Task 2: snap head onto the hit line
                self.feedback.append(["HOLD!", col, 25, lane_x, HIT_Y - 30])  # Task 2
                return  # Task 2
            best.hit = True  # Task 2: moved below grading so hold notes aren't marked hit on press
            self.score_hit(grade, pts, col, lane_x)  # Task 2: scoring moved into score_hit() so hold notes can reuse it
        else:
            self.combo = 0
            self.feedback.append(["MISS", (220,60,60), 40, lane_x, HIT_Y - 30])

    def score_hit(self, grade, pts, col, lane_x):  # Task 2: shared scoring for taps and completed holds (moved from process_tap)
        self.combo += 1
        self.max_combo = max(self.max_combo, self.combo)
        self.score += pts * max(1, self.combo // 5)
        self.feedback.append([grade, col, 40, lane_x, HIT_Y - 30])
        sound = self.hit_sounds.get(grade)  # Task 1: play the sound for this grade
        if sound:  # Task 1
            sound.play()  # Task 1

    def process_release(self, lane):  # Task 2: key released - finish or break an active hold in this lane
        for note in self.notes:  # Task 2
            if note.lane == lane and note.holding:  # Task 2
                if note.held >= HOLD_FRAMES - HOLD_GRACE:  # Task 2
                    self.complete_hold(note)  # Task 2
                else:  # Task 2: let go too early - the note is dropped and counts as a miss
                    note.holding = False  # Task 2
                    note.missed = True  # Task 2
                    self.misses += 1  # Task 2
                    self.combo = 0  # Task 2
                    lane_x = lane * LANE_W + LANE_W // 2  # Task 2
                    self.feedback.append(["MISS", (220,60,60), 40, lane_x, HIT_Y - 30])  # Task 2

    def complete_hold(self, note):  # Task 2: held for the full second - award the grade from the initial press
        note.holding = False  # Task 2
        note.hit = True  # Task 2
        grade, pts, col = note.grade  # Task 2
        self.score_hit(grade, pts, col, note.lane * LANE_W + LANE_W // 2)  # Task 2

    def update(self):
        if self.game_over: return
        self.frame += 1
        while self.frame >= self.next_beat:  # Task 3: spawn on every beat of the BPM (replaces the spawn timer)
            self.spawn_note(late=self.frame - self.next_beat)  # Task 3
            self.next_beat += self.beat_frames  # Task 3: accumulate exact beat times so fractional beats never drift
            self.beat_count += 1  # Task 3
            self.beat_flash = 8  # Task 3
            if self.beat_count % SPEEDUP_EVERY_BEATS == 0:  # Task 3: speed-up on bar boundaries (was frame % 600)
                self.speed = min(10, self.speed + 0.5)
        self.beat_flash = max(0, self.beat_flash - 1)  # Task 3

        for note in self.notes:
            note.update()
            if note.holding and note.held >= HOLD_FRAMES:  # Task 2: tail fully drained while still held
                self.complete_hold(note)  # Task 2
            if not note.hit and not note.missed and note.y > HIT_Y + HIT_WINDOW + Note.HEIGHT:
                note.missed = True
                self.misses += 1
                self.combo = 0

        self.notes = [n for n in self.notes if not (n.hit or n.missed and n.y > HEIGHT + 10)]
        self.feedback = [[t,c,ttl-1,x,y] for t,c,ttl,x,y in self.feedback if ttl > 1]

        if self.misses >= 15:
            self.game_over = True

    def draw(self):
        self.screen.fill(BG)
        # Lane dividers
        for i in range(LANES + 1):
            pygame.draw.line(self.screen, (40,40,60), (i*LANE_W,0), (i*LANE_W,HEIGHT), 1)

        # Hit line
        pygame.draw.line(self.screen, (80,80,100), (0,HIT_Y), (WIDTH,HIT_Y), 2)
        for i in range(LANES):
            lx = i*LANE_W + LANE_W//2
            pygame.draw.rect(self.screen, LANE_COLORS[i],
                pygame.Rect(lx - Note.WIDTH//2, HIT_Y - 12, Note.WIDTH, 24), border_radius=6)
            lbl = self.font.render(LANE_LABELS[i], True, (20,20,20))
            self.screen.blit(lbl, (lx - lbl.get_width()//2, HIT_Y - 10))

        # Notes
        for note in self.notes:
            if note.hit: continue
            lx = note.lane * LANE_W + LANE_W // 2
            rect = note.get_rect(lx)
            if note.hold:  # Task 2: draw tail above the head; greyed out once missed/dropped
                col = (90, 90, 90) if note.missed else LANE_COLORS[note.lane]  # Task 2
                tail_len = int(note.tail_length())  # Task 2
                tail = pygame.Rect(lx - 14, rect.centery - tail_len, 28, tail_len)  # Task 2
                pygame.draw.rect(self.screen, tuple(c * 3 // 5 for c in col), tail, border_radius=8)  # Task 2
                pygame.draw.rect(self.screen, col, rect, border_radius=5)  # Task 2
                if note.holding:  # Task 2: white outline while being held
                    pygame.draw.rect(self.screen, (255, 255, 255), rect.inflate(6, 6), 2, border_radius=7)  # Task 2
                continue  # Task 2
            pygame.draw.rect(self.screen, LANE_COLORS[note.lane], rect, border_radius=5)

        # Feedback
        for text, color, ttl, x, y in self.feedback:
            surf = self.font.render(text, True, color)
            alpha = min(255, ttl * 7)
            surf.set_alpha(alpha)
            self.screen.blit(surf, (x - surf.get_width()//2, y))

        # HUD
        sc = self.font.render(f"Score: {self.score}", True, (220,220,220))
        co = self.font.render(f"Combo: {self.combo}x", True, (255,220,80))
        mi = self.font.render(f"Misses: {self.misses}/15", True, (220,100,100))
        self.screen.blit(sc, (10, 10))
        self.screen.blit(co, (10, 40))
        self.screen.blit(mi, (WIDTH - 170, 10))
        bpm = self.font.render(f"BPM: {self.bpm:g}", True, (180,180,220))  # Task 3: show tempo
        self.screen.blit(bpm, (WIDTH - 170, 40))  # Task 3
        dot = (255,255,255) if self.beat_flash else (70,70,90)  # Task 3: indicator flashes on every beat
        pygame.draw.circle(self.screen, dot, (WIDTH - 192, 55), 6)  # Task 3

        if self.game_over:
            ov = pygame.Surface((WIDTH,HEIGHT), pygame.SRCALPHA)
            ov.fill((0,0,0,160))
            self.screen.blit(ov,(0,0))
            msg = self.big_font.render("GAME OVER", True, (220,60,60))
            sc_msg = self.font.render(f"Final Score: {self.score}  Max Combo: {self.max_combo}x", True, (200,200,200))
            restart = self.font.render("Press R to Restart", True, (160,160,160))
            self.screen.blit(msg, (WIDTH//2-msg.get_width()//2, HEIGHT//2-70))
            self.screen.blit(sc_msg, (WIDTH//2-sc_msg.get_width()//2, HEIGHT//2))
            self.screen.blit(restart, (WIDTH//2-restart.get_width()//2, HEIGHT//2+50))
        pygame.display.flip()

    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()
