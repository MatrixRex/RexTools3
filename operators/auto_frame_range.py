import bpy
from bpy.app.handlers import persistent

def update_frame_range(scene):
    if not scene.rex_auto_frame_range:
        return

    obj = bpy.context.active_object
    if not (obj and obj.animation_data and obj.animation_data.action):
        return

    action = obj.animation_data.action
    frame_range = action.frame_range
    
    # Calculate start and end frames from action frame range
    start = int(frame_range[0])
    end = int(frame_range[1])
    
    # Only update if values have changed to avoid unnecessary updates
    if scene.frame_start != start:
        scene.frame_start = start
    if scene.frame_end != end:
        scene.frame_end = end

@persistent
def auto_frame_range_handler(scene, depsgraph=None):
    # This handler can be called with different arguments depending on the event
    # We use scene directly if available, otherwise get from context
    if not scene:
        scene = bpy.context.scene
    update_frame_range(scene)

def draw_timeline_header(self, context):
    layout = self.layout
    scene = context.scene
    
    layout.separator()
    layout.prop(scene, "rex_auto_frame_range", 
                text="Auto Range", 
                toggle=True, 
                icon='TIME')

def register():
    # Append handler to depsgraph_update_post to catch keyframe changes and object switching
    if auto_frame_range_handler not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(auto_frame_range_handler)
    
    # Append the UI to the timeline header
    # Try multiple possible header names for compatibility
    header_classes = ["TIME_HT_header", "DOPESHEET_HT_header"]
    for header_name in header_classes:
        header = getattr(bpy.types, header_name, None)
        if header:
            header.append(draw_timeline_header)

def unregister():
    # Remove handler
    if auto_frame_range_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(auto_frame_range_handler)
    
    # Remove the UI from the timeline header
    header_classes = ["TIME_HT_header", "DOPESHEET_HT_header"]
    for header_name in header_classes:
        header = getattr(bpy.types, header_name, None)
        if header:
            try:
                header.remove(draw_timeline_header)
            except Exception:
                pass
