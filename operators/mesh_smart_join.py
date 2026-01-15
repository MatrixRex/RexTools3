import bpy
from bpy.types import Operator
from bpy.props import BoolProperty

class OBJECT_OT_RexTools3SmartJoin(Operator):
    """Join mesh objects and warn if UV map names are mismatched"""
    bl_idname = "object.rextools3_smart_join"
    bl_label = "Smart Join"
    bl_description = "Join mesh objects and warn if UV map names are mismatched. Checks for UV name consistency before merging."
    bl_options = {'REGISTER', 'UNDO'}

    apply_modifiers: BoolProperty(
        name="Apply Modifiers",
        description="Apply all modifiers before joining",
        default=False
    )

    @classmethod
    def poll(cls, context):
        return (context.active_object and 
                context.active_object.type == 'MESH' and 
                len(context.selected_objects) > 1)

    def invoke(self, context, event):
        # Sync from sidebar property only on initial call
        self.apply_modifiers = context.scene.rex_common_settings.smart_join_apply_modifiers
        return self.execute(context)

    def execute(self, context):
        from ..core import notify
        
        # Check if we should warn about UVs before doing anything
        # We perform the check on the current selection
        targets = [o for o in context.selected_objects if o.type in {'MESH', 'CURVE', 'SURFACE', 'FONT', 'META'}]
        if not targets:
            return {'CANCELLED'}

        meshes_before = [o for o in targets if o.type == 'MESH']
        if len(meshes_before) > 1:
            uv_sets = []
            for o in meshes_before:
                names = sorted([uv.name for uv in o.data.uv_layers]) if hasattr(o.data, "uv_layers") else []
                uv_sets.append(names)
            if uv_sets:
                base = uv_sets[0]
                for other in uv_sets[1:]:
                    if other != base:
                        notify.warning("UV slots may not merge merged. Mismatched UV names.")
                        break

        if self.apply_modifiers:
            notify.info("Smart Join: Apply Modifiers was ON")
            
            # Application: Convert everything to mesh (applies modifiers)
            # This is an undoable action in the stack
            bpy.ops.object.convert(target='MESH')

        try:
            # Final join
            bpy.ops.object.join()
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Join failed: {e}")
            return {'CANCELLED'}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "apply_modifiers")

def menu_func(self, context):
    self.layout.operator(OBJECT_OT_RexTools3SmartJoin.bl_idname, text="Smart Join (UV Check)")

def register():
    bpy.types.VIEW3D_MT_object.append(menu_func)

def unregister():
    bpy.types.VIEW3D_MT_object.remove(menu_func)
