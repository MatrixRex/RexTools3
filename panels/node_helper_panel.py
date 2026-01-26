import bpy

class REXTOOLS3_PT_NodeHelper(bpy.types.Panel):
    bl_label = "Node Socket Inspector"
    bl_idname = "NODE_PT_rextools3_node_inspector"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "RexTools3"

    @classmethod
    def poll(cls, context):
        # Only show in Shader Editor and when a node is selected
        if not context.space_data or context.space_data.type != 'NODE_EDITOR':
            return False
        # Limit to Shader Node Editor
        if context.space_data.tree_type != 'ShaderNodeTree':
            return False
        return context.active_node is not None

    def draw(self, context):
        layout = self.layout
        node = context.active_node
        
        if not node:
            layout.label(text="No active node selected")
            return
            
        # Node Header Info
        main_box = layout.box()
        col = main_box.column(align=True)
        row = col.row()
        row.label(text=node.label if node.label else node.name, icon='NODE')
        
        row = col.row(align=True)
        row.scale_y = 0.8
        row.label(text=f"ID: {node.bl_idname}", icon='NONE')
        copy_id = row.operator("rextools3.copy_text", text="", icon='COPYDOWN')
        copy_id.text = node.bl_idname
        
        layout.separator()

        # Outputs Section
        out_box = layout.box()
        row = out_box.row()
        row.label(text="Outputs", icon='EXPORT')
        
        if not node.outputs:
            out_box.label(text="No Outputs", icon='NONE')
        else:
            for i, sock in enumerate(node.outputs):
                slot_box = out_box.box()
                row = slot_box.row(align=True)
                row.label(text=f"{i}: {sock.name}")
                
                # Right side: Type + Copy
                right = row.row(align=True)
                right.alignment = 'RIGHT'
                right.label(text=sock.type)
                copy = right.operator("rextools3.copy_text", text="", icon='COPYDOWN')
                copy.text = sock.name

        layout.separator()

        # Inputs Section
        in_box = layout.box()
        row = in_box.row()
        row.label(text="Inputs", icon='IMPORT')
        
        if not node.inputs:
            in_box.label(text="No Inputs", icon='NONE')
        else:
            for i, sock in enumerate(node.inputs):
                slot_box = in_box.box()
                row = slot_box.row(align=True)
                row.label(text=f"{i}: {sock.name}")
                
                # Right side: Type + Copy
                right = row.row(align=True)
                right.alignment = 'RIGHT'
                right.label(text=sock.type)
                copy = right.operator("rextools3.copy_text", text="", icon='COPYDOWN')
                copy.text = sock.name

class REXTOOLS3_PT_NodeLayout(bpy.types.Panel):
    bl_label = "Node Layout"
    bl_idname = "NODE_PT_rextools3_node_layout"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "RexTools3"

    def draw(self, context):
        layout = self.layout
        layout.operator("pbr.arrange_nodes", text="Arrange All Nodes", icon='NODETREE')
