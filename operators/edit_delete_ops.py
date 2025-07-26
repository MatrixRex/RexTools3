import bpy
from bpy.types import Menu

addon_keymaps = []

class VIEW3D_MT_delete_ops_pie(Menu):
    bl_idname = "VIEW3D_MT_delete_ops_pie"
    bl_label  = "Delete Ops"

    def draw(self, context):
        pie = self.layout.menu_pie()  # start radial layout 

        # ─── West: Separate ───
        col = pie.column(align=True)
        
        box = col.box()
        box.label(text="Separate")
        
        sep = box.column(align=True)
        
        sep.operator("mesh.separate", text="Selection").type   = 'SELECTED'
        sep.operator("mesh.separate", text="Loose Part").type  = 'LOOSE'
        sep.operator("mesh.separate", text="Material").type    = 'MATERIAL'

        # ─── East: Delete / Dissolve / Limited Dissolve ───
        col = pie.row(align=True)
        col.label(text="Delete Ops")

        # Box 1: Delete
        b1 = col.box()
        b1.label(text="Delete")
        grid = b1.grid_flow(columns=2, align=True)
        grid.operator("mesh.delete", text="Vert").type            = 'VERT'
        grid.operator("mesh.delete", text="Edge").type            = 'EDGE'
        grid.operator("mesh.delete", text="Face").type            = 'FACE'
        
        
        grid.operator("mesh.delete", text="Only Face+Edge").type  = 'EDGE_FACE'
        grid.operator("mesh.delete", text="Only Face").type        = 'ONLY_FACE'


        # Box 2: Dissolve
        b2 = col.box()
        b2.label(text="Dissolve")
        grid2 = b2.grid_flow(columns=2, align=True)
        grid2.operator("mesh.dissolve_verts", text="Vert")
        grid2.operator("mesh.dissolve_edges", text="Edge")
        grid2.operator("mesh.dissolve_faces", text="Face")

        # Box 3: Limited Dissolve
        b3 = col.box()
        b3.label(text="")
        grid3 = b3.grid_flow(columns=1, align=True)
        grid3.operator("mesh.edge_collapse",      text="Collapse Face+Edge")
        grid3.operator("mesh.dissolve_limited", text="Limited Dissolve")
        grid3.operator("mesh.delete_edgeloop",  text="Edge Loops")

        # ─── South: Merge & Split ───
        row = pie.row(align=True)

        # Merge column
        col_m = row.column(align=True)
        m1 = col_m.box()
        m1.label(text="Merge")
        mcol = m1.column(align=True)
        mcol.operator("mesh.merge", text="Center").type    = 'CENTER'
        mcol.operator("mesh.merge", text="Cursor").type    = 'CURSOR'
        mcol.operator("mesh.merge", text="Collapse").type  = 'COLLAPSE'
        m2 = col_m.box()
        # use remove_doubles for merge by distance
        m2.operator("mesh.remove_doubles", text="By Distance")

        # Split box
        bsplit = row.box()
        bsplit.label(text="Split")
        split = bsplit.column(align=True)
        split.operator("mesh.split", text="Selection")
        split.operator("mesh.edge_split", text="By Edges").type       = 'EDGE'
        split.operator("mesh.edge_split", text="By Vertices").type    = 'VERT'

        # ─── North: Custom ───
        col_c = pie.column(align=True)
        
        box_c = col_c.box()
        row_c = box_c.row(align=True)
        row_c.operator("rextools3.delete_linked_ex", text="Delete Linked")
        row_c.operator("rextools3.checker_dissolve", text="Checker Dissolve")
        row_c.operator("rextools3.checker_dissolve_selected", text="Checker Dissolve Selected")
        row_c.operator("rextools3.loop_dissolve_ex", text="Loop Dissolve")

        # NW, NE, SW, SE left empty

def register():
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.get('3D View')
    if km:
        kmi = km.keymap_items.new(
            'wm.call_menu_pie', 'X', 'PRESS',
        )
        kmi.properties.name = VIEW3D_MT_delete_ops_pie.bl_idname
        addon_keymaps.append((km, kmi))

def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
