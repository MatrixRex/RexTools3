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

def draw_info_block(x, y, lines, line_height=18, value_col_offset=150, key_col_offset=300):
    """
    Draws a list of (label, value, key) tuples as a HUD block.
    Example: [("Width", "0.25", "toggle W"), ...]
    """
    font_id = 0
    blf.size(font_id, 14)

    for i, (label, value, key) in enumerate(lines):
        offset_y = y - i * line_height

        # Draw label
        blf.position(font_id, x, offset_y, 0)
        blf.draw(font_id, label)

        # Draw value with color
        value_col = color_from_value(value)
        draw_colored_text(value, (x + value_col_offset, offset_y), value_col)

        # Draw key hint
        if key:
            draw_text(key, (x + key_col_offset, offset_y))

def draw_colored_text(text, position, color=(1, 1, 1, 1), size=14):
    font_id = 0
    blf.color(font_id, *color)
    blf.position(font_id, position[0], position[1], 0)
    blf.size(font_id, size)
    blf.draw(font_id, text)

def color_from_value(value):
    if isinstance(value, str):
        v = value.lower()
        if v == "true":
            return (0.3, 1.0, 0.3, 1)
        if v == "false":
            return (1.0, 0.3, 0.3, 1)
    return (1, 1, 1, 1)
