import bpy
import re
from bpy.types import Operator

def smart_rename(name):
    """
    Rename animation smartly by swapping left/right indicators.
    e.g., walk_L -> walk_R, run_left -> run_right
    """
    # Define pairs for swapping. Full words first to prevent substring matching issues (e.g. Turn_Right matching _R).
    pairs = [
        ("Left", "Right"), ("Right", "Left"),
        ("left", "right"), ("right", "left"),
        ("LEFT", "RIGHT"), ("RIGHT", "LEFT"),
        (".L", ".R"), (".R", ".L"),
        (".l", ".r"), (".r", ".l"),
        ("_L", "_R"), ("_R", "_L"),
        ("_l", "_r"), ("_r", "_l"),
        ("-L", "-R"), ("-R", "-L"),
        ("-l", "-r"), ("-r", "-l"),
        ("L_", "R_"), ("R_", "L_"),
        ("l_", "r_"), ("r_", "l_"),
    ]
    
    # Try to find a match and swap it
    for old, new in pairs:
        if old in name:
            return name.replace(old, new)
            
    # Fallback if no side indicators found
    if "_Flipped" in name:
        return name.replace("_Flipped", "")
    return name + "_Flipped"

def get_bone_keyframes(action):
    """
    Extract a map of bone names and their keyframed frames and attributes.
    Returns: { bone_name: { frame: {attr1, attr2, ...} } }
    """
    data = {}
    # Regex to match pose.bones["Name"].attr or pose.bones["Name"]["prop"]
    pattern = r'^pose\.bones\["([^"]+)"\](\..+|\[".+"\])$'
    
    for fcurve in action.fcurves:
        match = re.match(pattern, fcurve.data_path)
        if not match:
            continue
            
        bone_name = match.group(1)
        attr_raw = match.group(2)
        
        # Clean up attr for keyframe_insert (strip leading dot if present)
        attr = attr_raw[1:] if attr_raw.startswith('.') else attr_raw
            
        if bone_name not in data:
            data[bone_name] = {}
            
        for kp in fcurve.keyframe_points:
            # Use rounding to avoid floating point issues with frame numbers
            frame = round(kp.co.x, 3)
            if frame not in data[bone_name]:
                data[bone_name][frame] = set()
            data[bone_name][frame].add(attr)
    return data

def flip_data_path(path):
    """
    Flip names inside a data path, e.g., for constraints.
    constraints["IK.L"].enabled -> constraints["IK.R"].enabled
    """
    match = re.search(r'constraints\["([^"]+)"\]', path)
    if match:
        con_name = match.group(1)
        flipped_con_name = bpy.utils.flip_name(con_name)
        return path.replace(f'constraints["{con_name}"]', f'constraints["{flipped_con_name}"]')
    return path

