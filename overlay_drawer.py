import gpu
from gpu_extras.batch import batch_for_shader
import blf

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

def draw_info_block(x, y, title, lines, line_gap=36, value_col_offset=180, bar_width=100):
    font_id = 0

    # Title
    blf.size(font_id, 16)
    draw_colored_text(f"» {title}", (x, y), color=(1, 1, 1, 1), size=16)

    start_y = y - 30
    blf.size(font_id, 13)

    for i, (label, value, key) in enumerate(lines):
        line_y = start_y - i * line_gap

        # Label
        draw_text(label, (x, line_y))

        # Key under label
        if key:
            draw_text(key, (x, line_y - 12), size=11)

        # Check if value is tuple (i.e., draw a progress bar)
        if isinstance(value, (tuple, list)) and len(value) == 3:
            val, min_val, max_val = value
            bar_x = x + value_col_offset
            bar_y = line_y - 6  # vertically center between label/key
            draw_progress_bar(bar_x, bar_y, width=bar_width, height=16,
                              value=val, min_value=min_val, max_value=max_val, label="")
        else:
            val_y = line_y - 6
            color = color_from_value(value)
            draw_colored_text(value, (x + value_col_offset, val_y), color=color)



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


def draw_filled_rect(verts, color=(1, 1, 1, 1)):
    """Helper to draw filled quad with given 4 verts (clockwise or CCW)."""
    batch = batch_for_shader(_shader, 'TRI_FAN', {"pos": verts})
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
