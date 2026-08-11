import os
from constants import COLUMN_COUNT

def parse_osu_file(osu_path):
    notes = []
    key_count = 4
    meta = {'Title': 'Unknown', 'Artist': 'Unknown', 'Version': 'Normal'}
    audio_filename = None

    if not os.path.exists(osu_path):
        return None, key_count, meta, None, f"Beatmap file not found: {osu_path}"

    with open(osu_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    is_general = is_hit_objects = is_difficulty = is_metadata = False

    for line in lines:
        line = line.strip()
        if not line or line.startswith('//'):
            continue

        if line.startswith('['):
            is_general = (line == '[General]')
            is_hit_objects = (line == '[HitObjects]')
            is_difficulty = (line == '[Difficulty]')
            is_metadata = (line == '[Metadata]')
            continue

        if is_general and ':' in line:
            k, v = line.split(':', 1)
            if k.strip() == 'AudioFilename':
                audio_filename = v.strip()

        if is_metadata and ':' in line:
            k, v = line.split(':', 1)
            k, v = k.strip(), v.strip()
            if k in meta:
                meta[k] = v

        if is_difficulty and line.startswith('CircleSize'):
            key_count = int(line.split(':')[1].strip())

        if is_hit_objects:
            parts = line.split(',')
            if len(parts) < 4:
                continue

            x = int(parts[0])
            t = int(parts[2])
            type_val = int(parts[3])

            column = int(max(0, min(x, 512)) * key_count / 512)
            column = min(column, COLUMN_COUNT - 1)

            end_time = t
            if type_val & 128:
                end_params = parts[5].split(':')
                end_time = int(end_params[0])

            notes.append({
                'column': column,
                'time': t,
                'end_time': end_time,
                'is_ln': end_time > t,
                'hit': False
            })

    notes.sort(key=lambda n: n['time'])
    log_msg = f"title: {meta['Title']}\nKeyCount: {key_count}\nTotal Notes: {len(notes)}"
    return notes, key_count, meta, audio_filename, log_msg
