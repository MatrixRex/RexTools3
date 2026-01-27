import bpy
from bpy.types import Operator
from ..core import notify

addon_keymaps = []


class REXTOOLS3_OT_SmartJoin(Operator):
    """Join objects with UV mismatch checking"""
    bl_idname = "rextools3.smart_join"
    bl_label = "Smart Join"
    bl_description = "Join selected objects with UV mismatch checking"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (
            context.mode == 'OBJECT' and 
            context.selected_objects and 
            len([obj for obj in context.selected_objects if obj.type == 'MESH']) >= 2
        )

    def check_uv_mismatch(self, selected_meshes):
        """Check if all selected meshes have the same UV map structure"""
        if not selected_meshes:
            return False, ""

        # Get UV map names from the first object
        first_obj = selected_meshes[0]
        ref_uv_names = sorted([uv.name for uv in first_obj.data.uv_layers])
        ref_uv_count = len(ref_uv_names)

        mismatched_names = []
        count_mismatch = False

        for obj in selected_meshes[1:]:
            obj_uv_names = sorted([uv.name for uv in obj.data.uv_layers])
            obj_uv_count = len(obj_uv_names)

            if obj_uv_count != ref_uv_count:
                count_mismatch = True
            
            if obj_uv_names != ref_uv_names:
                mismatched_names.append(obj.name)

        if count_mismatch:
            return True, "UV count mismatch! Some objects have more UV maps than others."
        
        if mismatched_names:
            return True, f"UV name mismatch! UV maps won't merge properly: {', '.join(ref_uv_names)}"

        return False, ""

    def execute(self, context):
        selected_meshes = [obj for obj in context.selected_objects if obj.type == 'MESH']
        
        if len(selected_meshes) < 2:
            self.report({'WARNING'}, "Need at least 2 mesh objects selected")
            return {'CANCELLED'}
        
        # Check for UV mismatches
        has_mismatch, message = self.check_uv_mismatch(selected_meshes)
        
        if has_mismatch:
            notify.warning(f"UV Issue: {message}")
            self.report({'WARNING'}, message)
        
        # Perform the join
        try:
            bpy.ops.object.join()
            self.report({'INFO'}, f"Joined {len(selected_meshes)} objects")
        except Exception as e:
            self.report({'ERROR'}, f"Join failed: {e}")
            return {'CANCELLED'}
        
        return {'FINISHED'}


def register():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.get('Object Mode')
        if not km:
            km = kc.keymaps.new(name='Object Mode', space_type='EMPTY')
        
        kmi = km.keymap_items.new(
            REXTOOLS3_OT_SmartJoin.bl_idname,
            'J', 'PRESS',
            ctrl=True
        )
        addon_keymaps.append((km, kmi))


def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
