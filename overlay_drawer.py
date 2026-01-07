import gpu
from gpu_extras.batch import batch_for_shader
import blf
import time
import bpy
import math

# ---------- Shaders & Constants ----------
# We use UNIFORM_COLOR as the fallback, but for high-quality rounded shapes,
# we'll try to use the POLY_2D_SDF shader if available (Blender 4.0+).
try:
    _shader_sdf = gpu.shader.from_builtin('2D_POLY_SDF')
except:
    _shader_sdf = None

_shader_2d = gpu.shader.from_builtin('UNIFORM_COLOR')

class Theme:
    COLOR_TEXT = (1.0, 1.0, 1.0, 1.0)
    COLOR_SUBTEXT = (0.7, 0.7, 0.7, 1.0)
    COLOR_BG = (0.08, 0.08, 0.08, 0.9)
    COLOR_BORDER = (0.5, 0.5, 0.5, 0.8)
    COLOR_INFO = (0.35, 0.65, 1.0, 1.0)
    COLOR_WARNING = (1.0, 0.6, 0.2, 1.0)
    COLOR_SUCCESS = (0.4, 0.8, 0.4, 1.0)
    
    SPACING = 8
    PADDING = 15
    FONT_SIZE_NORMAL = 14
    FONT_SIZE_HEADER = 18
    CORNER_RADIUS = 10

# ---------- Base UI Classes ----------

class UIElement:
    def __init__(self):
        self.x = 0
        self.y = 0 
        self.width = 0
        self.height = 0
        self.visible = True
        self.padding = Theme.PADDING
        self.spacing = Theme.SPACING

    def update_layout(self, x, y):
        self.x = x
        self.y = y

    def get_dimensions(self):
        return self.width, self.height

    def draw(self):
        pass

class Container(UIElement):
    def __init__(self):
        super().__init__()
        self.children = []

    def add(self, child):
        self.children.append(child)
        return child

    def clear(self):
        self.children.clear()

class Column(Container):
    def update_layout(self, x, y):
        self.x = x
        self.y = y
        curr_y = y
        max_w = 0
        total_h = 0
        
        for child in self.children:
            if hasattr(child, 'update_dimensions'):
                child.update_dimensions()
                
            child.update_layout(x, curr_y)
            w, h = child.get_dimensions()
            curr_y -= (h + self.spacing)
            max_w = max(max_w, w)
            total_h += h + self.spacing
            
        self.width = max_w
        self.height = total_h - self.spacing if self.children else 0

    def draw(self):
        if not self.visible: return
        for child in self.children:
            child.draw()

class Row(Container):
    def update_layout(self, x, y):
        self.x = x
        self.y = y
        curr_x = x
        total_w = 0
        max_h = 0
        
        for child in self.children:
            if hasattr(child, 'update_dimensions'):
                child.update_dimensions()
                
            child.update_layout(curr_x, y)
            w, h = child.get_dimensions()
            curr_x += (w + self.spacing)
            total_w += w + self.spacing
            max_h = max(max_h, h)
            
        self.width = total_w - self.spacing if self.children else 0
        self.height = max_h

    def draw(self):
        if not self.visible: return
        for child in self.children:
            child.draw()

class Group(Container):
    def __init__(self, title="", icon=None):
        super().__init__()
        self.title = title
        self.icon = icon
        self.show_bg = True
        self.layout = Column()

    def add(self, child):
        return self.layout.add(child)

    def update_layout(self, x, y):
        self.x = x
        self.y = y
        
        header_h = 0
        if self.title:
            header_h = Theme.FONT_SIZE_HEADER + Theme.SPACING
            
        self.layout.update_layout(x + self.padding, y - self.padding - header_h)
        lw, lh = self.layout.get_dimensions()
        
        title_w = 0
        if self.title:
            blf.size(0, Theme.FONT_SIZE_HEADER)
            title_w, _ = blf.dimensions(0, self.title)
            
        self.width = max(lw, title_w) + 2 * self.padding
        self.height = lh + 2 * self.padding + header_h

    def draw(self):
        if not self.visible: return
        
        if self.show_bg:
            draw_rounded_rect(self.x, self.y, self.width, self.height, 
                              color_bg=Theme.COLOR_BG, 
                              color_border=Theme.COLOR_BORDER, 
                              radius=Theme.CORNER_RADIUS)
            
        if self.title:
            draw_text(self.title, self.x + self.padding, self.y - self.padding - Theme.FONT_SIZE_HEADER, size=Theme.FONT_SIZE_HEADER, color=Theme.COLOR_INFO)
            
        self.layout.draw()

