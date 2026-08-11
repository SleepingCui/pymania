# PyMania

A lightweight osu!mania 4K visualization tool built with Python + pygame.

## Features

- 4K falling-note animation with adjustable scroll speed and offset
- Supports note clipping at the judgment line
- Built-in hit sounds with independent volume controls for music and hitsounds
- Supports both GUI (Tkinter) and CLI launch methods

## Dependencies

- Python 3.9+
- Install with: `pip install -r requirements.txt`

## Usage

### GUI

```bash
python main.py
```

### CLI

```bash
python main.py -m beatmap.osu [options]
```

| Option | Description | Default |
| ------ | ----------- | ------- |
| `-m, --map` | Beatmap file path | - |
| `-s, --speed` | Scroll speed | `1.5` |
| `-o, --offset` | Time offset (ms) | `0` |
| `-H, --height` | Canvas height | `720` |
| `-c, --clip` | Notes disappear at judgment line | Off |
| `--music-vol` | Music volume (0–100) | `100` |
| `--hit-vol` | Hitsound volume (0–100) | `80` |

### License
MIT