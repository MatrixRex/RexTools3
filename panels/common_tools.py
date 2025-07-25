import bpy


class RexTools3CommonToolsPanel(bpy.types.Panel):
    bl_label = "Common Tools"
    bl_idname = "VIEW3D_PT_rextools3_common_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'  # sidebar
    bl_category = "RexTools3"  # tab name
    
    
    
    
    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        layout.label(text="Common Tools")
        layout.operator("rextools3.open_folder", text="Open Folder")
        layout.operator("outliner.orphans_purge", text="Purge Orphans")
        layout.operator("rextools3.modal_example", text="Run Modal Example")
        # Show the live X/Y:
        row = layout.row()
        row.label(text=f"X: {wm.modal_x}")
        row.label(text=f"Y: {wm.modal_y}")
        