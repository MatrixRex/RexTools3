import bpy
from bpy.types import Operator
from bpy.props import StringProperty, EnumProperty
from ..core import notify

class PBR_OT_DebugPreview(Operator):
    bl_idname = "pbr.debug_preview"
    bl_label = "Debug Preview"
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
                node = find_node("NormalTex", "Normal Texture")
                if node: 
                    print(f"DEBUG: Success! Found '{slot}' -> '{node.name}'")
                    return node.outputs.get('Color', node.outputs[0])
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
