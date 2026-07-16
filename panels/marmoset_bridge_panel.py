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
        
        renamer_props = context.scene.highlow_renamer_props
        selected_meshes = [obj for obj in context.selected_objects if obj.type == 'MESH']
        
        col_send.separator()
        if len(selected_meshes) < 2:
            col_send.label(text="Select at least 2 meshes (High/Low)", icon='INFO')
        else:
            low_objs, high_objs = MESH_OT_auto_rename_high_low.classify_low_high(selected_meshes, context)
            if not low_objs or not high_objs:
                col_send.label(text="Select at least 1 Low and 1 High poly mesh", icon='INFO')
            else:
                # Resolve prefixes and names
                asset_name = props.asset_name.strip()
                if not asset_name:
                    asset_name = MESH_OT_auto_rename_high_low.clean_base_name(low_objs[0].name)
                    if not asset_name:
                        asset_name = "Asset"
                low_prefix = renamer_props.low_prefix
                high_prefix = renamer_props.high_prefix

                def get_common_name(obj):
                    name = obj.name
                    for pref in [asset_name + low_prefix, asset_name + high_prefix]:
                        if name.startswith(pref):
                            var = name[len(pref):]
                            if var.startswith("_"):
                                var = var[1:]
                            return var.lower()
                    return MESH_OT_auto_rename_high_low.clean_base_name(name).lower()

                # Pair them
                pairs = []
                unpaired_low = []
                unpaired_high = []
                
                if len(low_objs) == 1 and len(high_objs) == 1:
                    low_obj = low_objs[0]
                    high_obj = high_objs[0]
                    base = get_common_name(low_obj)
                    pairs.append((base, low_obj, high_obj))
                else:
                    low_by_base = {get_common_name(o): o for o in low_objs}
                    high_by_base = {get_common_name(o): o for o in high_objs}
                    all_bases = sorted(list(set(low_by_base.keys()) | set(high_by_base.keys())))
                    
                    for base in all_bases:
                        low_obj = low_by_base.get(base)
                        high_obj = high_by_base.get(base)
                        if low_obj and high_obj:
                            pairs.append((base, low_obj, high_obj))
                        elif low_obj:
                            unpaired_low.append(low_obj)
                        elif high_obj:
                            unpaired_high.append(high_obj)

                # Draw sets
                for idx, (base, low_obj, high_obj) in enumerate(pairs):
                    display_base = base.title() if base else asset_name
                    # set 1: common_name (low_mesh, high_mesh)
                    col_send.label(text=f"Set {idx + 1}: {display_base} ({low_obj.name}, {high_obj.name})", icon='MESH_DATA')
                    
                # Draw unpaired meshes if any
                for obj in unpaired_low:
                    col_send.label(text=f"Unpaired Low: {obj.name}", icon='ERROR')
                for obj in unpaired_high:
                    col_send.label(text=f"Unpaired High: {obj.name}", icon='ERROR')
                col_send.separator()
                
                utils.draw_call_to_action(col_send, "rextools3.marmoset_bridge_send", "Prepare & Send to Marmoset", icon='EXPORT', type='PRIMARY')
                col_send.separator()
                col_send.operator("rextools3.marmoset_bridge_prep", text="Auto Name Meshes & Materials", icon='FILE_REFRESH')
            
        layout.separator()
        
        # 3. Import Baked Textures
        col_import = utils.draw_section(layout, "Import Textures", icon='IMPORT')
        utils.draw_call_to_action(col_import, "rextools3.marmoset_bridge_get_textures", "Import Baked Textures", icon='IMPORT', type='PRIMARY')