# ---------- Leaf Components ----------

class Label(UIElement):
    def __init__(self, text="", size=Theme.FONT_SIZE_NORMAL, color=Theme.COLOR_TEXT):
        super().__init__()
        self.text = text
        self.size = size
        self.color = color
        self.update_dimensions()

    def update_dimensions(self):
        blf.size(0, self.size)
        w, h = blf.dimensions(0, self.text)
        self.width = int(w)
        self.height = int(h)

    def set_text(self, text):
        self.text = text
        self.update_dimensions()

    def draw(self):
        if not self.visible: return
        draw_text(self.text, self.x, self.y - self.height, size=self.size, color=self.color)

class ProgressBar(UIElement):
    def __init__(self, label="", width=204, height=22):
        super().__init__()
        self.label = label
        self.width = width
        self.height = height
        self.value = 0.5
        self.color_fill = Theme.COLOR_SUCCESS
        self.color_bg = (0.2, 0.2, 0.2, 0.95)

    def update_dimensions(self):
        pass

    def draw(self):
        if not self.visible: return
        radius = self.height / 2
        
        # Background
        draw_rounded_rect(self.x, self.y, self.width, self.height, 
                          color_bg=self.color_bg, 
                          color_border=Theme.COLOR_BORDER, 
                          radius=radius)
        
        # Fill
        fill_w = self.width * max(0, min(1, self.value))
        if fill_w > 2: # Don't draw tiny slivers
             # For the fill, we draw it without a border
             # We clip the radius to the fill width if needed
             f_radius = min(radius, fill_w / 2)
             draw_rounded_rect(self.x, self.y, fill_w, self.height, 
                               color_bg=self.color_fill, 
                               color_border=(0,0,0,0), 
                               radius=f_radius)
        
        val_text = f"{self.label}: {int(self.value * 100)}%" if self.label else f"{int(self.value * 100)}%"
        size = Theme.FONT_SIZE_NORMAL - 1
        blf.size(0, size)
        tw, th = blf.dimensions(0, val_text)
        draw_text(val_text, self.x + (self.width - tw)/2, self.y - self.height/2 - th/2 + 2, size=size)

class MessageBox(UIElement):
    def __init__(self, text="", type='INFO', width=300, show_icon=True):
        super().__init__()
        self.text = text
        self.type = type
        self.width = width
        self.show_icon = show_icon
        self.padding = Theme.PADDING
        self.lines = []
        self._wrap_text()

    def update_dimensions(self):
        self._wrap_text()

    def _wrap_text(self):
        blf.size(0, Theme.FONT_SIZE_NORMAL)
        words = self.text.split(' ')
        lines = []
        curr_line = ""
        max_w = self.width - 2 * self.padding
        
        for w in words:
            test_line = curr_line + (" " if curr_line else "") + w
            tw, _ = blf.dimensions(0, test_line)
            if tw < max_w:
                curr_line = test_line
            else:
                lines.append(curr_line)
                curr_line = w
        if curr_line: lines.append(curr_line)
            
        self.lines = lines
        th = Theme.FONT_SIZE_NORMAL
        self.height = len(lines) * th + (len(lines)-1) * Theme.SPACING + 2 * self.padding

    def draw(self):
        if not self.visible: return
        
        if self.type == 'ERROR':
            col = (1.0, 0.2, 0.2, 1.0)
        else:
            col = Theme.COLOR_INFO if self.type == 'INFO' else Theme.COLOR_WARNING
            
        bg_col = (col[0], col[1], col[2], 0.22)
        
        draw_rounded_rect(self.x, self.y, self.width, self.height, 
                          color_bg=bg_col, 
                          color_border=col, 
                          radius=Theme.CORNER_RADIUS)
        
        # Room for icon
        text_x_offset = self.padding
        if self.show_icon:
            icon_size = 20
            draw_icon_warning(self.x + self.padding, self.y - self.padding - icon_size/2 - 2, icon_size, col)
            text_x_offset += icon_size + 10

        for i, line in enumerate(self.lines):
            ly = self.y - self.padding - (i+1) * Theme.FONT_SIZE_NORMAL - i * Theme.SPACING
            draw_text(line, self.x + text_x_offset, ly, color=Theme.COLOR_TEXT)

