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
        
        # 3. Export & Bake Groups
        col_send = utils.draw_section(layout, "Export & Bake Groups", icon='EXPORT')
        col_send.prop(props, "auto_rename", text="Auto Rename Meshes/Mats")
        col_send.prop(props, "send_textures", text="Send High Textures")
        
        col_send.separator()
        
        # Group toolbar: Refresh & Global Lock
        tb_row = col_send.row(align=True)
        tb_row.operator("rextools3.marmoset_bridge_refresh_groups", text="Refresh Groups", icon='FILE_REFRESH')
        
        lock_icon = 'LOCKED' if props.global_lock else 'UNLOCKED'
        lock_op = tb_row.operator("rextools3.marmoset_bridge_toggle_lock", text="Lock All" if not props.global_lock else "Unlock All", icon=lock_icon)
        lock_op.group_index = -1
        
        col_send.separator()
        
        if not props.bake_groups:
            col_send.label(text="No Bake Groups detected. Select meshes & refresh.", icon='INFO')
        else:
            for i, bg in enumerate(props.bake_groups):
                box = col_send.box()
                header = box.row(align=True)
                
                # Expand Arrow
                exp_icon = 'DISCLOSURE_TRI_DOWN' if bg.is_expanded else 'DISCLOSURE_TRI_RIGHT'
                exp_op = header.operator("rextools3.marmoset_bridge_toggle_expand", text="", icon=exp_icon, emboss=False)
                exp_op.group_index = i
                
                # Group Label
                low_cnt = len(bg.low_meshes)
                high_cnt = len(bg.high_meshes)
                header.label(text=f"{bg.group_name} ({low_cnt} Low, {high_cnt} High)")
                
                # Per-group Lock
                g_lock_icon = 'LOCKED' if bg.is_locked else 'UNLOCKED'
                g_lock_op = header.operator("rextools3.marmoset_bridge_toggle_lock", text="", icon=g_lock_icon, emboss=False)
                g_lock_op.group_index = i
                
                # Single Group Send
                send_op = header.operator("rextools3.marmoset_bridge_send", text="", icon='EXPORT', emboss=True)
                send_op.group_name = bg.group_name
                
                # Expanded meshes view
                if bg.is_expanded:
                    sub_col = box.column(align=True)
                    sub_col.separator()
                    if bg.low_meshes:
                        sub_col.label(text="Low Meshes:", icon='OUTLINER_OB_MESH')
                        for ref in bg.low_meshes:
                            sub_col.label(text=f"  - {ref.name}")
                    if bg.high_meshes:
                        sub_col.label(text="High Meshes:", icon='OUTLINER_OB_MESH')
                        for ref in bg.high_meshes:
                            sub_col.label(text=f"  - {ref.name}")

        col_send.separator()
        utils.draw_call_to_action(col_send, "rextools3.marmoset_bridge_send", "Send Bake Groups to Marmoset", icon='EXPORT', type='PRIMARY')
        col_send.separator()
        col_send.operator("rextools3.marmoset_bridge_prep", text="Auto Name Meshes & Materials", icon='FILE_REFRESH')
            
        layout.separator()
        
        # 4. Import Baked Textures
        col_import = utils.draw_section(layout, "Import Textures", icon='IMPORT')
        utils.draw_call_to_action(col_import, "rextools3.marmoset_bridge_get_textures", "Import Baked Textures", icon='IMPORT', type='PRIMARY')

