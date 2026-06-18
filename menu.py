import bpy

def draw_uv_menu(self, context):
    try:
        addon_name = ".".join(__package__.split(".")[:3]) if __package__ and __package__.startswith("bl_ext.") else (__package__.partition('.')[0] if __package__ else "RexTools3")
        prefs = context.preferences.addons[addon_name].preferences
        if not prefs.enable_uv_mesh_tools:
            return
    except Exception:
        pass
    layout = self.layout
    layout.separator()
    layout.operator(
        "rextools3.uv_seam_area_by_angle_modal",
        text="Seam Area by Angle (Modal)",
        icon='MOD_SMOOTH'
    )


def register():
    
    bpy.types.VIEW3D_MT_uv_map.append(draw_uv_menu)

def unregister():
    bpy.types.VIEW3D_MT_uv_map.remove(draw_uv_menu)
