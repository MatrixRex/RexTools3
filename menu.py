import bpy

def draw_uv_menu(self, context):
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
