# Task 1: Sound Effects on Hit - procedurally generated hit sounds (no asset files or numpy needed)
import math
import random
from array import array

import pygame


def _render(samples_fn, duration):  # Task 1: turn a mono sample function into a Sound matching the mixer format
    freq, size, channels = pygame.mixer.get_init()
    n = int(freq * duration)
    typecode = {8: 'b', -8: 'b', 16: 'h', -16: 'h', 32: 'i', -32: 'i'}.get(size, 'h')
    peak = 2 ** (abs(size) - 1) - 1
    buf = array(typecode)
    for i in range(n):
        t = i / freq
        attack = min(1.0, i / (freq * 0.003))  # Task 1: 3 ms fade-in avoids clicks
        v = int(max(-1.0, min(1.0, samples_fn(t) * attack)) * peak * 0.5)
        buf.extend([v] * channels)
    return pygame.mixer.Sound(buffer=buf.tobytes())


def _beep(pitch, duration, decay):  # Task 1: bright tone with a harmonic, exponential decay
    return _render(lambda t: (math.sin(2 * math.pi * pitch * t)
                              + 0.35 * math.sin(2 * math.pi * pitch * 2 * t)) * math.exp(-t * decay),
                   duration)


def _drum(duration=0.16):  # Task 1: kick-style drum - pitch sweep plus a little noise
    rng = random.Random(51)
    def fn(t):
        pitch = 60 + 140 * math.exp(-t * 30)
        body = math.sin(2 * math.pi * pitch * t) * math.exp(-t * 18)
        noise = rng.uniform(-1, 1) * 0.25 * math.exp(-t * 60)
        return body + noise
    return _render(fn, duration)


def load_hit_sounds():  # Task 1: one sound per grade; returns {} if audio is unavailable
    if not pygame.mixer.get_init():
        return {}
    try:
        return {
            "PERFECT": _beep(1320, 0.14, 22),
            "GREAT": _beep(880, 0.12, 26),
            "OK": _drum(),
        }
    except pygame.error:
        return {}
