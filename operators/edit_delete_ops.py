import bpy
from bpy.types import Menu

addon_keymaps = []

class VIEW3D_MT_delete_ops_pie(Menu):
    bl_idname = "VIEW3D_MT_delete_ops_pie"
    bl_label  = "Delete Ops"

    def draw(self, context):
        layout = self.layout
        
        # --- DELETE ---
        col = layout.column(align=True)
        col.label(text="Delete", icon='TRASH')
        col.operator("mesh.delete", text="&A Vertices").type          = 'VERT'
        col.operator("mesh.delete", text="&W Edges").type             = 'EDGE'
        col.operator("mesh.delete", text="&D Faces").type             = 'FACE'
        col.operator("mesh.delete", text="&X Only Faces+Edges").type  = 'EDGE_FACE'
        col.operator("mesh.delete", text="Only Faces").type           = 'ONLY_FACE'
        
        layout.separator()
        
        # --- DISSOLVE ---
        col = layout.column(align=True)
        col.label(text="Dissolve", icon='MOD_SMOOTH')
        col.operator("mesh.dissolve_verts", text="&Q Vertices")
        col.operator("mesh.dissolve_edges", text="&S Edges")
        col.operator("mesh.dissolve_faces", text="&E Faces")
        col.operator("mesh.edge_collapse",  text="&C Collapse")
        col.operator("mesh.dissolve_limited", text="&R Limited Dissolve")

        layout.separator()

        # --- MERGE ---
        col = layout.column(align=True)
        col.label(text="Merge", icon='AUTOMERGE_ON')
        col.operator("mesh.merge", text="&V Center").type    = 'CENTER'
        col.operator("mesh.merge", text="At Cursor").type    = 'CURSOR'
        col.operator("mesh.merge", text="Collapse").type     = 'COLLAPSE'
        col.operator("mesh.remove_doubles", text="By Distance")

        layout.separator()

        # --- SEPARATE ---
        col = layout.column(align=True)
        col.label(text="Separate", icon='UNLINKED')
        col.operator("mesh.separate", text="Selection").type   = 'SELECTED'
        col.operator("mesh.separate", text="By Loose Parts").type  = 'LOOSE'
        col.operator("mesh.separate", text="By Material").type    = 'MATERIAL'

        layout.separator()

        # --- SPLIT ---
        col = layout.column(align=True)
        col.label(text="Split", icon='MESH_PLANE')
        col.operator("mesh.split", text="Selection")
        col.operator("mesh.edge_split", text="By Edges").type       = 'EDGE'
        col.operator("mesh.edge_split", text="By Vertices").type    = 'VERT'

        layout.separator()

        # --- REXTOOLS ---
        col = layout.column(align=True)
        col.label(text="RexTools Extras", icon='RESTRICT_SELECT_OFF')
        col.operator("rextools3.delete_linked_ex", text="Delete Linked")
        col.operator("rextools3.checker_dissolve", text="Checker Dissolve")
        col.operator("rextools3.loop_dissolve_ex", text="Loop Dissolve")
        col.operator("rextools3.fill_loop_inner_region", text="Fill Loop Region")

        # NW, NE, SW, SE left empty

def register():
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.get('3D View')
    if km:
        kmi = km.keymap_items.new(
            'rextools3.quick_delete_modal', 'X', 'PRESS',
        )
        addon_keymaps.append((km, kmi))

def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
