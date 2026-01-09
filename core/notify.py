import bpy
from ..ui.overlay import MessageBox, ViewportOverlay, OverlayManager

def _show_message(text, type='INFO', timeout=3.0):
    """
    Internal helper to show a quick floating message.
    """
    # Create ephemeral overlay
    ov = ViewportOverlay(title="", x='CENTER', y='BOTTOM')
    ov.show_bg = False # Just the message box has bg
    ov.timeout = timeout
    ov.close_on_click = True
    
    # Message Box
    msg = MessageBox(text=text, type=type, width=350)
    ov.add(msg)
    ov.show()
    return ov

def success(message, title="Success"):
    """Show a success message (Green)"""
    _show_message(message, type='SUCCESS', timeout=2.5)

def warning(message, title="Warning"):
    """Show a warning message (Orange)"""
    _show_message(message, type='WARNING', timeout=4.0)

def error(message, title="Error"):
    """Show an error message (Red)"""
    _show_message(message, type='ERROR', timeout=5.0)

def info(message, title="Info"):
    """Show an info message (Blue)"""
    _show_message(message, type='INFO', timeout=3.0)
