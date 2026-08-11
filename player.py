import os
import sys
import pygame
from constants import CANVAS_WIDTH, HIT_POSITION
from osu_parser import parse_osu_file
from renderer import count_hit_notes, draw_frame, update_notes


def run_pure_pygame(map_path, audio_path, speed, offset, height, clip, music_vol, hit_vol):
    notes, key_count, meta, auto_audio, log_msg = parse_osu_file(map_path)
    print(log_msg)
    if notes is None:
        sys.exit(1)

    if not audio_path:
        if auto_audio:
            osu_dir = os.path.dirname(os.path.abspath(map_path))
            audio_path = os.path.join(osu_dir, auto_audio)
        else:
            print("audio file not found!")
            sys.exit(1)

    if not os.path.exists(audio_path):
        print(f"audio file not found: {audio_path}")
        sys.exit(1)

    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.init()
    pygame.mixer.set_num_channels(32)
    pygame.mixer.music.load(audio_path)
    pygame.mixer.music.set_volume(music_vol / 100.0)
    bgm_sound = pygame.mixer.Sound(audio_path)
    duration = bgm_sound.get_length()

    hitsound_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hit.ogg")
    hitsound = pygame.mixer.Sound(hitsound_path) if os.path.exists(hitsound_path) else None
    if hitsound:
        hitsound.set_volume(hit_vol / 100.0)

    screen = pygame.display.set_mode((CANVAS_WIDTH, height))
    pygame.display.set_caption(f"{meta['Artist']} - {meta['Title']} {meta['Version']}")
    clock = pygame.time.Clock()

    hit_line_y = height - HIT_POSITION
    start_pos_sec = 0.0
    is_playing = True
    pygame.mixer.music.play(start=0.0)
    start_ticks = pygame.time.get_ticks()

    total_notes = len(notes)
    last_print_time = 0

    running = True
    while running:
        tick_time = clock.tick(120)
        fps = clock.get_fps()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    if is_playing:
                        start_pos_sec += (pygame.time.get_ticks() - start_ticks) / 1000.0
                        pygame.mixer.music.pause()
                        is_playing = False
                        print("\nPaused")
                    else:
                        pygame.mixer.music.unpause()
                        start_ticks = pygame.time.get_ticks()
                        is_playing = True
                        print("\nResumed")
                elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    delta = -5.0 if event.key == pygame.K_LEFT else 5.0
                    elapsed = (pygame.time.get_ticks() - start_ticks) / 1000.0 if is_playing else 0
                    start_pos_sec = max(0.0, min(duration, start_pos_sec + elapsed + delta))
                    pygame.mixer.music.play(start=start_pos_sec)
                    if not is_playing:
                        pygame.mixer.music.pause()
                    start_ticks = pygame.time.get_ticks()
                    curr_ms = (start_pos_sec * 1000.0) + offset
                    for n in notes:
                        n['hit'] = n['time'] < curr_ms
                    print(f"\n[Jump] Jumped to {start_pos_sec:.2f}s")
                elif event.key == pygame.K_UP:
                    speed = round(speed + 0.1, 1)
                    print(f"\nspeed={speed}")
                elif event.key == pygame.K_DOWN:
                    speed = max(0.2, round(speed - 0.1, 1))
                    print(f"\nspeed=: {speed}")
                elif event.key in (pygame.K_LEFTBRACKET, pygame.K_RIGHTBRACKET):
                    step = 1 if (pygame.key.get_mods() & pygame.KMOD_SHIFT) else 10
                    offset += (-step if event.key == pygame.K_LEFTBRACKET else step)
                    print(f"\n[Setting] Offset adjusted to: {offset} ms")

        curr_pos = start_pos_sec + ((pygame.time.get_ticks() - start_ticks) / 1000.0 if is_playing else 0.0)
        curr_time_ms = (curr_pos * 1000.0) + offset
        play_hitsound = update_notes(notes, is_playing, curr_time_ms)
        hit_count = count_hit_notes(notes)
        draw_frame(screen, notes, curr_time_ms, hit_line_y, speed, clip, height)
        if play_hitsound and hitsound:
            hitsound.play()
        pygame.display.flip()
        now_ticks = pygame.time.get_ticks()
        if now_ticks - last_print_time >= 100:
            last_print_time = now_ticks
            status_str = "PLAYING" if is_playing else "PAUSED"
            sys.stdout.write(
                f"\r{status_str},time={curr_pos:.2f}/{duration:.2f}s "
                f"fps={fps:.1f} tick={tick_time}ms "
                f"notes={hit_count}/{total_notes} speed={speed:.1f} offset={offset}ms   "
            )
            sys.stdout.flush()

    pygame.mixer.music.stop()
    pygame.quit()
