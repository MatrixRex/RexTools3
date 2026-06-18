import bpy
from bpy.types import Menu

addon_keymaps = []

class VIEW3D_MT_rex_shading_pie(Menu):
    bl_idname = "VIEW3D_MT_rex_shading_pie"
    bl_label = "Rex Shading"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        view = context.space_data

        if not view or view.type != 'VIEW_3D':
            return

        # 1. West (Left): Wireframe
        pie.prop_enum(view.shading, "type", value='WIREFRAME')

        # 2. East (Right): Solid
        pie.prop_enum(view.shading, "type", value='SOLID')

        # 3. South (Bottom): X-Ray
        if context.pose_object:
            pie.prop(view.overlay, "show_xray_bone", icon='XRAY')
        else:
            xray_active = (
                (context.mode == 'EDIT_MESH') or
                (view.shading.type in {'SOLID', 'WIREFRAME'})
            )
            if xray_active:
                sub = pie
            else:
                sub = pie.row()
                sub.active = False
            sub.prop(
                view.shading,
                "show_xray_wireframe" if (view.shading.type == 'WIREFRAME') else "show_xray",
                text="Toggle X-Ray",
                icon='XRAY',
            )

        # 4. North (Top): Toggle Overlays
        pie.prop(view.overlay, "show_overlays", text="Toggle Overlays", icon='OVERLAY')

        # 5. North-West (Top-Left): Material Preview
        pie.prop_enum(view.shading, "type", value='MATERIAL')

        # 6. North-East (Top-Right): Rendered
        pie.prop_enum(view.shading, "type", value='RENDERED')

        # 7. South-West (Bottom-Left): Context-aware Retopo or Weight Contours
        if context.mode == 'EDIT_MESH' and hasattr(view.overlay, "show_retopology"):
            pie.prop(view.overlay, "show_retopology", text="Retopo", icon='MESH_DATA')
        elif context.mode == 'PAINT_WEIGHT' and hasattr(view.overlay, "show_wpaint_contours"):
            pie.prop(view.overlay, "show_wpaint_contours", text="Contours", icon='WPAINT_HLT')
        else:
            pie.separator()

        # 8. South-East (Bottom-Right): Show wireframe overlay toggle always
        if hasattr(view.overlay, "show_wireframes"):
            pie.prop(view.overlay, "show_wireframes", text="Wireframe Overlay", icon='SHADING_WIRE')
        else:
            pie.separator()


class VIEW3D_MT_rex_view_pie(Menu):
    bl_idname = "VIEW3D_MT_rex_view_pie"
    bl_label = "Rex View"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        # 1. West (Left) - Orbit 90° Left
        op = pie.operator("view3d.view_orbit", text="Orbit 90° Left", icon='LOOP_BACK')
        op.type = 'ORBITLEFT'
        op.angle = 1.5707963

        # 2. East (Right) - Orbit 90° Right
        op = pie.operator("view3d.view_orbit", text="Orbit 90° Right", icon='LOOP_FORWARDS')
        op.type = 'ORBITRIGHT'
        op.angle = 1.5707963

        # 3. South (Bottom) - Bottom View
        op = pie.operator("view3d.view_axis", text="Bottom", icon='TRIA_DOWN')
        op.type = 'BOTTOM'

        # 4. North (Top) - Top View
        op = pie.operator("view3d.view_axis", text="Top", icon='TRIA_UP')
        op.type = 'TOP'

        # 5. North-West (Top-Left) - Back View
        op = pie.operator("view3d.view_axis", text="Back", icon='AXIS_FRONT')
        op.type = 'BACK'

        # 6. North-East (Top-Right) - Front View
        op = pie.operator("view3d.view_axis", text="Front", icon='AXIS_FRONT')
        op.type = 'FRONT'

        # 7. South-West (Bottom-Left) - Left View
        op = pie.operator("view3d.view_axis", text="Left", icon='TRIA_LEFT')
        op.type = 'LEFT'

        # 8. South-East (Bottom-Right) - Right View
        op = pie.operator("view3d.view_axis", text="Right", icon='TRIA_RIGHT')
        op.type = 'RIGHT'


def register():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.get('3D View')
        if not km:
            km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        
        # Load preference state
        active_state = True
        try:
            addon_name = __package__.partition('.')[0]
            prefs = bpy.context.preferences.addons[addon_name].preferences
            active_state = prefs.enable_shading_pie
        except Exception:
            pass

        kmi = km.keymap_items.new(
            idname="wm.call_menu_pie",
            type='Z',
            value='PRESS',
        )
        kmi.properties.name = VIEW3D_MT_rex_shading_pie.bl_idname
        kmi.active = active_state
        addon_keymaps.append((km, kmi))

        kmi_view = km.keymap_items.new(
            idname="wm.call_menu_pie",
            type='W',
            value='PRESS',
        )
        kmi_view.properties.name = VIEW3D_MT_rex_view_pie.bl_idname
        kmi_view.active = active_state
        addon_keymaps.append((km, kmi_view))


def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
