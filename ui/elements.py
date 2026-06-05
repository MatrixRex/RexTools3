import blf
import math
from .drawing import draw_text, draw_rounded_rect, draw_icon_hud
from ..core.theme import Theme

class UIElement:
    def __init__(self):
        self.x = 0; self.y = 0; self.width = 0; self.height = 0
        self.visible = True
        self.padding = Theme.PADDING
        self.spacing = Theme.SPACING
    def update_layout(self, x, y): self.x = x; self.y = y
    def get_dimensions(self): return self.width, self.height
    def draw(self): pass

class Container(UIElement):
    def __init__(self):
        super().__init__()
        self.children = []
    def add(self, child):
        self.children.append(child)
        return child
    def clear(self): self.children.clear()

class Column(Container):
    def update_layout(self, x, y):
        self.x = x; self.y = y; curr_y = y; max_w = 0; total_h = 0
        for child in self.children:
            if hasattr(child, 'update_dimensions'): child.update_dimensions()
            child.update_layout(x, curr_y)
            w, h = child.get_dimensions()
            curr_y -= (h + self.spacing)
            max_w = max(max_w, w)
            total_h += h + self.spacing
        self.width = max_w
        self.height = total_h - self.spacing if self.children else 0
    def draw(self):
        if self.visible:
            for child in self.children: child.draw()

class Row(Container):
    def update_layout(self, x, y):
        self.x = x; self.y = y; curr_x = x; total_w = 0; max_h = 0
        for child in self.children:
            if hasattr(child, 'update_dimensions'): child.update_dimensions()
            child.update_layout(curr_x, y)
            w, h = child.get_dimensions()
            curr_x += (w + self.spacing)
            total_w += w + self.spacing
            max_h = max(max_h, h)
        self.width = total_w - self.spacing if self.children else 0
        self.height = max_h
    def draw(self):
        if self.visible:
            for child in self.children: child.draw()

class Group(Container):
    def __init__(self, title="", icon=None):
        super().__init__()
        self.title = title
        self.icon = icon
        self.show_bg = True
        self.layout = Column()
    def add(self, child): return self.layout.add(child)
    def update_layout(self, x, y):
        self.x = x; self.y = y
        header_h = Theme.FONT_SIZE_HEADER + Theme.SPACING if self.title else 0
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
            draw_rounded_rect(self.x, self.y, self.width, self.height, Theme.COLOR_BG, Theme.COLOR_BORDER, Theme.CORNER_RADIUS)
        if self.title:
            draw_text(self.title, self.x + self.padding, self.y - self.padding - Theme.FONT_SIZE_HEADER, size=Theme.FONT_SIZE_HEADER, color=Theme.COLOR_INFO)
        self.layout.draw()

class Label(UIElement):
    def __init__(self, text="", size=Theme.FONT_SIZE_NORMAL, color=Theme.COLOR_TEXT):
        super().__init__()
        self.text = text; self.size = size; self.color = color
        self.update_dimensions()
    def update_dimensions(self):
        blf.size(0, self.size)
        w, h = blf.dimensions(0, self.text)
        self.width = int(w); self.height = int(h)
    def set_text(self, text): self.text = text; self.update_dimensions()
    def draw(self):
        if self.visible: draw_text(self.text, self.x, self.y - self.height, size=self.size, color=self.color)

class ProgressBar(UIElement):
    def __init__(self, label="", width=204, height=22):
        super().__init__()
        self.label = label; self.width = width; self.height = height; self.value = 0.5
        self.color_fill = Theme.COLOR_SUCCESS
        self.color_bg = (0.2, 0.2, 0.2, 0.95)
    def draw(self):
        if not self.visible: return
        radius = self.height / 2
        draw_rounded_rect(self.x, self.y, self.width, self.height, self.color_bg, Theme.COLOR_BORDER, radius)
        fill_w = self.width * max(0, min(1, self.value))
        if fill_w > 2:
            draw_rounded_rect(self.x, self.y, fill_w, self.height, self.color_fill, (0,0,0,0), min(radius, fill_w/2))
        val_text = f"{self.label}: {int(self.value * 100)}%" if self.label else f"{int(self.value * 100)}%"
        size = Theme.FONT_SIZE_NORMAL - 1
        blf.size(0, size); tw, th = blf.dimensions(0, val_text)
        draw_text(val_text, self.x + (self.width - tw)/2, self.y - self.height/2 - th/2 + 2, size=size)

