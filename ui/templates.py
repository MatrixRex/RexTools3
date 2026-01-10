import bpy
import time
import blf
from .drawing import draw_rounded_rect, draw_text, draw_texture, IconManager, draw_icon_hud
from .elements import Group, UIElement
from .manager import OverlayManager
from ..core.theme import Theme

class ViewportOverlay(Group):
    def __init__(self, title="RexTools Overlay", x=50, y=None):
        super().__init__(title=title)
        self.anchor_x = x; self.anchor_y = y; self.start_time = time.time(); self.timeout = None; self.close_on_click = False
    def show(self): self.start_time = time.time(); OverlayManager().add_overlay(self)
    def hide(self): OverlayManager().remove_overlay(self)
    def draw(self):
        region = bpy.context.region; manager = OverlayManager(); self.update_layout(0, 0); tx, ty = self.anchor_x, self.anchor_y; mx, my = manager.mouse_pos
        if tx == 'MOUSE': tx = mx + 15
        elif tx == 'CENTER': tx = (region.width - self.width) / 2
        if ty == 'MOUSE': ty = my - 15
        elif ty == 'CENTER': ty = (region.height + self.height) / 2
        elif ty == 'BOTTOM': ty = self.height + 50 + getattr(self, '_stack_offset_y', 0)
        elif ty is None: ty = region.height - 50
        self.update_layout(tx, ty); super().draw()

class ModalOverlay(UIElement):
    def __init__(self, title="Modal Action", x=100, y=100, width=420):
        super().__init__()
        self.title = title; self.x = x; self.y = y; self.width = width; self.items = []
        self.padding = Theme.PADDING; self.row_height = 30
    def add_mode_selector(self, label, shortcuts, options, current_index, interacting=False):
        self.items.append({'type': 'MODE', 'label': label, 'shortcuts': shortcuts, 'options': options, 'current_index': current_index, 'interacting': interacting})
    def add_progress(self, label, shortcuts, value, min_val, max_val):
        self.items.append({'type': 'PROGRESS', 'label': label, 'shortcuts': shortcuts, 'value': value, 'min': min_val, 'max': max_val})
    def add_bool(self, label, shortcuts, value):
        self.items.append({'type': 'BOOL', 'label': label, 'shortcuts': shortcuts, 'value': value})
    def add_value(self, label, shortcuts, value):
        self.items.append({'type': 'VALUE', 'label': label, 'shortcuts': shortcuts, 'value': value})
    def draw(self):
        if not self.visible: return
        # Calculate height with more breathing room for header and bottom padding
        h = len(self.items) * self.row_height + self.padding * 2 + 40
        draw_rounded_rect(self.x, self.y, self.width, h, Theme.COLOR_BG, Theme.COLOR_BORDER, Theme.CORNER_RADIUS)
        draw_rounded_rect(self.x, self.y, 3, h, Theme.COLOR_INFO, (0,0,0,0), 0)
        draw_text(f"# {self.title}", self.x + self.padding + 5, self.y - self.padding - 15, size=16, color=Theme.COLOR_INFO)
        curr_y = self.y - self.padding - 35
        for item in self.items:
            lx = self.x + self.padding + 5
            draw_text(item['label'], lx, curr_y - 14, size=13, color=Theme.COLOR_TEXT)
            draw_text(f"[{item['shortcuts']}]", lx, curr_y - 26, size=9, color=Theme.COLOR_SUBTEXT)
            
            # Reduced column spacing: pull right-side widgets closer to the center
            rx = self.x + self.width / 2 - 40; rw = self.width - (rx - self.x) - self.padding
            if item['type'] == 'MODE': self._draw_mode(rx, curr_y, rw, item)
            elif item['type'] == 'PROGRESS': self._draw_progress(rx, curr_y, rw, item)
            elif item['type'] == 'BOOL': self._draw_bool(rx, curr_y, rw, item)
            elif item['type'] == 'VALUE': self._draw_value(rx, curr_y, rw, item)
            curr_y -= self.row_height

    def _draw_mode(self, x, y, w, item):
        opts = item['options']; idx = item['current_index']; interacting = item.get('interacting', False)
        if not interacting:
            draw_text(opts[idx], x, y - 18, size=14, color=Theme.COLOR_SUCCESS)
        else:
            spacing = 15; curr_x = x
            for i, opt in enumerate(opts):
                col = Theme.COLOR_SUCCESS if i == idx else Theme.COLOR_SUBTEXT
                blf.size(0, 14); tw, _ = blf.dimensions(0, opt)
                draw_text(opt, curr_x, y - 18, size=14, color=col)
                curr_x += tw + spacing

    def _draw_progress(self, x, y, w, item):
        # Scale range
        val_range = item['max'] - item['min']
        val_pct = (item['value'] - item['min']) / val_range if val_range != 0 else 0
        
        # Sharp corners for a more tactical look
        bar_w = w - 50
        draw_rounded_rect(x, y - 14, bar_w, 6, (0.15, 0.15, 0.15, 1), (0.3, 0.3, 0.3, 1), 0)
        draw_rounded_rect(x, y - 14, bar_w * val_pct, 6, Theme.COLOR_SUCCESS, (0,0,0,0), 0)
        
        # Value string
        val_str = f"{item['value']:.2f}"
        draw_text(val_str, x + bar_w + 10, y - 18, size=13, color=Theme.COLOR_TEXT)

    def _draw_bool(self, x, y, w, item):
        col = Theme.COLOR_SUCCESS if item['value'] else Theme.COLOR_SUBTEXT
        txt = "ENABLED" if item['value'] else "DISABLED"
        draw_text(txt, x, y - 18, size=13, color=col)

    def _draw_value(self, x, y, w, item):
        val = item['value']
        txt = f"{val:.2f}" if isinstance(val, float) else str(val)
        draw_text(txt, x, y - 18, size=14, color=Theme.COLOR_SUCCESS)