class REXTOOLS3_OT_FlippedAnim(Operator):
    """Flip the active action using frame-by-frame pose mirroring"""
    bl_idname = "rextools3.flipped_anim"
    bl_label = "Flipped Anim"
    bl_description = "Creates a new action with flipped keyframes by processing the pose frame-by-frame (L <-> R)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if not obj or obj.type != 'ARMATURE':
            return False
            
        # Check for active action or active NLA strip
        if obj.animation_data:
            if obj.animation_data.action:
                return True
            # Also check for active NLA strip
            for track in obj.animation_data.nla_tracks:
                if track.active:
                    for strip in track.strips:
                        if strip.active:
                            return True
        return False

    def execute(self, context):
        obj = context.active_object
        anim_data = obj.animation_data
        scene = context.scene
        
        # 1. Identify the source action
        original_action = anim_data.action
        if not original_action:
            for track in anim_data.nla_tracks:
                if track.active:
                    for strip in track.strips:
                        if strip.active:
                            original_action = strip.action
                            break
                if original_action:
                    break
        
        if not original_action:
            self.report({'ERROR'}, "No active action found to flip")
            return {'CANCELLED'}
            
        # 2. Extract keyframe map from original action
        keyframes_map = get_bone_keyframes(original_action)
        if not keyframes_map:
            self.report({'ERROR'}, "No bone keyframes found in action")
            return {'CANCELLED'}
            
        # Get all unique frames that need processing
        all_frames = sorted(list(set(f for bone_frames in keyframes_map.values() for f in bone_frames.keys())))
        
        # 3. Create new action
        # We copy the original to preserve non-bone F-curves (e.g. object properties, markers)
        new_name = smart_rename(original_action.name)
        new_action = original_action.copy()
        new_action.name = new_name
        
        # Delete all bone-related F-curves in the new action so we can write fresh flipped ones
        for fcurve in list(new_action.fcurves):
            if fcurve.data_path.startswith("pose.bones"):
                new_action.fcurves.remove(fcurve)
        
        # 4. Prepare for frame-by-frame mirroring
        original_frame = scene.frame_current
        original_mode = obj.mode
        auto_key = scene.tool_settings.use_keyframe_insert_auto
        
        # Disable auto-keying to prevent artifacts during loop
        scene.tool_settings.use_keyframe_insert_auto = False
        
        if obj.mode != 'POSE':
            bpy.ops.object.mode_set(mode='POSE')
            
        # Select all bones to ensure pose copy/paste works for the entire rig
        bpy.ops.pose.select_all(action='SELECT')
        
        try:
            # Iterate through each frame that had keyframes
            for f in all_frames:
                # Set the frame
                scene.frame_set(int(f) if f == round(f) else f)
                
                # Switch to original action and update pose
                anim_data.action = original_action
                context.view_layer.update()
                
                # Copy current pose from 3D View
                bpy.ops.pose.copy()
                
                # Switch to new action
                anim_data.action = new_action
                context.view_layer.update()
                
                # Paste flipped in 3D View (this handles L/R mapping and center bone flipping)
                bpy.ops.pose.paste(flipped=True)
                
                # Insert keyframes on the MIRRORED bones
                for bone_name, frames in keyframes_map.items():
                    if f in frames:
                        # Find mirrored partner name
                        mirrored_name = bpy.utils.flip_name(bone_name)
                        
                        # Use mirrored bone if it exists, otherwise it's a center bone (mirrors to self)
                        if mirrored_name not in obj.pose.bones:
                            mirrored_name = bone_name
                            
                        pbone = obj.pose.bones.get(mirrored_name)
                        if pbone:
                            # Keyframe exactly the same channels as the original
                            for data_type in frames[f]:
                                # 1. Try flipped data path (for constraints like IK.L -> IK.R)
                                target_path = flip_data_path(data_type)
                                try:
                                    pbone.path_resolve(target_path)
                                    pbone.keyframe_insert(data_path=target_path)
                                except:
                                    # 2. Fallback to original path if flipped didn't exist
                                    try:
                                        pbone.path_resolve(data_type)
                                        pbone.keyframe_insert(data_path=data_type)
                                    except:
                                        # 3. Last resort: log but don't crash
                                        pass
                                
            self.report({'INFO'}, f"Created flipped action: {new_action.name}")
            
        except Exception as e:
            self.report({'ERROR'}, f"Flipping failed: {str(e)}")
            # Restore original action on failure
            anim_data.action = original_action
            return {'CANCELLED'}
        finally:
            # Restore original state
            scene.frame_set(original_frame)
            scene.tool_settings.use_keyframe_insert_auto = auto_key
            if obj.mode != original_mode:
                bpy.ops.object.mode_set(mode=original_mode)

        return {'FINISHED'}

def draw_action_button(self, context):
    if context.space_data.type == 'DOPESHEET_EDITOR' and context.space_data.mode == 'ACTION':
        layout = self.layout
        layout.separator()
        layout.operator("rextools3.flipped_anim", text="Flip Action", icon='DUPLICATE')

def draw_nla_button(self, context):
    if context.space_data.type == 'NLA_EDITOR':
        layout = self.layout
        layout.separator()
        layout.operator("rextools3.flipped_anim", text="Flip Strip", icon='DUPLICATE')

def register():
    bpy.types.DOPESHEET_HT_header.append(draw_action_button)
    bpy.types.NLA_HT_header.append(draw_nla_button)

def unregister():
    bpy.types.DOPESHEET_HT_header.remove(draw_action_button)
    bpy.types.NLA_HT_header.remove(draw_nla_button)
