import bpy
from bpy.app.handlers import persistent

def set_scene_frame_range(scene, start, end):
    if scene.frame_start == start and scene.frame_end == end:
        return
    # Prevent frame_start from being clamped by current frame_end when expanding or shifting
    if start > scene.frame_end:
        scene.frame_end = end
        scene.frame_start = start
    else:
        scene.frame_start = start
        scene.frame_end = end

def update_frame_range(scene):
    if not getattr(scene, "rex_auto_frame_range", False):
        return

    # In handlers, context can be fragile. We gather target objects.
    target_objs = set()
    try:
        active = bpy.context.view_layer.objects.active
        if active:
            target_objs.add(active)
        for obj in bpy.context.selected_objects:
            target_objs.add(obj)
    except Exception:
        pass

    # 1. Search for selected NLA strips
    selected_strips = []
    
    # Check target_objs first
    for obj in target_objs:
        if obj.animation_data and obj.animation_data.nla_tracks:
            for track in obj.animation_data.nla_tracks:
                if track.mute:
                    continue
                for strip in track.strips:
                    if strip.select:
                        selected_strips.append(strip)

    # If no selected strips in target_objs, search across all scene objects
    if not selected_strips and hasattr(scene, "objects"):
        for obj in scene.objects:
            if obj.animation_data and obj.animation_data.nla_tracks:
                for track in obj.animation_data.nla_tracks:
                    if track.mute:
                        continue
                    for strip in track.strips:
                        if strip.select:
                            selected_strips.append(strip)

    # If any NLA strip is selected, set auto range to start/end on the selected strip(s)
    if selected_strips:
        start = int(round(min(strip.frame_start for strip in selected_strips)))
        end = int(round(max(strip.frame_end for strip in selected_strips)))
        set_scene_frame_range(scene, start, end)
        return

    # 2. Fallback: calculate frame range from active action keyframes or unselected NLA strips
    all_min = []
    all_max = []
    
    for obj in target_objs:
        anim_data = getattr(obj, "animation_data", None)
        if not anim_data:
            continue
            
        action = anim_data.action
        
        if action:
            # Determine NLA offset and scale if in tweak mode
            offset = 0.0
            scale = 1.0
            if anim_data.use_tweak_mode:
                for track in anim_data.nla_tracks:
                    for strip in track.strips:
                        if strip.active and strip.action == action:
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
        else:
            # If no active action, check unselected NLA strips on the object
            if anim_data.nla_tracks:
                for track in anim_data.nla_tracks:
                    if track.mute:
                        continue
                    for strip in track.strips:
                        if not strip.mute:
                            all_min.append(strip.frame_start)
                            all_max.append(strip.frame_end)

    if not all_min:
        return
        
    start = int(round(min(all_min)))
    end = int(round(max(all_max)))
    
    set_scene_frame_range(scene, start, end)

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
    
    # Append the UI to animation timeline headers
    header_classes = ["TIME_HT_header", "DOPESHEET_HT_header", "NLA_HT_header", "GRAPH_HT_header"]
    for header_name in header_classes:
        header = getattr(bpy.types, header_name, None)
        if header:
            header.append(draw_timeline_header)

def unregister():
    # Remove handler
    if auto_frame_range_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(auto_frame_range_handler)
    
    # Remove the UI from headers
    header_classes = ["TIME_HT_header", "DOPESHEET_HT_header", "NLA_HT_header", "GRAPH_HT_header"]
    for header_name in header_classes:
        header = getattr(bpy.types, header_name, None)
        if header:
            try:
                header.remove(draw_timeline_header)
            except Exception:
                pass

