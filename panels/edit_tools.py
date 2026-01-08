import bpy

class REXTools3EditToolsPanel(bpy.types.Panel):
    bl_label = "Edit Tools"
    bl_idname = "VIEW3D_PT_rextools3_edit_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "RexTools3"
    
    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'
    
    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        
        box = layout.box()
        box.label(text="Selection", icon='RESTRICT_SELECT_OFF')
        box.operator("mesh.angle_loop_select", text="Angle Loop Select", icon='ORIENTATION_NORMAL')
        
        box = layout.box()
        box.label(text="Tube Tools", icon='MOD_SCREW')
        box.operator("mesh.subdivide_tube", text="Subdivide Tube", icon='MESH_CYLINDER')
