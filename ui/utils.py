import bpy
from ..core.theme import Theme

def draw_section(layout, title, icon='NONE'):
    """
    Draws a visual grouping box with a header.
    Returns the column to add items to.
    """
    box = layout.box()
    
    # Header
    row = box.row(align=True)
    row.alignment = 'LEFT'
    if icon != 'NONE':
        row.label(text=title, icon=icon)
    else:
        row.label(text=title)
        
    return box.column(align=True)

def draw_input_group(layout, label, prop_ptr, prop_name, active=True):
    """
    Draws a label and input property aligned consistently.
    """
    row = layout.row(align=True)
    row.active = active
    row.label(text=label + ":")
    row.prop(prop_ptr, prop_name, text="")
    
def draw_call_to_action(layout, operator_id, text, icon='NONE', type='PRIMARY'):
    """
    Draws a prominent button.
    """
    scale = 1.2 if type == 'PRIMARY' else 1.0
    col = layout.column()
    col.scale_y = scale
    col.operator(operator_id, text=text, icon=icon)
