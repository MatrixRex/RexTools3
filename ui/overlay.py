# RexTools3 UI Overlay System (Facade)
# This file re-exports components from modular sub-scripts for backward compatibility.

from .drawing import (
    IconManager, 
    draw_texture, 
    draw_line, 
    draw_point, 
    draw_crosshair, 
    draw_text, 
    draw_icon_hud, 
    draw_icon_warning, 
    draw_rounded_rect, 
    get_rounded_rect_verts
)

from .elements import (
    UIElement, 
    Container, 
    Column, 
    Row, 
    Group, 
    Label, 
    ProgressBar, 
    MessageBox
)

from .manager import (
    OverlayManager, 
    REXTOOLS3_OT_OverlayEventWatcher
)

from .templates import (
    ViewportOverlay, 
    ModalOverlay
)

from .legacy import (
    draw_info_block, 
    draw_option_set
)

from ..core.theme import Theme