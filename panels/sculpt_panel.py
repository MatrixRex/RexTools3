import bpy

class RexTools3SculptToolsPanel(bpy.types.Panel):
    bl_label = "Sculpt Tools"
    bl_idname = "VIEW3D_PT_rextools3_sculpt_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "RexTools3"
    
    @classmethod
    def poll(cls, context):
        try:
            addon_name = ".".join(__package__.split(".")[:3]) if __package__ and __package__.startswith("bl_ext.") else (__package__.partition('.')[0] if __package__ else "RexTools3")
            prefs = context.preferences.addons[addon_name].preferences
            if not prefs.enable_sculpt_tools:
                return False
        except Exception:
            pass
        return context.mode == 'SCULPT'
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.sculpt_tools_props

        addon_name = ".".join(__package__.split(".")[:3]) if __package__ and __package__.startswith("bl_ext.") else (__package__.partition('.')[0] if __package__ else "RexTools3")
        try:
            prefs = context.preferences.addons[addon_name].preferences
        except Exception:
            prefs = None

        # ── Pen Navigation ────────────────────────────────────────────────────
        if not prefs or prefs.enable_tool_sculpt_navigation:
            box = layout.box()
            box.label(text="Navigation", icon='MOUSE_LMB_DRAG')
            col = box.column(align=True)
            is_on = props.pen_nav
            icon = 'CHECKBOX_HLT' if is_on else 'CHECKBOX_DEHLT'
            col.prop(props, "pen_nav", text="Pen Nav", icon=icon, toggle=True)

        # ── Sculpt Assets ─────────────────────────────────────────────────────
        if not prefs or prefs.enable_tool_sculpt_assets:
            box = layout.box()
            box.label(text="Sculpt Assets", icon='ASSET_MANAGER')
            col = box.column(align=True)
            col.operator("rextools3.batch_assign_sculpt_previews", text="Batch Assign Previews", icon='FILE_FOLDER')