class MessageBox(UIElement):
    def __init__(self, text="", type='INFO', width=300, show_icon=True):
        super().__init__()
        self.text = text; self.type = type; self.width = width; self.show_icon = show_icon
        self.padding = Theme.PADDING; self.lines = []
        self._wrap_text()
    def update_dimensions(self): self._wrap_text()
    def _wrap_text(self):
        blf.size(0, Theme.FONT_SIZE_NORMAL)
        
        # Calculate the actual offset from the left edge of the messagebox
        text_x_offset = self.padding + 5
        if self.show_icon:
            text_x_offset += 18 + 15  # 18 is icon_size, 15 is spacing after icon
            
        # The remaining width for text is: total width - left offset - right padding
        max_w = max(20, self.width - text_x_offset - self.padding)
        
        def wrap_word(word, max_w):
            tw, _ = blf.dimensions(0, word)
            if tw < max_w:
                return [word]
            
            chunks = []
            curr_chunk = ""
            delimiters = {'\\', '/', '_', '-', '.'}
            for char in word:
                test_chunk = curr_chunk + char
                cw, _ = blf.dimensions(0, test_chunk)
                if cw < max_w:
                    curr_chunk = test_chunk
                else:
                    # Try to find the last delimiter to split cleanly
                    break_idx = -1
                    for d in delimiters:
                        idx = curr_chunk.rfind(d)
                        if idx > break_idx:
                            break_idx = idx
                    
                    if break_idx > 0:
                        chunks.append(curr_chunk[:break_idx + 1])
                        curr_chunk = curr_chunk[break_idx + 1:] + char
                    else:
                        if curr_chunk:
                            chunks.append(curr_chunk)
                        curr_chunk = char
            if curr_chunk:
                chunks.append(curr_chunk)
            return chunks

        lines = []
        # Split by explicit newline first
        paragraphs = self.text.split('\n')
        for paragraph in paragraphs:
            if not paragraph:
                lines.append("")
                continue
                
            words = paragraph.split(' ')
            curr_line = ""
            for w in words:
                if not w:
                    continue
                w_chunks = wrap_word(w, max_w)
                for chunk in w_chunks:
                    test_line = curr_line + (" " if curr_line else "") + chunk
                    tw, _ = blf.dimensions(0, test_line)
                    if tw < max_w:
                        curr_line = test_line
                    else:
                        if curr_line:
                            lines.append(curr_line)
                        curr_line = chunk
            if curr_line:
                lines.append(curr_line)
                
        self.lines = lines
        self.height = len(lines) * Theme.FONT_SIZE_NORMAL + (len(lines)-1)*Theme.SPACING + 2*self.padding
    def draw(self):
        if not self.visible: return
        col = getattr(Theme, f"COLOR_{self.type}", Theme.COLOR_INFO)
        draw_rounded_rect(self.x, self.y, self.width, self.height, Theme.COLOR_BG, Theme.COLOR_BORDER, Theme.CORNER_RADIUS)
        draw_rounded_rect(self.x, self.y, 3, self.height, col, (0,0,0,0), 0)
        text_x_offset = self.padding + 5
        if self.show_icon:
            icon_size = 18; iy = self.y - (self.height / 2) + 1
            draw_icon_hud(self.x + self.padding + 8, iy, icon_size, col, self.type)
            text_x_offset += icon_size + 15
        for i, line in enumerate(self.lines):
            ly = self.y - self.padding - (i+1) * Theme.FONT_SIZE_NORMAL - i * Theme.SPACING
            draw_text(line, self.x + text_x_offset, ly + 4, size=Theme.FONT_SIZE_NORMAL, color=Theme.COLOR_TEXT)
