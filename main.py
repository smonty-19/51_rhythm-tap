import sys  # Task 3: read optional BPM from the command line
from game.game_engine import GameEngine, BPM  # Task 3: import default BPM

if __name__ == "__main__":
    bpm = float(sys.argv[1]) if len(sys.argv) > 1 else BPM  # Task 3: e.g. `python main.py 140`
    engine = GameEngine(bpm=bpm)  # Task 3: pass tempo to the engine
    engine.run()
