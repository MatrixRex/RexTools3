import bpy
from bpy.types import Operator
from bpy.props import BoolProperty

class REXTOOLS3_OT_UnhideAll(Operator):
    """Unhide all objects and optionally hide the 'Cutters' collection"""
    bl_idname = "object.rextools3_unhide_all"
    bl_label = "Unhide All (Rex)"
    bl_options = {'REGISTER', 'UNDO'}

    hide_cutters: BoolProperty(
        name="Hide Cutters",
        description="Hide collection named 'Cutters' after performing Unhide All",
        default=True
    )

    @classmethod
    def poll(cls, context):
        # Only allow in 3D View and Object Mode
        return context.area.type == 'VIEW_3D' and context.mode == 'OBJECT'

    def execute(self, context):
        # Perform standard unhide all
        bpy.ops.object.hide_view_clear(select=False)

        if self.hide_cutters:
            hid_any = self.hide_collection_by_name(context, "Cutters")
            if hid_any:
                self.report({'INFO'}, "Unhid all objects and hid 'Cutters' collection")
            else:
                self.report({'INFO'}, "Unhid all objects")
        else:
            self.report({'INFO'}, "Unhid all objects")
            
        return {'FINISHED'}

    def hide_collection_by_name(self, context, name):
        found_any = False
        for coll in bpy.data.collections:
            if coll.name == name:
                layer_coll = self.find_layer_collection(context.view_layer.layer_collection, coll)
                if layer_coll:
                    layer_coll.hide_viewport = True
                    found_any = True
        return found_any

    def find_layer_collection(self, layer_collection, collection):
        if layer_collection.collection == collection:
            return layer_collection
        for child in layer_collection.children:
            found = self.find_layer_collection(child, collection)
            if found:
                return found
        return None

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "hide_cutters", toggle=True)
