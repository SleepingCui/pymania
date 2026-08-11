import os
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText
import pygame
from constants import CANVAS_WIDTH, HIT_POSITION
from osu_parser import parse_osu_file
from renderer import count_hit_notes, draw_frame, update_notes


class UnifiedApp:
    def __init__(self, root):
        self.root = root
        self.root.title("o!m 4K Visualizer")
        self.root.geometry("520x620")
        self.root.resizable(False, False)

        self.is_running = False
        self.clock = None
        self.hitsound = None

        self.loop_thread = None
        self.ui_queue = queue.Queue()
        self.state = {
            'speed': 1.5,
            'offset': 0,
            'clip': False,
            'music_vol': 100,
            'hit_vol': 80,
        }

        f_frame = ttk.LabelFrame(root, text=" File Configuration ", padding=10)
        f_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(f_frame, text="Beatmap File:").grid(row=0, column=0, sticky="w")
        self.map_var = tk.StringVar()
        ttk.Entry(f_frame, textvariable=self.map_var, width=40).grid(row=1, column=0, padx=2)
        ttk.Button(f_frame, text="Browse...", command=self.browse_map).grid(row=1, column=1)

        # ttk.Label(f_frame, text="Audio File:").grid(row=2, column=0, sticky="w", pady=(5,0))
        self.audio_var = tk.StringVar()
        # ttk.Entry(f_frame, textvariable=self.audio_var, width=40).grid(row=3, column=0, padx=2)
        # ttk.Button(f_frame, text="Browse...", command=self.browse_audio).grid(row=3, column=1)

        p_frame = ttk.LabelFrame(root, text=" Parameter Settings", padding=10)
        p_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(p_frame, text="Music Volume:").grid(row=0, column=0, sticky="w")
        self.music_vol = tk.IntVar(value=100)
        m_scale = ttk.Scale(p_frame, from_=0, to=100, variable=self.music_vol, command=self.on_music_vol_change)
        m_scale.grid(row=0, column=1, sticky="ew", padx=5)
        self.m_lbl = ttk.Label(p_frame, text="100%")
        self.m_lbl.grid(row=0, column=2)

        ttk.Label(p_frame, text="Hit Volume:").grid(row=1, column=0, sticky="w", pady=5)
        self.hit_vol = tk.IntVar(value=80)
        h_scale = ttk.Scale(p_frame, from_=0, to=100, variable=self.hit_vol, command=self.on_hit_vol_change)
        h_scale.grid(row=1, column=1, sticky="ew", padx=5)
        self.h_lbl = ttk.Label(p_frame, text="80%")
        self.h_lbl.grid(row=1, column=2)

        ttk.Label(p_frame, text="Speed:").grid(row=2, column=0, sticky="w")
        self.speed_var = tk.DoubleVar(value=1.5)
        self.speed_entry = ttk.Entry(p_frame, textvariable=self.speed_var, width=10)
        self.speed_entry.grid(row=2, column=1, sticky="w", padx=5)
        self.speed_entry.bind('<KeyRelease>', lambda e: self._sync_speed())

        ttk.Label(p_frame, text="Offset/ms:").grid(row=3, column=0, sticky="w", pady=5)
        self.offset_var = tk.IntVar(value=0)
        self.offset_entry = ttk.Entry(p_frame, textvariable=self.offset_var, width=10)
        self.offset_entry.grid(row=3, column=1, sticky="w", padx=5)
        self.offset_entry.bind('<KeyRelease>', lambda e: self._sync_offset())

        ttk.Label(p_frame, text="Window Height:").grid(row=4, column=0, sticky="w")
        self.height_var = tk.IntVar(value=720)
        ttk.Entry(p_frame, textvariable=self.height_var, width=10).grid(row=4, column=1, sticky="w", padx=5)

        self.clip_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(p_frame, text="Disappear at hit line", variable=self.clip_var,
                        command=self.on_clip_toggle).grid(row=5, column=0, columnspan=2, sticky="w", pady=(5,0))

        p_frame.columnconfigure(1, weight=1)

        s_frame = ttk.LabelFrame(root, text="Status", padding=10)
        s_frame.pack(fill="x", padx=10, pady=5)

        self.lbl_status = ttk.Label(s_frame, text="Status: Not Running", font=("", 10, "bold"))
        self.lbl_status.grid(row=0, column=0, sticky="w")

        self.lbl_fps = ttk.Label(s_frame, text="FPS: -- | Tick: -- ms", font=("", 10))
        self.lbl_fps.grid(row=0, column=1, sticky="w", padx=10)

        self.lbl_notes = ttk.Label(s_frame, text="Note Count: 0 / 0", font=("", 10))
        self.lbl_notes.grid(row=1, column=0, sticky="w", pady=2)

        self.lbl_time = ttk.Label(s_frame, text="Playback Time: 00:00.00 / 00:00.00", font=("", 10))
        self.lbl_time.grid(row=1, column=1, sticky="w", padx=10, pady=2)

        btn_frame = ttk.Frame(root)
        btn_frame.pack(fill="x", padx=10, pady=5)

        self.start_btn = ttk.Button(btn_frame, text="Start / Restart Render", command=self.start_game)
        self.start_btn.pack(side="left", expand=True, fill="x", padx=2)

        self.stop_btn = ttk.Button(btn_frame, text="Stop Render", command=self.stop_game, state="disabled")
        self.stop_btn.pack(side="right", expand=True, fill="x", padx=2)

        log_frame = ttk.LabelFrame(root, text="logs" , padding=5)
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.log_area = ScrolledText(log_frame, wrap="word", height=6, font=("", 9))
        self.log_area.pack(fill="both", expand=True)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def log(self, text):
        self.log_area.insert(tk.END, text + "\n")
        self.log_area.see(tk.END)

    def browse_map(self):
        filename = filedialog.askopenfilename(filetypes=[("osu! Beatmap", "*.osu"), ("All Files", "*.*")])
        if filename:
            self.map_var.set(filename)

    def browse_audio(self):
        filename = filedialog.askopenfilename(filetypes=[("Audio Files", "*.mp3 *.wav *.ogg"), ("All Files", "*.*")])
        if filename:
            self.audio_var.set(filename)

    def on_music_vol_change(self, val):
        v = int(float(val))
        self.m_lbl.config(text=f"{v}%")
        self.state['music_vol'] = v

    def on_hit_vol_change(self, val):
        v = int(float(val))
        self.h_lbl.config(text=f"{v}%")
        self.state['hit_vol'] = v

    def on_clip_toggle(self):
        self.state['clip'] = bool(self.clip_var.get())

    def _sync_speed(self):
        try:
            self.state['speed'] = float(self.speed_var.get())
        except (ValueError, tk.TclError):
            pass

    def _sync_offset(self):
        try:
            self.state['offset'] = int(float(self.offset_var.get()))
        except (ValueError, tk.TclError):
            pass

    def start_game(self):
        if self.loop_thread is not None and self.loop_thread.is_alive():
            self.is_running = False
            self.loop_thread.join(timeout=3.0)

        map_path = self.map_var.get().strip()
        if not map_path or not os.path.exists(map_path):
            messagebox.showerror("Error", "Please select a valid .osu beatmap file!")
            return

        audio_path = self.audio_var.get().strip()

        self.notes, key_count, self.meta, auto_audio, log_msg = parse_osu_file(map_path)
        self.log(log_msg)

        if not audio_path and auto_audio:
            osu_dir = os.path.dirname(os.path.abspath(map_path))
            audio_path = os.path.join(osu_dir, auto_audio)
            self.log(f"[Auto-detect] Audio path: {audio_path}")

        if not os.path.exists(audio_path):
            messagebox.showerror("Error", f"Audio file not found: {audio_path}")
            return

        self.state['speed'] = float(self.speed_var.get())
        self.state['offset'] = int(self.offset_var.get())
        self.state['clip'] = bool(self.clip_var.get())
        self.state['music_vol'] = self.music_vol.get()
        self.state['hit_vol'] = self.hit_vol.get()

        self.audio_path = audio_path
        self.height = self.height_var.get()

        self.is_running = True
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.log("Starting render thread...")

        self.loop_thread = threading.Thread(target=self._game_loop_main, daemon=True)
        self.loop_thread.start()
        self._poll_ui()

    def _game_loop_main(self):
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        pygame.mixer.set_num_channels(32)
        try:
            pygame.mixer.music.load(self.audio_path)
            pygame.mixer.music.set_volume(self.state['music_vol'] / 100.0)
            self.duration = pygame.mixer.Sound(self.audio_path).get_length()

            hitsound_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hit.ogg")
            self.hitsound = pygame.mixer.Sound(hitsound_path) if os.path.exists(hitsound_path) else None
            if self.hitsound:
                self.hitsound.set_volume(self.state['hit_vol'] / 100.0)

            self.screen = pygame.display.set_mode((CANVAS_WIDTH, self.height))
            pygame.display.set_caption(self.meta['Title'])
            self.clock = pygame.time.Clock()

            self.hit_line_y = self.height - HIT_POSITION
            self.start_pos_sec = 0.0
            self.is_playing = True
            last_music_vol = last_hit_vol = -1.0

            pygame.mixer.music.play(start=0.0)
            self.start_ticks = pygame.time.get_ticks()
            last_push = 0

            while self.is_running:
                tick_time = self.clock.tick(120)
                fps = self.clock.get_fps()

                mv = self.state['music_vol'] / 100.0
                if mv != last_music_vol:
                    pygame.mixer.music.set_volume(mv)
                    last_music_vol = mv
                hv = self.state['hit_vol'] / 100.0
                if hv != last_hit_vol and self.hitsound:
                    self.hitsound.set_volume(hv)
                    last_hit_vol = hv

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.is_running = False
                        break
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.is_running = False
                            break
                        elif event.key == pygame.K_SPACE:
                            if self.is_playing:
                                self.start_pos_sec += (pygame.time.get_ticks() - self.start_ticks) / 1000.0
                                pygame.mixer.music.pause()
                                self.is_playing = False
                                self.ui_queue.put({'type': 'log', 'text': "[Control] Paused"})
                            else:
                                pygame.mixer.music.unpause()
                                self.start_ticks = pygame.time.get_ticks()
                                self.is_playing = True
                                self.ui_queue.put({'type': 'log', 'text': "[Control] Resumed"})
                        elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                            delta = -5.0 if event.key == pygame.K_LEFT else 5.0
                            elapsed = (pygame.time.get_ticks() - self.start_ticks) / 1000.0 if self.is_playing else 0
                            self.start_pos_sec = max(0.0, min(self.duration, self.start_pos_sec + elapsed + delta))
                            pygame.mixer.music.play(start=self.start_pos_sec)
                            if not self.is_playing:
                                pygame.mixer.music.pause()
                            self.start_ticks = pygame.time.get_ticks()
                            curr_ms = (self.start_pos_sec * 1000.0) + self.state['offset']
                            for n in self.notes:
                                n['hit'] = n['time'] < curr_ms
                            self.ui_queue.put({'type': 'log', 'text': f"[Jump] Jumped to {self.start_pos_sec:.2f}s"})
                        elif event.key == pygame.K_UP:
                            self.state['speed'] = round(self.state['speed'] + 0.1, 1)
                            self.ui_queue.put({'type': 'var', 'name': 'speed', 'value': self.state['speed']})
                            self.ui_queue.put({'type': 'log', 'text': f"[Setting] Speed: {self.state['speed']}"})
                        elif event.key == pygame.K_DOWN:
                            self.state['speed'] = max(0.2, round(self.state['speed'] - 0.1, 1))
                            self.ui_queue.put({'type': 'var', 'name': 'speed', 'value': self.state['speed']})
                            self.ui_queue.put({'type': 'log', 'text': f"[Setting] Speed: {self.state['speed']}"})
                        elif event.key in (pygame.K_LEFTBRACKET, pygame.K_RIGHTBRACKET):
                            step = 1 if (pygame.key.get_mods() & pygame.KMOD_SHIFT) else 10
                            self.state['offset'] += (-step if event.key == pygame.K_LEFTBRACKET else step)
                            self.ui_queue.put({'type': 'var', 'name': 'offset', 'value': self.state['offset']})
                            self.ui_queue.put({'type': 'log', 'text': f"[Setting] Offset: {self.state['offset']} ms"})

                if not self.is_running:
                    break

                curr_pos = self.start_pos_sec + ((pygame.time.get_ticks() - self.start_ticks) / 1000.0 if self.is_playing else 0.0)
                curr_time_ms = (curr_pos * 1000.0) + self.state['offset']

                play_hitsound = update_notes(self.notes, self.is_playing, curr_time_ms)
                hit_notes_count = count_hit_notes(self.notes)
                draw_frame(self.screen, self.notes, curr_time_ms, self.hit_line_y,
                           self.state['speed'], self.state['clip'], self.height)

                if play_hitsound and self.hitsound:
                    self.hitsound.play()

                pygame.display.flip()

                now_ticks = pygame.time.get_ticks()
                if now_ticks - last_push >= 100:
                    last_push = now_ticks
                    self.ui_queue.put({
                        'type': 'status',
                        'playing': self.is_playing,
                        'pos': curr_pos,
                        'dur': self.duration,
                        'fps': fps,
                        'tick': tick_time,
                        'hit': hit_notes_count,
                        'total': len(self.notes),
                    })
        except Exception as e:
            self.ui_queue.put({'type': 'log', 'text': f"Render thread exception: {e}"})
        finally:
            pygame.mixer.music.stop()
            pygame.quit()
            self.is_running = False
            self.ui_queue.put({'type': 'stopped'})

    def _poll_ui(self):
        try:
            while True:
                msg = self.ui_queue.get_nowait()
                mtype = msg['type']
                if mtype == 'status':
                    status_text = "Playing" if msg['playing'] else "Paused"
                    self.lbl_status.config(text=f"Status: {status_text}")
                    self.lbl_fps.config(text=f"FPS: {msg['fps']:.1f} | Tick: {msg['tick']} ms")
                    self.lbl_notes.config(text=f"Note Count: {msg['hit']} / {msg['total']}")
                    self.lbl_time.config(text=f"Time: {msg['pos']:.2f}s / {msg['dur']:.2f}s")
                elif mtype == 'log':
                    self.log(msg['text'])
                elif mtype == 'var':
                    if msg['name'] == 'speed':
                        self.speed_var.set(msg['value'])
                    elif msg['name'] == 'offset':
                        self.offset_var.set(msg['value'])
                elif mtype == 'stopped':
                    self.start_btn.config(state="normal")
                    self.stop_btn.config(state="disabled")
                    self.lbl_status.config(text="Status: Stopped")
                    self.lbl_fps.config(text="FPS: -- | Tick: -- ms")
                    self.log("Render window closed")
        except queue.Empty:
            pass

        if self.loop_thread is not None and self.loop_thread.is_alive():
            try:
                self.root.after(50, self._poll_ui)
            except tk.TclError:
                pass

    def stop_game(self):
        self.is_running = False
        if self.loop_thread is not None:
            self.loop_thread.join(timeout=3.0)

    def on_close(self):
        self.is_running = False
        if self.loop_thread is not None:
            self.loop_thread.join(timeout=3.0)
        self.root.destroy()
