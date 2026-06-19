import bpy
from ..ui import utils

class RexTools3EngineVertexStatsPanel(bpy.types.Panel):
    bl_label = "Engine Vertex Stats"
    bl_idname = "RexTools3EngineVertexStatsPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "RexTools3"  # default, but overridden by preferences on register

    @classmethod
    def poll(cls, context):
        try:
            addon_name = ".".join(__package__.split(".")[:3]) if __package__ and __package__.startswith("bl_ext.") else (__package__.partition('.')[0] if __package__ else "RexTools3")
            prefs = context.preferences.addons[addon_name].preferences
            if not prefs.enable_engine_vertex_stats:
                return False
        except Exception:
            pass
        return context.mode == 'OBJECT'

    def draw(self, context):
        layout = self.layout
        s = context.scene
        props = s.rex_engine_vertex_stats

        addon_name = ".".join(__package__.split(".")[:3]) if __package__ and __package__.startswith("bl_ext.") else (__package__.partition('.')[0] if __package__ else "RexTools3")
        prefs = context.preferences.addons[addon_name].preferences

        active_obj = context.active_object
        selected_objs = context.selected_objects
        is_mesh_selected = (active_obj and active_obj.type == 'MESH' and active_obj in selected_objs)

        # Main Engine Verts display
        col = layout.column(align=True)
        engine_verts = props.engine_verts if is_mesh_selected else 0
        col.label(text=f"Game Engine Verts: {engine_verts}", icon='SNAP_VERTEX')

        # Manual calculate button (only if auto recalculate is disabled and a mesh is selected)
        if not prefs.evstat_auto_recalculate and is_mesh_selected:
            layout.separator()
            utils.draw_call_to_action(layout, "rextools3.calculate_engine_stats", "Calculate Stats", icon='MESH_DATA', type='PRIMARY')
