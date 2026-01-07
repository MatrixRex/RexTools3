import bpy
from bpy.types import Operator
from ..overlay_drawer import ViewportOverlay, MessageBox

class MESH_OT_RexTools3SmartJoin(Operator):
    """Join mesh objects and warn if UV map names are mismatched"""
    bl_idname = "mesh.rextools3_smart_join"
    bl_label = "Smart Join (UV Check)"
    bl_description = "Join mesh objects and warn if UV map names are mismatched. Checks for UV name consistency before merging."
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.active_object and 
                context.active_object.type == 'MESH' and 
                len(context.selected_objects) > 1)

    def execute(self, context):
        # Filter for actual meshes
        meshes = [o for o in context.selected_objects if o.type == 'MESH']
        
        if len(meshes) > 1:
            # Collect UV names for all meshes
            uv_sets = []
            for o in meshes:
                if hasattr(o.data, "uv_layers"):
                    names = sorted([uv.name for uv in o.data.uv_layers])
                    uv_sets.append(names)
            
            # Compare to the first mesh
            if uv_sets:
                mismatch = False
                base = uv_sets[0]
                for other in uv_sets[1:]:
                    if other != base:
                        mismatch = True
                        break
                
                if mismatch:
                    # Spawn overlay warning
                    ov = ViewportOverlay(title="", x='CENTER', y='BOTTOM')
                    ov.show_bg = False
                    ov.padding = 0
                    ov.timeout = 5
                    ov.add(MessageBox(
                        text="Warning: UV slots not merged. Mismatched UV names.",
                        type='WARNING',
                        width=350,
                        show_icon=True
                    ))
                    ov.show()

        # Execute the native join operation
        try:
            return bpy.ops.object.join()
        except Exception as e:
            self.report({'ERROR'}, f"Join failed: {e}")
            return {'CANCELLED'}

def menu_func(self, context):
    self.layout.operator(MESH_OT_RexTools3SmartJoin.bl_idname, text="Smart Join (UV Check)")

def register():
    # Adding it to the standard Object menu makes it assignable via right-click
    bpy.types.VIEW3D_MT_object.append(menu_func)

def unregister():
    bpy.types.VIEW3D_MT_object.remove(menu_func)
