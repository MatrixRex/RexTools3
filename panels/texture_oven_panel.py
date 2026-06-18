import bpy
from ..ui.utils import draw_section, draw_call_to_action

class REXTOOLS3_PT_TextureOvenPanel(bpy.types.Panel):
    bl_label = "Texture Oven"
    bl_idname = "REXTOOLS3_PT_TextureOvenPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Texture Oven"

    @classmethod
    def poll(cls, context):
        try:
            addon_name = ".".join(__package__.split(".")[:3]) if __package__ and __package__.startswith("bl_ext.") else (__package__.partition('.')[0] if __package__ else "RexTools3")
            prefs = context.preferences.addons[addon_name].preferences
            if not prefs.enable_texture_oven:
                return False
        except Exception:
            pass
        return context.mode == 'OBJECT'

    def draw(self, context):
        layout = self.layout
        props = context.scene.rex_texture_oven_props

        # 1. Mesh Selection Section
        mesh_sec = draw_section(layout, "Mesh Selection", icon='MESH_DATA')
        
        # Target picker
        mesh_sec.prop(props, "target_object", text="Target (Low)")

        # Source picker
        mesh_sec.prop(props, "source_object", text="Source (High)")

        # 2. Explode Settings (Only visible when Target object is set)
        if props.target_object:
            # Check if Displacement modifier actually exists
            modifier_exists = any(
                mod.type == 'DISPLACE' and mod.name == "Displacement_imposter" 
                for mod in props.target_object.modifiers
            )
            
            explode_sec = draw_section(layout, "Explode Settings", icon='MOD_EXPLODE')
            explode_sec.prop(props, "displacement_strength", text="Distance", slider=True)
            if not modifier_exists:
                explode_sec.label(text="Modifier will be created on bake", icon='INFO')

        # 3. Bake Settings & Trigger
        if props.target_object and props.source_object:
            bake_sec = draw_section(layout, "Bake Settings", icon='RENDER_STILL')
            bake_sec.prop(props, "bake_mode", text="Mode")
            bake_sec.prop(props, "resolution", text="Resolution")
            bake_sec.prop(props, "ao_sample_count", text="AO Samples")
            
            draw_call_to_action(layout, "rextools3.texture_oven_bake", "Bake Imposter", icon='RENDER_STILL', type='PRIMARY')

        # 4. Save/Output Settings
        save_sec = draw_section(layout, "Output Settings", icon='EXPORT')
        save_sec.prop(props, "save_directory", text="")
        
        # Draw save CTA
        draw_call_to_action(layout, "rextools3.texture_oven_save_images", "Save Textures", icon='DISK_DRIVE', type='SECONDARY')
