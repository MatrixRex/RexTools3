import bpy
from bpy.app.handlers import persistent

def update_frame_range(scene):
    if not getattr(scene, "rex_auto_frame_range", False):
        return

    # In handlers, context can be fragile. We gather actions from both 
    # the active object and all selected objects to match user expectations.
    target_objs = set()
    active = bpy.context.view_layer.objects.active
    if active:
        target_objs.add(active)
    
    for obj in bpy.context.selected_objects:
        target_objs.add(obj)
            
    all_min = []
    all_max = []
    
    for obj in target_objs:
        if not (obj.animation_data and obj.animation_data.action):
            continue
            
        action = obj.animation_data.action
        anim_data = obj.animation_data
        
        # Determine NLA offset and scale if in tweak mode
        offset = 0.0
        scale = 1.0
        if anim_data.use_tweak_mode:
            for track in anim_data.nla_tracks:
                for strip in track.strips:
                    if strip.active and strip.action == action:
                        # Calculation for scene time from action time:
                        # scene_time = (action_time - action_frame_start) * scale + frame_start
                        # Thus, the offset to add to action_time is:
                        # -action_frame_start * scale + frame_start
                        # And we must multiply the relative action time by scale.
                        offset = strip.frame_start - (strip.action_frame_start * strip.scale)
                        scale = strip.scale
                        break
                else: continue
                break

        # Gathering keyframes from all fcurves in the action
        found_in_action = False
        for fcurve in action.fcurves:
            if fcurve.keyframe_points:
                found_in_action = True
                # Keyframes are ordered by frame number
                kp_min = fcurve.keyframe_points[0].co[0]
                kp_max = fcurve.keyframe_points[-1].co[0]
                
                # Apply NLA transform
                all_min.append((kp_min * scale) + offset)
                all_max.append((kp_max * scale) + offset)
        
        # Fallback to action.frame_range if fcurves iteration didn't yield results
        if not found_in_action:
            all_min.append((action.frame_range[0] * scale) + offset)
            all_max.append((action.frame_range[1] * scale) + offset)

    if not all_min:
        return
        
    # Use round() to avoid truncation issues (e.g., 139.999 becoming 139)
    start = int(round(min(all_min)))
    end = int(round(max(all_max)))
    
    # Only update if values have changed to avoid unnecessary scene updates
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
