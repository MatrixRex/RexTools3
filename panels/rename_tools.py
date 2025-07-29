import bpy


class RexTools3RenameToolsPanel(bpy.types.Panel):
    bl_label = "Rename Tools"
    bl_idname = "VIEW3D_PT_rextools3_rename_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'  # sidebar
    bl_category = "RexTools3"  # tab name
    
    @classmethod
    def poll(cls, context):
        
        return context.mode == 'OBJECT'
    
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.highlow_renamer_props

        selected_meshes = [obj for obj in context.selected_objects if obj.type == 'MESH']

        box = layout.box()
        box.label(text="Selected Objects:")

        if len(selected_meshes) == 0:
            box.label(text="No mesh objects selected", icon='ERROR')
        elif len(selected_meshes) == 1:
            depsgraph = context.evaluated_depsgraph_get()
            obj_eval = selected_meshes[0].evaluated_get(depsgraph)
            vertex_count = len(obj_eval.data.vertices)
            box.label(text=f"{selected_meshes[0].name} ({vertex_count} verts)", icon='MESH_DATA')
        elif len(selected_meshes) == 2:
            depsgraph = context.evaluated_depsgraph_get()
            for obj in selected_meshes:
                obj_eval = obj.evaluated_get(depsgraph)
                vertex_count = len(obj_eval.data.vertices)
                box.label(text=f"{obj.name} ({vertex_count} verts)", icon='MESH_DATA')
        else:
            box.label(text=f"{len(selected_meshes)} mesh objects selected", icon='ERROR')
            box.label(text="Select only 2 meshes")

        layout.separator()
        layout.prop(props, "obj_name")
        layout.prop(props, "high_prefix")
        layout.prop(props, "low_prefix")

        layout.separator()
        layout.operator("mesh.auto_rename_high_low", text="Auto Rename High/Low", icon='FILE_REFRESH')