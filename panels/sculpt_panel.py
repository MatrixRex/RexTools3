import bpy

class RexTools3SculptToolsPanel(bpy.types.Panel):
    bl_label = "Sculpt Tools"
    bl_idname = "VIEW3D_PT_rextools3_sculpt_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "RexTools3"
    
    @classmethod
    def poll(cls, context):
        return True
    
    def draw(self, context):
        layout = self.layout
        
        box = layout.box()
        box.label(text="Sculpt Assets", icon='ASSET_MANAGER')
        col = box.column(align=True)
        col.operator("rextools3.batch_assign_sculpt_previews", text="Batch Assign Previews", icon='FILE_FOLDER')

