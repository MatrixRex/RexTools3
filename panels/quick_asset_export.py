import bpy
from ..ui import utils

class REXTOOLS3_PT_QuickAssetExport(bpy.types.Panel):
    bl_label = "Quick Asset Export"
    bl_idname = "REXTOOLS3_PT_quick_asset_export"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "RexTools3"

    @classmethod
    def poll(cls, context):
        try:
            addon_name = ".".join(__package__.split(".")[:3]) if __package__ and __package__.startswith("bl_ext.") else (__package__.partition('.')[0] if __package__ else "RexTools3")
            prefs = context.preferences.addons[addon_name].preferences
            if not prefs.enable_quick_asset_export:
                return False
        except Exception:
            pass
        return context.active_object is not None

    def draw(self, context):
        layout = self.layout
        settings = context.scene.rex_asset_export_settings

        col = utils.draw_section(layout, "Quick Asset Export Settings", icon='ASSET_MANAGER')

        col.prop(settings, "library", text="Library")
        if settings.library == "__CUSTOM__":
            col.prop(settings, "custom_path", text="Custom Folder")
        col.prop(settings, "catalog_selection", text="Catalog")
        if settings.catalog_selection == "__CUSTOM__":
            col.prop(settings, "catalog", text="Catalog Path")
        
        col.separator()
        col.prop(settings, "separate_files", text="One file per object")
        col.prop(settings, "clear_after", text="Keep working file clean")
        col.prop(settings, "preview_wait", text="Preview Wait (s)")

        col.separator()
        utils.draw_call_to_action(col, "rextools3.quick_asset_export", "Save Selected as Asset", icon='EXPORT', type='PRIMARY')
