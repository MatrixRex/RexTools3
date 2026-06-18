import bpy
from bpy.types import Menu

import bpy
from bpy.types import Menu

class VIEW3D_MT_my_grouped_pie(Menu):
    bl_idname = "VIEW3D_MT_my_grouped_pie"
    bl_label = "My Grouped Pie"

    def draw(self, context):
        pie = self.layout.menu_pie()

        # ─── West slice: Selection tools ───
        # Use heading="…" to draw the title label
        col = pie.column(align=True, heading="Selection")
        box = col.box()                      # start a framed box
        sel = box.column(align=True)         # column inside the box
        sel.operator("object.select_all", text="Select All").action = 'SELECT'
        sel.operator("object.delete",     text="Delete")
        sel.operator("object.duplicate_move", text="Duplicate")

        # ─── East slice: Transform tools ───
        col = pie.column(align=True, heading="Transforms")
        box = col.box()
        tfm = box.row(align=True)            # row inside the box
        tfm.operator("transform.translate", text="Move")
        tfm.operator("transform.rotate",    text="Rotate")
        # single‐column for Scale
        box.operator("transform.resize", text="Scale")

        # ─── South slice: Miscellaneous ───
        # manually adding a label inside a box
        col = pie.column(align=True)
        box = col.box()
        box.label(text="Other Ops")
        box.operator("wm.save_mainfile", text="Save")
        box.operator("wm.open_mainfile", text="Open")


addon_keymaps = []

def register():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.get('3D View')
        if not km:
            km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        
        kmi = km.keymap_items.new(
            idname="wm.call_menu_pie", 
            type='X', 
            value='PRESS', 
            shift=True
        )
        kmi.properties.name = VIEW3D_MT_my_grouped_pie.bl_idname
        try:
            addon_name = __package__.partition('.')[0]
            prefs = bpy.context.preferences.addons[addon_name].preferences
            kmi.active = prefs.enable_pie_test
        except Exception:
            pass
        addon_keymaps.append((km, kmi))


def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()  # :contentReference[oaicite:2]{index=2}
