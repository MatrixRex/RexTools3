import bpy
from bpy.types import Panel
from ..ui import utils
from ..operators.object_auto_rename_low_high import MESH_OT_auto_rename_high_low

class RexTools3MarmosetBridgePanel(Panel):
    bl_label = "Marmoset Bridge"
    bl_idname = "VIEW3D_PT_rextools3_marmoset_bridge"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "RexTools3"
    
    @classmethod
    def poll(cls, context):
        try:
            addon_name = ".".join(__package__.split(".")[:3]) if __package__ and __package__.startswith("bl_ext.") else (__package__.partition('.')[0] if __package__ else "RexTools3")
            prefs = context.preferences.addons[addon_name].preferences
            if not prefs.enable_marmoset_bridge:
                return False
        except Exception:
            pass
        return context.mode == 'OBJECT'
        
    def draw(self, context):
        layout = self.layout
        props = context.scene.rex_marmoset_bridge_props
        
        # 1. Output Settings
        col_out = utils.draw_section(layout, "Bake Output Settings", icon='TOOL_SETTINGS')
        col_out.prop(props, "export_path", text="Output Folder")
        col_out.prop(props, "asset_name", text="Asset Name")
        col_out.prop(props, "resolution", text="Resolution")
        col_out.prop(props, "file_format", text="File Format")
        
        layout.separator()
        
        # 2. Bake Maps
        col_maps = utils.draw_section(layout, "Bake Maps", icon='TEXTURE')
        row1 = col_maps.row(align=True)
        row1.prop(props, "bake_albedo", text="Albedo")
        row1.prop(props, "bake_normals", text="Normals")
        
        row2 = col_maps.row(align=True)
        row2.prop(props, "bake_roughness", text="Roughness")
        row2.prop(props, "bake_metallic", text="Metallic")
        
        row3 = col_maps.row(align=True)
        row3.prop(props, "bake_ao", text="AO")
        
        layout.separator()
        
        # 3. Export & Handoff
        col_send = utils.draw_section(layout, "Export & Handoff", icon='EXPORT')
        col_send.prop(props, "auto_rename", text="Auto Rename Meshes/Mats")
        col_send.prop(props, "send_textures", text="Send High Textures")
        
        selected_meshes = [obj for obj in context.selected_objects if obj.type == 'MESH']
        
        col_send.separator()
        if len(selected_meshes) != 2:
            col_send.label(text="Select exactly 2 meshes (High/Low)", icon='INFO')
        else:
            low_poly, high_poly = MESH_OT_auto_rename_high_low.detect_low_high(selected_meshes, context)
            if low_poly and high_poly:
                col_send.label(text=f"Low: {low_poly.name}", icon='MESH_DATA')
                col_send.label(text=f"High: {high_poly.name}", icon='MESH_DATA')
                col_send.separator()
                
            utils.draw_call_to_action(col_send, "rextools3.marmoset_bridge_send", "Prepare & Send to Marmoset", icon='EXPORT', type='PRIMARY')
            col_send.separator()
            col_send.operator("rextools3.marmoset_bridge_prep", text="Auto Name Meshes & Materials", icon='FILE_REFRESH')
            
        layout.separator()
        
        # 3. Import Baked Textures
        col_import = utils.draw_section(layout, "Import Textures", icon='IMPORT')
        utils.draw_call_to_action(col_import, "rextools3.marmoset_bridge_get_textures", "Import Baked Textures", icon='IMPORT', type='PRIMARY')
