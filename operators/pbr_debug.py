import bpy
from bpy.types import Operator
from bpy.props import StringProperty, EnumProperty
from ..core import notify

class PBR_OT_DebugPreview(Operator):
    bl_idname = "pbr.debug_preview"
    bl_label = "Debug Preview"
    bl_description = "Preview texture outputs directly or mixed through an Emission shader"
    bl_options = {'REGISTER', 'UNDO'}

    _active_toast = None # Persistent toast reference

    slot: StringProperty()
    mode: EnumProperty(
        items=[
            ('DIRECT', "Direct", ""),
            ('MIXED', "Mixed", ""),
            ('OFF', "Off", ""),
        ],
        default='DIRECT'
    )

    def execute(self, context):
        mat = context.active_object.active_material
        if not mat or not mat.use_nodes:
            self.report({'ERROR'}, "No active material")
            return {'CANCELLED'}
        
        settings = mat.pbr_settings
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        
        # 1. Reset/Off
        if self.mode == 'OFF':
            settings.debug_preview_mode = 'OFF'
            settings.debug_preview_slot = ""
            _restore_original_material(mat)
            # notify.info("Debug Preview Disabled")
            return {'FINISHED'}
            
        settings.debug_preview_mode = self.mode
        settings.debug_preview_slot = self.slot
        
        # 2. Find target output socket
        out_sock = self.get_target_socket(mat, self.slot, self.mode)
        if not out_sock:
            # Try to restore if failed to find target
            _restore_original_material(mat)
            settings.debug_preview_mode = 'OFF'
            settings.debug_preview_slot = ""
            self.report({'WARNING'}, f"Could not find output for {self.slot} ({self.mode})")
            return {'CANCELLED'}
        
        # 3. Find Material Output
        mat_out = next((n for n in nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output), None)
        if not mat_out:
            mat_out = next((n for n in nodes if n.type == 'OUTPUT_MATERIAL'), None)
        if not mat_out:
            mat_out = nodes.new('ShaderNodeOutputMaterial')
            mat_out.is_active_output = True

        # 4. Create/Find Debug Emission Node
        emission = nodes.get("DebugEmissionPreview")
        if not emission:
            emission = nodes.new('ShaderNodeEmission')
            emission.name = "DebugEmissionPreview"
            emission.label = "DEBUG PREVIEW (UNLIT)"
            # Position it to the left of the material output
            if mat_out:
                emission.location = (mat_out.location.x - 300, mat_out.location.y)

        # 4. Connect to Material Output
        try:
            # 1. Connect target to Emission 'Color'
            links.new(out_sock, emission.inputs['Color'])
            # 2. Connect Emission to Material Output 'Surface'
            links.new(emission.outputs['Emission'], mat_out.inputs[0])
            
            print(f"DEBUG: Successfully routed '{out_sock.node.name}.{out_sock.name}' -> Emission -> '{mat_out.name}.Surface'")
        except Exception as e:
            print(f"DEBUG: FAILED to connect debug routing: {e}")
            self.report({'ERROR'}, f"Connection failed: {e}")
            return {'CANCELLED'}
        
        # Force a redraw so the user sees the output change immediately
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
        
        # 4. Notify (Persistent)
        if PBR_OT_DebugPreview._active_toast:
            PBR_OT_DebugPreview._active_toast.hide()
        
        PBR_OT_DebugPreview._active_toast = notify.sticky_warning(f"DEBUG: {self.slot} ({self.mode.title()}) - CLEAR to restore material")
        return {'FINISHED'}

    def get_target_socket(self, mat, slot, mode):
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        
        def find_node(name, label=None):
            n = nodes.get(name)
            if n:
                print(f"DEBUG: Found node by name '{name}'")
                return n
            if label:
                n = next((x for x in nodes if x.label == label), None)
                if n:
                    print(f"DEBUG: Found node by label '{label}' (internal name: {n.name})")
                    return n
            print(f"DEBUG: FAILED to find node: {name} / {label}")
            return None

        print(f"\n--- DEBUG PREVIEW START: {slot} [{mode}] ---")
        if slot == 'Base Color':
            if mode == 'DIRECT':
                # User wants: Base Color Tint (Mix Node)
                node = find_node("BaseTintMix", "Base Color Tint")
                if node: 
                    print(f"DEBUG: Success! Found '{slot}' -> '{node.name}'")
                    return node.outputs.get('Result', node.outputs[0])
            else: # MIXED
                # User wants: AO multiply (Mix Node)
                node = find_node("AOMix", "AO Multiply")
                if node: 
                    print(f"DEBUG: Success! Found '{slot}' -> '{node.name}'")
                    return node.outputs.get('Result', node.outputs[0])
                # Fallback if AO is not assigned
                node = find_node("BaseTintMix", "Base Color Tint")
                if node: 
                    print(f"DEBUG: Success! Found '{slot}' (Fallback) -> '{node.name}'")
                    return node.outputs.get('Result', node.outputs[0])
        
        elif slot == 'Normal':
            if mode == 'DIRECT':
                # Prefer the combined result if flipping G is active
                node = find_node("NormalCombine", "Normal Combine") or find_node("NormalTex", "Normal Texture")
                if node: 
                    print(f"DEBUG: Success! Found '{slot}' -> '{node.name}'")
                    # Combine node uses 'Image', Texture node uses 'Color'
                    return node.outputs.get('Image') or node.outputs.get('Color') or node.outputs[0]
            else: # MIXED
                node = find_node("NormalMap", "Normal Map Node")
                if node: 
                    print(f"DEBUG: Success! Found '{slot}' -> '{node.name}'")
                    return node.outputs.get('Normal', node.outputs[0])
                
        elif slot in ('Roughness', 'Metallic'):
            # These use Math nodes
            node = find_node(f"{slot}Math", f"{slot} Strength")
            if node: 
                print(f"DEBUG: Success! Found '{slot}' -> '{node.name}'")
                return node.outputs.get('Value', node.outputs[0])
            
        elif slot == 'Emission':
            if mode == 'DIRECT':
                # User wants: emission texture
                node = find_node("EmissionTex", "Emission Texture")
                if node: 
                    print(f"DEBUG: Success! Found '{slot}' -> '{node.name}'")
                    return node.outputs.get('Color', node.outputs[0])
            else: # MIXED (Tint - Mix Node)
                # User wants: emission tint
                node = find_node("EmissionTintMix", "Emission Tint")
                if node: 
                    print(f"DEBUG: Success! Found '{slot}' -> '{node.name}'")
                    return node.outputs.get('Result', node.outputs[0])
                
        elif slot == 'AO':
            # AO conversion/strength (Math or Mix)
            node = find_node("AOAdd", "AO Strength")
            if node: 
                print(f"DEBUG: Success! Found '{slot}' -> '{node.name}'")
                # Try Result (Mix) then Value (Math)
                return node.outputs.get('Result', node.outputs.get('Value', node.outputs[0]))
            
        elif slot == 'Alpha':
            if mode == 'DIRECT':
                # Texture node
                node = find_node("AlphaTex", "Alpha Texture") or find_node("BaseTex", "Base Color Texture")
                if node:
                    print(f"DEBUG: Success! Found '{slot}' (Texture) -> '{node.name}'")
                    # Use Alpha channel if it's the base texture, or Color if it's AlphaTex
                    return node.outputs.get('Alpha') if node.name == "BaseTex" else node.outputs.get('Color')
            else: # MIXED
                # Check for AlphaClip (most final) then AlphaMath (Strength)
                node = find_node("AlphaClip", "Alpha Clip") or find_node("AlphaMath", "Alpha Strength")
                if node:
                    print(f"DEBUG: Success! Found '{slot}' (Math/Clip) -> '{node.name}'")
                    return node.outputs.get('Value', node.outputs[0])
        print(f"DEBUG: FAILED to find target for slot '{slot}' in mode '{mode}'")
        return None




