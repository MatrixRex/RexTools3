import gpu
import bpy
import blf
import os
import math
from gpu_extras.batch import batch_for_shader
from ..core.theme import Theme

# ---------- Shaders & Constants ----------
try:
    _shader_sdf = gpu.shader.from_builtin('2D_POLY_SDF')
except:
    _shader_sdf = None

_shader_2d = gpu.shader.from_builtin('UNIFORM_COLOR')
try:
    _shader_img_color = gpu.shader.from_builtin('IMAGE_COLOR')
except:
    _shader_img_color = gpu.shader.from_builtin('2D_IMAGE_COLOR')

# ---------- Asset Management ----------

class IconManager:
    _icons = {}
    
    @classmethod
    def get_icon(cls, icon_name):
        icon_key = icon_name.lower()
        if icon_key in cls._icons:
            return cls._icons[icon_key]
        
        base_dir = os.path.dirname(os.path.dirname(__file__))
        path = os.path.join(base_dir, "assets", f"{icon_key}.png")
        
        if not os.path.exists(path):
            return None
            
        try:
            img_name = f"rextools3_icon_{icon_key}"
            img = bpy.data.images.get(img_name)
            if not img:
                img = bpy.data.images.load(path, check_existing=True)
                img.name = img_name
                img.alpha_mode = 'STRAIGHT'
                img.pack()
            
            tex = gpu.texture.from_image(img)
            cls._icons[icon_key] = tex
            return tex
        except Exception as e:
            print(f"RexTools3: Error loading icon {icon_key}: {e}")
            return None

def draw_texture(texture, x, y, w, h, color=(1,1,1,1)):
    """Draw a texture quad at x, y."""
    gpu.state.blend_set('ALPHA')
    verts = [(x, y), (x + w, y), (x + w, y - h), (x, y - h)]
    uvs = [(0, 1), (1, 1), (1, 0), (0, 0)]
    
    batch = batch_for_shader(_shader_img_color, 'TRI_FAN', {
        "pos": verts,
        "texCoord": uvs,
    })
    
    _shader_img_color.bind()
    _shader_img_color.uniform_sampler("image", texture)
    _shader_img_color.uniform_float("color", color)
    batch.draw(_shader_img_color)

def draw_line(p1, p2, width=1, color=(1,1,1,1)):
    gpu.state.blend_set('ALPHA')
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'LINES', {"pos": [p1, p2]})
    shader.bind()
    shader.uniform_float("color", color)
    gpu.state.line_width_set(width)
    batch.draw(shader)
    gpu.state.line_width_set(1.0)

def draw_point(p, radius=5, color=(1,1,1,1)):
    # Draw as a small circle
    draw_rounded_rect(p[0]-radius, p[1]+radius, radius*2, radius*2, color, (0,0,0,0), radius)

def draw_crosshair(p, size=5, gap=3, width=1, color=(1,1,1,1)):
    """ Draws a tactical HUD crosshair with a central gap. """
    draw_line((p[0], p[1] + gap), (p[0], p[1] + gap + size), width, color)
    draw_line((p[0], p[1] - gap), (p[0], p[1] - gap - size), width, color)
    draw_line((p[0] - gap, p[1]), (p[0] - gap - size, p[1]), width, color)
    draw_line((p[0] + gap, p[1]), (p[0] + gap + size, p[1]), width, color)

def draw_text(text, x, y, size=14, color=(1, 1, 1, 1)):
    gpu.state.blend_set('ALPHA')
    blf.size(0, size)
    blf.color(0, *color)
    blf.position(0, x, y, 0)
    blf.draw(0, text)

def draw_icon_hud(x, y, size, color, type='INFO'):
    """Draw a stylized HUD icon based on type."""
    hh = size / 2
    tex = IconManager.get_icon(type)
    if tex:
        draw_texture(tex, x, y + hh, size, size, color)
        return

    if type == 'ERROR' or type == 'WARNING':
        pts = [(x + hh, y + hh), (x, y - hh), (x + size, y - hh)]
        draw_line(pts[0], pts[1], 1.5, color)
        draw_line(pts[1], pts[2], 1.5, color)
        draw_line(pts[2], pts[0], 1.5, color)
        draw_text("!", x + hh - 3, y - 6, size=int(size*0.75), color=color)
    elif type == 'SUCCESS':
        p1 = (x + 2, y - 2)
        p2 = (x + hh, y - hh + 2)
        p3 = (x + size - 2, y + hh - 2)
        draw_line(p1, p2, 2.5, color)
        draw_line(p2, p3, 2.5, color)
    else:
        p1 = (x + hh, y + hh); p2 = (x + size, y); p3 = (x + hh, y - hh); p4 = (x, y)
        draw_line(p1, p2, 1.2, color); draw_line(p2, p3, 1.2, color)
        draw_line(p3, p4, 1.2, color); draw_line(p4, p1, 1.2, color)
        draw_text("i", x + hh - 2, y - 6, size=int(size*0.75), color=color)

def draw_rounded_rect(x, y, w, h, color_bg, color_border, radius):
    gpu.state.blend_set('ALPHA')
    if _shader_sdf:
        verts = [(x, y), (x+w, y), (x+w, y-h), (x, y-h)]
        batch = batch_for_shader(_shader_sdf, 'TRI_FAN', {"pos": verts})
        _shader_sdf.bind()
        _shader_sdf.uniform_float("color", color_bg)
        _shader_sdf.uniform_float("outline_color", color_border)
        _shader_sdf.uniform_float("outline_thickness", 1.2)
        _shader_sdf.uniform_float("radius", [radius] * 4)
        _shader_sdf.uniform_float("rect", (x, y-h, w, h))
        batch.draw(_shader_sdf)
    else:
        verts = get_rounded_rect_verts(x, y, w, h, radius)
        batch_bg = batch_for_shader(_shader_2d, 'TRI_FAN', {"pos": verts})
        _shader_2d.bind()
        _shader_2d.uniform_float("color", color_bg)
        batch_bg.draw(_shader_2d)
        if color_border[3] > 0:
            verts_border = verts + [verts[0]]
            batch_border = batch_for_shader(_shader_2d, 'LINE_STRIP', {"pos": verts_border})
            _shader_2d.bind()
            _shader_2d.uniform_float("color", color_border)
            batch_border.draw(_shader_2d)

def get_rounded_rect_verts(x, y, w, h, rounding):
    if rounding <= 0: return [(x, y), (x+w, y), (x+w, y-h), (x, y-h)]
    rounding = min(rounding, w/2, h/2)
    verts = []
    steps = 12
    for i in range(steps + 1):
        angle = math.radians(90 - (90 * i / steps))
        verts.append((x + w - rounding + math.cos(angle) * rounding, y - rounding + math.sin(angle) * rounding))
    for i in range(steps + 1):
        angle = math.radians(0 - (90 * i / steps))
        verts.append((x + w - rounding + math.cos(angle) * rounding, y - h + rounding + math.sin(angle) * rounding))
    for i in range(steps + 1):
        angle = math.radians(270 - (90 * i / steps))
        verts.append((x + rounding + math.cos(angle) * rounding, y - h + rounding + math.sin(angle) * rounding))
    for i in range(steps + 1):
        angle = math.radians(180 - (90 * i / steps))
        verts.append((x + rounding + math.cos(angle) * rounding, y - rounding + math.sin(angle) * rounding))
    return verts

def draw_icon_warning(x, y, size, color):
    # Standard warning, keep for legacy but map to hud if possible
    draw_icon_hud(x, y + size/2, size, color, 'WARNING')
