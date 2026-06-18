import bpy
from bpy.types import Panel

class PBR_PT_BatchMaterialPanel(Panel):
    bl_label = "Material Tools"
    bl_idname = "PBR_PT_batch_material_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "RexTools3"

    @classmethod
    def poll(cls, context):
        try:
            addon_name = ".".join(__package__.split(".")[:3]) if __package__ and __package__.startswith("bl_ext.") else (__package__.partition('.')[0] if __package__ else "RexTools3")
            prefs = context.preferences.addons[addon_name].preferences
            if not prefs.enable_batch_material:
                return False
        except Exception:
            pass
        return True

    def draw(self, context):
        layout = self.layout
        props = context.scene.rex_batch_mat_props

        # Init Section
        col = layout.column(align=True)
        col.operator("pbr.batch_init", icon='FILE_REFRESH', text="Init Batch Texture Assign")
        
        if not props.items:
            return

        layout.separator()

        # Material List Section
        box = layout.box()
        box.label(text=f"Gathered Materials ({len(props.items)})", icon='MATERIAL')
        
        # Simple scrollable list via a column in a box
        mat_col = box.column(align=True)
        for item in props.items:
            row = mat_col.row(align=True)
            # material name
            row.label(text=item.material_name, icon='MATERIAL')
            
            # status
            row.label(text=item.status)
            
            # Button to select the material as active
            op = row.operator("pbr.select_material_from_batch", text="", icon='RESTRICT_SELECT_OFF')
            op.material_name = item.material_name

        layout.separator()

        # Settings Section
        sbox = layout.box()
        sbox.label(text="Batch Settings", icon='SETTINGS')
        sbox.prop(props, "target_folder")
        sbox.prop(props, "recursive")

        layout.separator()

        # Execute Section
        row = layout.row()
        row.scale_y = 1.5
        row.operator("pbr.batch_assign_textures", icon='TEXTURE_DATA', text="Batch Assign Textures")


class PBR_OT_SelectMaterialFromBatch(bpy.types.Operator):
    """Helper to select a material from the batch list"""
    bl_idname = "pbr.select_material_from_batch"
    bl_label = "Select Material"
    
    material_name: bpy.props.StringProperty()
    
    def execute(self, context):
        mat = bpy.data.materials.get(self.material_name)
        if mat and context.active_object:
            # Find the slot with this material
            for i, slot in enumerate(context.active_object.material_slots):
                if slot.material == mat:
                    context.active_object.active_material_index = i
                    break
        return {'FINISHED'}