def _restore_original_material(mat):
    """Utility to reconnect Principled BSDF to Material Output."""
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    principled = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
    
    # Standard output nodes
    mat_out = next((n for n in nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output), None)
    if not mat_out:
        mat_out = next((n for n in nodes if n.type == 'OUTPUT_MATERIAL'), None)
        
    if principled and mat_out:
        # Connect BSDF to Surface
        links.new(principled.outputs[0], mat_out.inputs[0])
        
    # Cleanup temp nodes
    temp = nodes.get("DebugEmissionPreview")
    if temp: nodes.remove(temp)

class PBR_OT_ClearDebugPreview(Operator):
    bl_idname = "pbr.clear_debug_preview"
    bl_label = "Clear Debug Preview"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        mat = context.active_object.active_material
        if mat:
            mat.pbr_settings.debug_preview_mode = 'OFF'
            mat.pbr_settings.debug_preview_slot = ""
            
            # Hide toast
            if PBR_OT_DebugPreview._active_toast:
                PBR_OT_DebugPreview._active_toast.hide()
                PBR_OT_DebugPreview._active_toast = None

            # Use the restore logic
            _restore_original_material(mat)
            notify.info("Debug Preview Cleared")
            
        return {'FINISHED'}


def get_image_for_socket(material, socket_name):
    if not material or not material.use_nodes:
        return None
    nodes = material.node_tree.nodes
    principled = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if not principled:
        return None

    src_node = None
    
    if socket_name == "AO":
        ao_mix = nodes.get("AOMix")
        bc_inp = principled.inputs.get("Base Color")
        if ao_mix and bc_inp and bc_inp.is_linked:
            curr = bc_inp.links[0].from_node
            while curr:
                if curr == ao_mix:
                    b_sock = curr.inputs.get('B') or curr.inputs[2]
                    if b_sock and b_sock.is_linked:
                        src_node = b_sock.links[0].from_node
                    break
                a_sock = curr.inputs.get('A') or curr.inputs.get('Color1')
                curr = a_sock.links[0].from_node if a_sock and a_sock.is_linked else None
    elif socket_name == "Height":
        disp_node = nodes.get("HeightDisplace")
        if disp_node:
            h_sock = disp_node.inputs.get('Height')
            if h_sock and h_sock.is_linked:
                src_node = h_sock.links[0].from_node
    elif socket_name == "Emission":
        em_inp = principled.inputs.get("Emission Color")
        if em_inp and em_inp.is_linked:
            curr = em_inp.links[0].from_node
            if curr.name == "EmissionTintMix":
                a_sock = curr.inputs.get('A') or curr.inputs.get('Color1')
                if a_sock and a_sock.is_linked:
                    src_node = a_sock.links[0].from_node
            else:
                src_node = curr
    else:
        # Standard socket (Base Color, Roughness, Metallic, Normal, Alpha)
        inp = principled.inputs.get(socket_name)
        if inp and inp.is_linked:
            if socket_name == "Base Color":
                curr = inp.links[0].from_node
                while curr:
                    if curr.name == "BaseTex":
                        src_node = curr
                        break
                    if curr.name == "BaseTintMix":
                        a_sock = curr.inputs.get('A') or curr.inputs.get('Color1')
                        if a_sock and a_sock.is_linked:
                            curr = a_sock.links[0].from_node
                            continue
                    if curr.name == "AOMix":
                        a_sock = curr.inputs.get('A') or curr.inputs.get('Color1')
                        if a_sock and a_sock.is_linked:
                            curr = a_sock.links[0].from_node
                            continue
                    if curr.type == 'TEX_IMAGE' and curr.name != "AOTex":
                        src_node = curr
                        break
                    break
            else:
                src_node = inp.links[0].from_node

    if not src_node:
        return None

    # Helper to crawl and find first Image Texture node in chain
    visited = set()
    current = src_node
    while current and current not in visited:
        visited.add(current)
        if current.type == 'TEX_IMAGE':
            return current.image if current.image else None
        
        next_node = None
        for name in ['Color', 'Color1', 'Value', 'Image']:
            inp = current.inputs.get(name)
            if inp and inp.is_linked:
                next_node = inp.links[0].from_node
                break
        if not next_node:
            for inp in current.inputs:
                if inp.is_linked:
                    next_node = inp.links[0].from_node
                    break
        current = next_node

    return None


