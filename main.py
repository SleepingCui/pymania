import argparse
import sys
import tkinter as tk
from gui import UnifiedApp
from player import run_pure_pygame

def main():
    parser = argparse.ArgumentParser(description="osu!mania 4K Visualizer")
    parser.add_argument('-m', '--map', required=False, default=None, help="Path to .osu beatmap file")
    parser.add_argument('-a', '--audio', required=False, default=None, help="Path to audio file")
    parser.add_argument('-s', '--speed', type=float, default=1.5, help="Scroll Speed")
    parser.add_argument('-o', '--offset', type=int, default=0, help="Offset (ms)")
    parser.add_argument('-H', '--height', type=int, default=720, help="Canvas height")
    parser.add_argument('-c', '--clip', action='store_true', help="Notes disappear when reaching hit line")
    parser.add_argument('--music-vol', type=int, default=100, help="Background music volume (0-100)")
    parser.add_argument('--hit-vol', type=int, default=80, help="Hit sound volume (0-100)")
    args = parser.parse_args()

    if len(sys.argv) == 1 or args.map is None:
        root = tk.Tk()
        app = UnifiedApp(root)
        root.mainloop()
    else:
        run_pure_pygame(map_path=args.map,audio_path=args.audio,speed=args.speed,offset=args.offset,height=args.height,clip=args.clip,music_vol=args.music_vol,hit_vol=args.hit_vol)


if __name__ == "__main__":
    main()