# ---------- Drawing Primitives ----------

def draw_rounded_rect(x, y, w, h, color_bg, color_border, radius):
    """Draw an anti-aliased rounded rectangle with an optional border."""
    gpu.state.blend_set('ALPHA')
    
    # Try using the high-quality SDF shader if available
    if _shader_sdf:
        # SDF shader expects: x, y, width, height, radius (4 values for each corner), outline_thickness, outline_color
        # vertices for the quad
        verts = [(x, y), (x+w, y), (x+w, y-h), (x, y-h)]
        batch = batch_for_shader(_shader_sdf, 'TRI_FAN', {"pos": verts})
        _shader_sdf.bind()
        
        # Shader Uniforms (Blender 4.0+ style)
        _shader_sdf.uniform_float("color", color_bg)
        _shader_sdf.uniform_float("outline_color", color_border)
        _shader_sdf.uniform_float("outline_thickness", 1.2)
        _shader_sdf.uniform_float("radius", [radius] * 4)
        _shader_sdf.uniform_float("rect", (x, y-h, w, h)) # x, y, w, h
        
        batch.draw(_shader_sdf)
    else:
        # Fallback for older Blender versions using manual vertex arcs
        verts = get_rounded_rect_verts(x, y, w, h, radius)
        # Background
        batch_bg = batch_for_shader(_shader_2d, 'TRI_FAN', {"pos": verts})
        _shader_2d.bind()
        _shader_2d.uniform_float("color", color_bg)
        batch_bg.draw(_shader_2d)
        
        # Border (aliased fallback)
        if color_border[3] > 0:
            verts_border = verts + [verts[0]]
            batch_border = batch_for_shader(_shader_2d, 'LINE_STRIP', {"pos": verts_border})
            _shader_2d.bind()
            _shader_2d.uniform_float("color", color_border)
            batch_border.draw(_shader_2d)

def get_rounded_rect_verts(x, y, w, h, rounding):
    """Generate vertices for a rounded rectangle. y is top."""
    if rounding <= 0:
        return [(x, y), (x+w, y), (x+w, y-h), (x, y-h)]
    
    rounding = min(rounding, w/2, h/2)
    verts = []
    steps = 12 # Higher steps for smoother manual arcs
    
    # Corner Top-Right
    for i in range(steps + 1):
        angle = math.radians(90 - (90 * i / steps))
        verts.append((x + w - rounding + math.cos(angle) * rounding, 
                      y - rounding + math.sin(angle) * rounding))
    
    # Corner Bottom-Right
    for i in range(steps + 1):
        angle = math.radians(0 - (90 * i / steps))
        verts.append((x + w - rounding + math.cos(angle) * rounding, 
                      y - h + rounding + math.sin(angle) * rounding))

    # Corner Bottom-Left
    for i in range(steps + 1):
        angle = math.radians(270 - (90 * i / steps))
        verts.append((x + rounding + math.cos(angle) * rounding, 
                      y - h + rounding + math.sin(angle) * rounding))

    # Corner Top-Left
    for i in range(steps + 1):
        angle = math.radians(180 - (90 * i / steps))
        verts.append((x + rounding + math.cos(angle) * rounding, 
                      y - rounding + math.sin(angle) * rounding))
                      
    return verts

def draw_text(text, x, y, size=14, color=(1, 1, 1, 1)):
    gpu.state.blend_set('ALPHA')
    blf.size(0, size)
    blf.color(0, *color)
    blf.position(0, x, y, 0)
    blf.draw(0, text)

def draw_icon_warning(x, y, size, color):
    """Draw a stylized warning triangle."""
    padding = size * 0.1
    pts = [
        (x + size/2, y + size/2 - padding), # Top
        (x + padding, y - size/2 + padding), # Bottom Left
        (x + size - padding, y - size/2 + padding) # Bottom Right
    ]
    batch = batch_for_shader(_shader_2d, 'TRI_FAN', {"pos": pts})
    _shader_2d.bind()
    _shader_2d.uniform_float("color", color)
    batch.draw(_shader_2d)
    
    # Exclamation mark
    draw_text("!", x + size/2 - 3, y - size/2 + 5, size=int(size * 0.8), color=(0,0,0,1))

# ---------- Management ----------

class OverlayManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OverlayManager, cls).__new__(cls)
            cls._instance.overlays = []
            cls._instance.handle = None
            cls._instance.mouse_pos = (0, 0)
        return cls._instance

    def _force_redraw(self):
        if not bpy.context.screen: return
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

    def add_overlay(self, overlay):
        if overlay not in self.overlays:
            self.overlays.append(overlay)
        if not self.handle:
            self.handle = bpy.types.SpaceView3D.draw_handler_add(self.draw, (), 'WINDOW', 'POST_PIXEL')
        
        if not bpy.app.timers.is_registered(self._check_timeouts):
            bpy.app.timers.register(self._check_timeouts, first_interval=0.1)

        if any(ov.close_on_click or ov.anchor_x == 'MOUSE' or ov.anchor_y == 'MOUSE' for ov in self.overlays):
            bpy.ops.rextools3.overlay_event_watcher('INVOKE_DEFAULT')
            
        self._force_redraw()
        return overlay

    def _check_timeouts(self):
        if not self.overlays: return None
        now = time.time()
        to_remove = [ov for ov in self.overlays if ov.timeout and (now - ov.start_time) > ov.timeout]
        if to_remove:
            for ov in to_remove: self.remove_overlay(ov)
            self._force_redraw()
        return 0.1

    def remove_overlay(self, overlay):
        if overlay in self.overlays:
            self.overlays.remove(overlay)
        if not self.overlays and self.handle:
            bpy.types.SpaceView3D.draw_handler_remove(self.handle, 'WINDOW')
            self.handle = None
        self._force_redraw()

    def clear(self):
        self.overlays.clear()
        if self.handle:
            bpy.types.SpaceView3D.draw_handler_remove(self.handle, 'WINDOW')
            self.handle = None
        self._force_redraw()

    def draw(self):
        if not self.overlays: return
        gpu.state.blend_set('ALPHA')
        for overlay in self.overlays:
            overlay.draw()
        gpu.state.blend_set('NONE')

class REXTOOLS3_OT_OverlayEventWatcher(bpy.types.Operator):
    bl_idname = "rextools3.overlay_event_watcher"
    bl_label = "Overlay Event Watcher"
    
    def modal(self, context, event):
        manager = OverlayManager()
        if not manager.overlays: return {'FINISHED'}
        
        # Track mouse position
        manager.mouse_pos = (event.mouse_region_x, event.mouse_region_y)
        
        if any(ov.anchor_x == 'MOUSE' or ov.anchor_y == 'MOUSE' for ov in manager.overlays):
            self._force_redraw_areas(context)

        if event.type in {'LEFTMOUSE', 'RIGHTMOUSE', 'MIDDLEMOUSE'} and event.value == 'PRESS':
            to_remove = [ov for ov in manager.overlays if ov.close_on_click]
            for ov in to_remove: ov.hide()
            self._force_redraw_areas(context)
            if not any(ov.close_on_click or ov.anchor_x == 'MOUSE' or ov.anchor_y == 'MOUSE' for ov in manager.overlays): return {'FINISHED'}
        return {'PASS_THROUGH'}

    def _force_redraw_areas(self, context):
        for area in context.screen.areas:
            if area.type == 'VIEW_3D': area.tag_redraw()

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

class ViewportOverlay(Group):
    def __init__(self, title="RexTools Overlay", x=50, y=None):
        super().__init__(title=title)
        self.anchor_x = x
        self.anchor_y = y
        self.start_time = time.time()
        self.timeout = None
        self.close_on_click = False

    def show(self):
        self.start_time = time.time()
        OverlayManager().add_overlay(self)

    def hide(self):
        OverlayManager().remove_overlay(self)

    def draw(self):
        region = bpy.context.region
        manager = OverlayManager()
        
        self.update_layout(0, 0)
        tx, ty = self.anchor_x, self.anchor_y
        
        mx, my = manager.mouse_pos
        
        if tx == 'MOUSE': tx = mx + 15
        elif tx == 'CENTER': tx = (region.width - self.width) / 2
        
        if ty == 'MOUSE': ty = my - 15
        elif ty == 'CENTER': ty = (region.height + self.height) / 2
        elif ty == 'BOTTOM': ty = self.height + 50
        elif ty is None: ty = region.height - 50
        
        self.update_layout(tx, ty)
        super().draw()
