import pygame
import random

LANES = 4
LANE_KEYS = [pygame.K_d, pygame.K_f, pygame.K_j, pygame.K_k]
LANE_LABELS = ['D', 'F', 'J', 'K']
LANE_COLORS = [(220,80,80),(80,180,220),(100,220,100),(220,180,60)]

HOLD_FRAMES = 60  # Task 2: hold notes must be held for 1 second (60 frames at 60 FPS)

class Note:
    WIDTH = 70
    HEIGHT = 20
    def __init__(self, lane, y=-30, speed=4, hold=False):  # Task 2: added hold flag
        self.lane = lane
        self.y = y
        self.speed = speed
        self.hit = False
        self.missed = False
        self.hold = hold  # Task 2: True for a long (hold) note
        self.holding = False  # Task 2: player is currently holding this note
        self.held = 0  # Task 2: frames held so far
        self.grade = None  # Task 2: (grade, pts, color) from the initial press, scored on completion

    def tail_length(self):  # Task 2: remaining tail in pixels = distance still to travel over the hit line
        if not self.hold:  # Task 2
            return 0  # Task 2
        return self.speed * (HOLD_FRAMES - self.held)  # Task 2

    def update(self):
        if self.holding:  # Task 2: head stays pinned on the hit line while the tail drains
            self.held += 1  # Task 2
        else:  # Task 2
            self.y += self.speed

    def get_rect(self, lane_x):
        return pygame.Rect(lane_x - self.WIDTH//2, int(self.y), self.WIDTH, self.HEIGHT)
