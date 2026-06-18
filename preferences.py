import bpy
from bpy.props import BoolProperty, EnumProperty

def update_keymap_active_states(self, context):
    try:
        from .operators import smart_join, rex_shading_pie, pie_test, edit_delete_ops, context_aware_select
        
        if hasattr(smart_join, 'addon_keymaps'):
            for km, kmi in smart_join.addon_keymaps:
                kmi.active = self.enable_smart_join
                
        if hasattr(rex_shading_pie, 'addon_keymaps'):
            for km, kmi in rex_shading_pie.addon_keymaps:
                kmi.active = self.enable_shading_pie
                
        if hasattr(pie_test, 'addon_keymaps'):
            for km, kmi in pie_test.addon_keymaps:
                kmi.active = self.enable_pie_test
                
        if hasattr(edit_delete_ops, 'addon_keymaps'):
            for km, kmi in edit_delete_ops.addon_keymaps:
                kmi.active = self.enable_quick_delete
                
        if hasattr(context_aware_select, 'addon_keymaps'):
            for km, kmi in context_aware_select.addon_keymaps:
                kmi.active = self.enable_context_select
    except Exception as e:
        print("[RexTools3] Error updating keymap active states:", e)


class RexTools3Preferences(bpy.types.AddonPreferences):
    bl_idname = __package__ or "RexTools3"

    active_tab: EnumProperty(
        name="Tab",
        items=[
            ('TOOLS', "Tools & Panels", "Enable or disable tool panels in the sidebar", 'SETTINGS', 0),
            ('KEYMAP', "Keyboard Shortcuts", "Manage shortcut keys for tools", 'KEY_SHIFT', 1),
        ],
        default='TOOLS',
    )

    # Tool Category Toggles (Panels)
    enable_common_tools: BoolProperty(
        name="Common Tools",
        description="Enable/Disable the Common Tools panel",
        default=True,
    )
    enable_cleanup_tools: BoolProperty(
        name="Cleanup Tools",
        description="Enable/Disable the Cleanup Tools panel",
        default=True,
    )
    enable_pbr_tools: BoolProperty(
        name="PBR Material Tools",
        description="Enable/Disable the PBR Material Tools panel",
        default=True,
    )
    enable_batch_material: BoolProperty(
        name="Batch Material Panel",
        description="Enable/Disable the Batch Material Panel",
        default=True,
    )
    enable_node_helper: BoolProperty(
        name="Node Helper & Layout",
        description="Enable/Disable the Node Helper and Node Layout panels",
        default=True,
    )
    enable_object_tools: BoolProperty(
        name="Object Tools",
        description="Enable/Disable the Object Tools panel",
        default=True,
    )
    enable_edit_tools: BoolProperty(
        name="Edit Tools",
        description="Enable/Disable the Edit Tools panel",
        default=True,
    )
    enable_export_panel: BoolProperty(
        name="Export Manager",
        description="Enable/Disable the Export Manager and its topbar menu",
        default=True,
    )
    enable_quick_asset_export: BoolProperty(
        name="Quick Asset Export",
        description="Enable/Disable the Quick Asset Export panel",
        default=True,
    )
    enable_pose_tools: BoolProperty(
        name="Pose Tools",
        description="Enable/Disable the Pose Tools panel",
        default=True,
    )
    enable_rig_tools: BoolProperty(
        name="Rigging Tools (Batch Rename)",
        description="Enable/Disable the Bone Batch Rename panel",
        default=True,
    )
    enable_chain_constraints: BoolProperty(
        name="Chain Constraints Adder",
        description="Enable/Disable the Chain Constraints Adder panel",
        default=True,
    )
    enable_sculpt_tools: BoolProperty(
        name="Sculpt Tools",
        description="Enable/Disable the Sculpt Tools panel",
        default=True,
    )
    enable_uv_tools: BoolProperty(
        name="UV Tools",
        description="Enable/Disable the UV Tools panel",
        default=True,
    )
    enable_uv_mesh_tools: BoolProperty(
        name="UV Mesh Tools",
        description="Enable/Disable the UV Mesh Tools panel",
        default=True,
    )
    enable_weight_tools: BoolProperty(
        name="Weight Tools",
        description="Enable/Disable the Weight Tools panel",
        default=True,
    )
    enable_rename_tools: BoolProperty(
        name="Rename Tools",
        description="Enable/Disable the Rename Tools panel",
        default=True,
    )

    # Keymapped Operators Toggles
    enable_smart_join: BoolProperty(
        name="Smart Join",
        description="Enable/Disable Smart Join operator and shortcut",
        default=True,
        update=update_keymap_active_states,
    )
    enable_shading_pie: BoolProperty(
        name="Rex Shading & View Pies",
        description="Enable/Disable Shading and View pie menus and shortcuts",
        default=True,
        update=update_keymap_active_states,
    )
    enable_pie_test: BoolProperty(
        name="Pie Test",
        description="Enable/Disable Pie Test menu and shortcut",
        default=True,
        update=update_keymap_active_states,
    )
    enable_quick_delete: BoolProperty(
        name="Quick Delete Modal",
        description="Enable/Disable Quick Delete modal operator and shortcut",
        default=True,
        update=update_keymap_active_states,
    )
    enable_context_select: BoolProperty(
        name="Context Aware Select",
        description="Enable/Disable Context Aware Select operator and double-click shortcut",
        default=True,
        update=update_keymap_active_states,
    )

    def draw(self, context):
        layout = self.layout
        
        # Draw Tab Selector
        row = layout.row(align=True)
        row.prop(self, "active_tab", expand=True)
        layout.separator()

        if self.active_tab == 'TOOLS':
            # --- Panels Enable/Disable Section ---
            col = layout.column(align=True)
            col.label(text="Tool Panels Visibility", icon='PREFERENCES')
            
            box = col.box()
            grid = box.grid_flow(columns=2, align=True)
            
            grid.prop(self, "enable_common_tools")
            grid.prop(self, "enable_cleanup_tools")
            grid.prop(self, "enable_pbr_tools")
            grid.prop(self, "enable_batch_material")
            grid.prop(self, "enable_node_helper")
            grid.prop(self, "enable_object_tools")
            grid.prop(self, "enable_edit_tools")
            grid.prop(self, "enable_export_panel")
            grid.prop(self, "enable_quick_asset_export")
            grid.prop(self, "enable_pose_tools")
            grid.prop(self, "enable_rig_tools")
            grid.prop(self, "enable_chain_constraints")
            grid.prop(self, "enable_sculpt_tools")
            grid.prop(self, "enable_uv_tools")
            grid.prop(self, "enable_uv_mesh_tools")
            grid.prop(self, "enable_weight_tools")
            grid.prop(self, "enable_rename_tools")
            
        elif self.active_tab == 'KEYMAP':
            # --- Keyboard Shortcuts Management Section ---
            col = layout.column()
            col.label(text="Shortcut Keys Configuration", icon='KEY_SHIFT')
            
            from .operators import smart_join, rex_shading_pie, pie_test, edit_delete_ops, context_aware_select

            shortcut_tools = [
                (self.enable_smart_join, "enable_smart_join", smart_join, "Smart Join (Object Mode: Ctrl+J)"),
                (self.enable_shading_pie, "enable_shading_pie", rex_shading_pie, "Rex Shading & View Pies (3D View: Z / W)"),
                (self.enable_pie_test, "enable_pie_test", pie_test, "Pie Test (3D View: Shift+X)"),
                (self.enable_quick_delete, "enable_quick_delete", edit_delete_ops, "Quick Delete Modal (3D View: X)"),
                (self.enable_context_select, "enable_context_select", context_aware_select, "Context Aware Select (Mesh/Curve: Double Click)"),
            ]

            for enabled, toggle_prop_name, module, title in shortcut_tools:
                box = col.box()
                
                # Header row with enable/disable toggle
                hdr = box.row()
                hdr.prop(self, toggle_prop_name, text=title)
                
                if enabled and hasattr(module, 'addon_keymaps'):
                    keymap_col = box.column(align=True)
                    for km, kmi in module.addon_keymaps:
                        row = keymap_col.row(align=True)
                        row.prop(kmi, "active", text="")
                        row.prop(kmi, "map_type", text="")
                        row.prop(kmi, "type", text="", full_event=True)
                        
                        if kmi.map_type == 'KEYBOARD':
                            row.prop(kmi, "ctrl", text="Ctrl", toggle=True)
                            row.prop(kmi, "shift", text="Shift", toggle=True)
                            row.prop(kmi, "alt", text="Alt", toggle=True)
                            row.prop(kmi, "oskey", text="Cmd", toggle=True)
