import pygame
from constants import CANVAS_WIDTH, COLUMN_COUNT, COLUMN_WIDTH, COLUMN_COLORS

def update_notes(notes, is_playing, curr_time_ms):
    play_hitsound = False
    for note in notes:
        if is_playing and not note['hit'] and curr_time_ms >= note['time']:
            note['hit'] = True
            play_hitsound = True
    return play_hitsound

def count_hit_notes(notes):
    return sum(1 for note in notes if note['hit'])

def draw_frame(screen, notes, curr_time_ms, hit_line_y, speed, clip, height):
    screen.fill((18, 18, 20))
    for i in range(1, COLUMN_COUNT):
        pygame.draw.line(screen, (40, 40, 40), (i * COLUMN_WIDTH, 0), (i * COLUMN_WIDTH, height), 1)

    for note in notes:
        y_start = hit_line_y - (note['time'] - curr_time_ms) * speed
        y_end = hit_line_y - (note['end_time'] - curr_time_ms) * speed

        if y_start > -100 and y_end < height + 100:
            color = COLUMN_COLORS[note['column']]
            x = note['column'] * COLUMN_WIDTH
            if note['is_ln']: 
                d_start = min(y_start, hit_line_y) if clip else y_start
                d_end = min(y_end, hit_line_y) if clip else y_end
                bh = d_start - d_end
                if bh > 0:
                    surf = pygame.Surface((COLUMN_WIDTH - 8, int(bh)), pygame.SRCALPHA)
                    surf.fill((*color, 100))
                    screen.blit(surf, (x + 4, d_end))
                    if d_end < hit_line_y:
                        pygame.draw.rect(screen, color, (x + 2, d_end, COLUMN_WIDTH - 4, 4))
                    if d_start <= hit_line_y and d_start - 12 >= 0:
                        pygame.draw.rect(screen, color, (x + 2, d_start - 12, COLUMN_WIDTH - 4, 12))
            else:
                if clip and y_start >= hit_line_y:
                    continue
                pygame.draw.rect(screen, color, (x + 2, y_start - 14, COLUMN_WIDTH - 4, 14))
    pygame.draw.line(screen, (255, 102, 170), (0, hit_line_y), (CANVAS_WIDTH, hit_line_y), 3)
