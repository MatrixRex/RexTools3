import gpu
from gpu_extras.batch import batch_for_shader
import blf
import time


_shader = gpu.shader.from_builtin('UNIFORM_COLOR')

# ---------- Basic Primitives ----------

def draw_line(start, end, color=(1, 1, 1, 1)):
    batch = batch_for_shader(_shader, 'LINES', {"pos": [start, end]})
    _shader.bind()
    _shader.uniform_float("color", color)
    batch.draw(_shader)

def draw_point(center, radius=4, color=(1, 0, 0, 1)):
    x, y = center
    verts = [
        (x - radius, y - radius),
        (x + radius, y - radius),
        (x + radius, y + radius),
        (x - radius, y + radius),
    ]
    batch = batch_for_shader(_shader, 'TRI_FAN', {"pos": verts})
    _shader.bind()
    _shader.uniform_float("color", color)
    batch.draw(_shader)

def draw_text(text, position, size=12, color=(1, 1, 1, 1)):
    font_id = 0
    blf.position(font_id, position[0], position[1], 0)
    blf.size(font_id, size)
    # GPU text color (no alpha blend): requires bgl (deprecated in 4.5), use default white for now
    blf.draw(font_id, text)

# ---------- HUD Block Drawing ----------

def draw_info_block(x, y, title, lines, line_gap=36, value_col_offset=180, bar_width=100, show_until_map=None):
    """
    - lines = list of (label, value, key)
      where `value` can be:
        - str or number: draw as normal
        - tuple of 3 (v, min, max): draw as progress bar
        - tuple of (options_list, current_option): draw as option set
    - show_until_map: dict of {label: show_until_time} to control fading logic per-option
    """
    font_id = 0
    blf.size(font_id, 16)
    draw_colored_text(f"» {title}", (x, y), color=(1, 1, 1, 1), size=16)

    start_y = y - 30
    blf.size(font_id, 13)

    for i, (label, value, key) in enumerate(lines):
        line_y = start_y - i * line_gap

        draw_text(label, (x, line_y))
        if key:
            draw_text(key, (x, line_y - 12), size=11)

        # Handle progress bar
        if isinstance(value, (tuple, list)) and len(value) == 3 and all(isinstance(v, (int, float)) for v in value):
            val, min_val, max_val = value
            bar_x = x + value_col_offset
            bar_y = line_y - 6
            draw_progress_bar(bar_x, bar_y, bar_width, 16, val, min_val, max_val, label="")

        # Handle option set: list of options + selected option
        elif isinstance(value, (tuple, list)) and len(value) == 2 and isinstance(value[0], list):
            options, selected = value
            show_until = show_until_map[label] if show_until_map and label in show_until_map else None
            od_x = x + value_col_offset
            od_y = line_y - 6
            draw_option_set(od_x, od_y, options, selected, show_until)

        # Fallback: regular value string
        else:
            val_y = line_y - 6
            draw_colored_text(str(value), (x + value_col_offset, val_y), color=color_from_value(value))



def draw_colored_text(text, position, color=(1, 1, 1, 1), size=14):
    font_id = 0
    blf.color(font_id, *color)
    blf.position(font_id, position[0], position[1], 0)
    blf.size(font_id, size)
    blf.draw(font_id, text)
    
def draw_progress_bar(x, y, width, height, value, min_value, max_value, label=""):
    clamped = max(min_value, min(value, max_value))
    norm = (clamped - min_value) / (max_value - min_value) if max_value != min_value else 0.0
    fill_width = int(width * norm)

    # Background
    bg_verts = [
        (x, y), (x + width, y),
        (x + width, y + height), (x, y + height),
    ]
    draw_filled_rect(bg_verts, color=(0.2, 0.2, 0.2, 0.8))

    # Fill
    fill_verts = [
        (x, y), (x + fill_width, y),
        (x + fill_width, y + height), (x, y + height),
    ]
    draw_filled_rect(fill_verts, color=(0.4, 0.8, 0.4, 1.0))

    # Always show numeric value (and label if given)
    value_text = f"{label + ': ' if label else ''}{value:.3f}"
    font_id = 0
    blf.size(font_id, 12)
    text_width, text_height = blf.dimensions(font_id, value_text)
    center_x = x + (width - text_width) / 2
    center_y = y + (height - text_height) / 2
    blf.position(font_id, center_x, center_y, 0)
    blf.draw(font_id, value_text)




def draw_option_set(x, y, options, current_option, show_until_time=None):
    """
    Always draw current option.
    Only show all options if within timeout window.
    """
    font_id = 0
    now = time.time()
    show_all = show_until_time and now < show_until_time

    spacing = 16
    inner_padding = 6
    outer_padding = 4
    height = 22 + 2 * outer_padding
    cursor_x = x

    # Ensure we always show the current option
    display_options = options if show_all else [current_option]

    for opt in display_options:
        is_highlighted = (opt == current_option and show_all)

        font_size = 16 if is_highlighted else 14
        blf.size(font_id, font_size)
        text_width, _ = blf.dimensions(font_id, opt)
        width = text_width + 2 * inner_padding

        # Box
        if is_highlighted:
            box_x = cursor_x - outer_padding
            box_y = y - outer_padding
            box_w = width + 2 * outer_padding
            box_h = height

            draw_outline_rect(
                verts=[
                    (box_x, box_y),
                    (box_x + box_w, box_y),
                    (box_x + box_w, box_y + box_h),
                    (box_x, box_y + box_h),
                ],
                color=(1, 1, 1, 0.6)
            )

        # Color and draw text
        text_col = (0.682, 0.914, 0.976, 1) if is_highlighted else (1, 1, 1, 1)
        draw_colored_text(opt, (cursor_x + inner_padding, y + 4), color=text_col)

        cursor_x += width + spacing


def draw_filled_rect(verts, color=(1, 1, 1, 1)):
    """Helper to draw filled quad with given 4 verts (clockwise or CCW)."""
    import gpu
    gpu.state.blend_set('ALPHA')
    batch = batch_for_shader(_shader, 'TRI_FAN', {"pos": verts})
    _shader.bind()
    _shader.uniform_float("color", color)
    batch.draw(_shader)
    gpu.state.blend_set('NONE')


def draw_outline_rect(verts, color=(1, 1, 1, 1)):
    """
    Draw a clean outline box.
    """
    batch = batch_for_shader(_shader, 'LINE_LOOP', {"pos": verts})
    _shader.bind()
    _shader.uniform_float("color", color)
    batch.draw(_shader)


def color_from_value(value):
    if isinstance(value, str):
        v = value.lower()
        if v == "true":
            return (0.3, 1.0, 0.3, 1)
        if v == "false":
            return (1.0, 0.3, 0.3, 1)
    return (1, 1, 1, 1)