class PBR_OT_OpenInImageEditor(Operator):
    """Open the selected texture in the UV/Image Editor"""
    bl_idname = "pbr.open_in_image_editor"
    bl_label = "Open in UV/Image Editor"
    bl_description = "Open the material's texture for this slot in the UV/Image Editor"
    bl_options = {'REGISTER', 'UNDO'}

    socket_name: StringProperty()

    def execute(self, context):
        mat = context.active_object.active_material
        if not mat:
            notify.error("No active material")
            return {'CANCELLED'}

        image = get_image_for_socket(mat, self.socket_name)
        if not image:
            notify.warning(f"No texture image found for {self.socket_name}")
            return {'CANCELLED'}

        # Find or establish an IMAGE_EDITOR area to view the image
        image_editor_area = None
        
        # 1. Look for a UV Editor first (IMAGE_EDITOR with ui_type == 'UV')
        for area in context.screen.areas:
            if area.type == 'IMAGE_EDITOR' and area.ui_type == 'UV':
                image_editor_area = area
                break
                
        if not image_editor_area:
            for screen in bpy.data.screens:
                for area in screen.areas:
                    if area.type == 'IMAGE_EDITOR' and area.ui_type == 'UV':
                        image_editor_area = area
                        break
                if image_editor_area:
                    break
                    
        # 2. If no UV Editor is open, look for any Image Editor area (IMAGE_EDITOR)
        if not image_editor_area:
            for area in context.screen.areas:
                if area.type == 'IMAGE_EDITOR':
                    image_editor_area = area
                    break
                    
        if not image_editor_area:
            for screen in bpy.data.screens:
                for area in screen.areas:
                    if area.type == 'IMAGE_EDITOR':
                        image_editor_area = area
                        break
                if image_editor_area:
                    break
                    
        if image_editor_area:
            image_editor_area.spaces.active.image = image
            # Only switch ui_mode to 'VIEW' if the editor's ui_type is 'VIEW' (Image Editor)
            if image_editor_area.ui_type == 'VIEW':
                if image_editor_area.spaces.active.ui_mode != 'VIEW':
                    image_editor_area.spaces.active.ui_mode = 'VIEW'
        else:
            # Fallback: Find a VIEW_3D area and change its type to IMAGE_EDITOR
            view_3d_area = next((a for a in context.screen.areas if a.type == 'VIEW_3D'), None)
            if view_3d_area:
                view_3d_area.type = 'IMAGE_EDITOR'
                view_3d_area.ui_type = 'VIEW'
                view_3d_area.spaces.active.image = image
                view_3d_area.spaces.active.ui_mode = 'VIEW'
            else:
                context.area.type = 'IMAGE_EDITOR'
                context.area.ui_type = 'VIEW'
                context.area.spaces.active.image = image
                context.area.spaces.active.ui_mode = 'VIEW'

        notify.success(f"Opened texture '{image.name}' in UV/Image Editor")
        return {'FINISHED'}
