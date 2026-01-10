import bpy
import blf
import time
from .drawing import draw_rounded_rect, draw_text
from ..core.theme import Theme

def draw_info_block(x, y, title, lines, show_until_map=None):
    padding = Theme.PADDING; line_h = Theme.FONT_SIZE_NORMAL + 4; max_w = 0
    blf.size(0, Theme.FONT_SIZE_HEADER); w, _ = blf.dimensions(0, title); max_w = w
    blf.size(0, Theme.FONT_SIZE_NORMAL)
    for row in lines:
        label, val = row[0], row[1]; hint = row[2] if len(row) > 2 else ""
        tw, _ = blf.dimensions(0, f"{label}: {str(val)} {hint}"); max_w = max(max_w, tw + 20)
    width = max_w + padding * 2; height = len(lines) * line_h + Theme.FONT_SIZE_HEADER + padding * 2 + 10
    draw_rounded_rect(x, y, width, height, Theme.COLOR_BG, Theme.COLOR_BORDER, Theme.CORNER_RADIUS)
    draw_rounded_rect(x, y, 3, height, Theme.COLOR_INFO, (0,0,0,0), 0)
    draw_text(f"# {title}", x + padding + 5, y - padding - Theme.FONT_SIZE_HEADER, size=Theme.FONT_SIZE_HEADER, color=Theme.COLOR_INFO)
    curr_y = y - padding - Theme.FONT_SIZE_HEADER - 10
    for row in lines:
        label, val = row[0], row[1]; hint = row[2] if len(row) > 2 else ""; col = Theme.COLOR_TEXT
        if show_until_map and label in show_until_map and time.time() < show_until_map[label]: col = Theme.COLOR_WARNING
        val_str = f"{val[0]:.2f}" if isinstance(val, tuple) and len(val) == 3 else str(val)
        draw_text(f"{label}: {val_str}", x + padding, curr_y - Theme.FONT_SIZE_NORMAL, size=Theme.FONT_SIZE_NORMAL, color=col)
        if hint:
            ht = f"[{hint}]"; blf.size(0, 12); hw, _ = blf.dimensions(0, ht)
            draw_text(ht, x + width - padding - hw, curr_y - Theme.FONT_SIZE_NORMAL, size=12, color=Theme.COLOR_SUBTEXT)
        curr_y -= line_h

def draw_option_set(x, y, options, current_option, show_until_time):
    if time.time() > show_until_time: return
    padding = 10; line_h = 20; width = 150; height = len(options) * line_h + padding * 2
    draw_rounded_rect(x, y, width, height, Theme.COLOR_BG, Theme.COLOR_BORDER, Theme.CORNER_RADIUS)
    draw_rounded_rect(x, y, 3, height, Theme.COLOR_INFO, (0,0,0,0), 0)
    curr_y = y - padding
    for opt in options:
        col = Theme.COLOR_SUCCESS if opt == current_option else Theme.COLOR_SUBTEXT
        draw_text(opt, x + padding, curr_y - 14, size=14, color=col)
        curr_y -= line_h
