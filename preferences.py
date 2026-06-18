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
            ('PANELS', "Panel Tools", "Enable or disable sidebar panel tools", 'PREFERENCES', 0),
            ('SHORTCUTS', "Shortcut Tools", "Manage shortcut tools and their hotkeys", 'TOOL_SETTINGS', 1),
            ('PIES', "Pie Menus", "Manage pie menus and their hotkeys", 'MENU_PANEL', 2),
        ],
        default='PANELS',
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

    # Common Tools Sub-tools
    enable_tool_open_folder: BoolProperty(name="Open Folder", default=True)
    enable_tool_extract_textures: BoolProperty(name="Extract Textures", default=True)
    enable_tool_purge_orphans: BoolProperty(name="Purge Orphans", default=True)
    enable_tool_replace_materials: BoolProperty(name="Replace Materials", default=True)

    # Cleanup Tools Sub-tools
    enable_tool_clean_objects: BoolProperty(name="Clean Objects", default=True)
    enable_tool_checker_dissolve: BoolProperty(name="Checker Dissolve", default=True)
    enable_tool_clear_seams: BoolProperty(name="Clear Seams", default=True)
    enable_tool_clean_modifiers: BoolProperty(name="Clean Modifiers", default=True)
    enable_tool_missing_textures: BoolProperty(name="Missing Textures Scanner", default=True)

    # PBR Tools Sub-tools
    enable_tool_pbr_loader: BoolProperty(name="Texture Auto Loader", default=True)
    enable_tool_pbr_utils: BoolProperty(name="Texture Utilities", default=True)
    enable_tool_pbr_viewport: BoolProperty(name="Viewport Color", default=True)

    # Edit Tools Sub-tools
    enable_tool_angle_loop_select: BoolProperty(name="Angle Loop Select", default=True)
    enable_tool_subdivide_tube: BoolProperty(name="Subdivide Tube", default=True)

    # Pose Tools Sub-tools
    enable_tool_pose_init_weight: BoolProperty(name="Init Weight Paint", default=True)
    enable_tool_setup_pose_copier: BoolProperty(name="Setup Pose Copier", default=True)
    enable_tool_flipped_anim: BoolProperty(name="Flipped Anim", default=True)

    # Sculpt Tools Sub-tools
    enable_tool_sculpt_navigation: BoolProperty(name="Pen Navigation", default=True)
    enable_tool_sculpt_assets: BoolProperty(name="Sculpt Assets Previews", default=True)

    # UV Tools Sub-tools
    enable_tool_uv_seam_from_sharp: BoolProperty(name="Seam From Sharp", default=True)

    # UV Mesh Tools Sub-tools
    enable_tool_uv_mesh_area_seam: BoolProperty(name="Area Seam", default=True)
    enable_tool_uv_mesh_angle_loop_seam: BoolProperty(name="Angle Loop Seam", default=True)
    enable_tool_uv_mesh_seam_island_sharp: BoolProperty(name="Seam From Island & Sharp", default=True)
    enable_tool_uv_mesh_area_seam_angle: BoolProperty(name="Area Seam by Angle", default=True)
    enable_tool_uv_mesh_unwrap_quad: BoolProperty(name="Live Unwrap & Quad Follow", default=True)

    # Weight Tools Sub-tools
    enable_tool_weight_init_weight: BoolProperty(name="Init Weight Paint", default=True)
    enable_tool_weight_xray_brush: BoolProperty(name="X-Ray Brush Toggle", default=True)

    # Rename Tools Sub-tools
    enable_tool_rename_high_low: BoolProperty(name="Auto Rename High/Low", default=True)

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

        if self.active_tab == 'PANELS':
            col = layout.column()
            col.label(text="Sidebar Panel Tools Visibility", icon='PREFERENCES')
            
            def draw_panel_category(layout, label, icon, enable_prop, sub_props=None):
                box = layout.box()
                hdr = box.row()
                hdr.prop(self, enable_prop, text=label, icon=icon)
                
                if getattr(self, enable_prop) and sub_props:
                    sub_col = box.column(align=True)
                    sub_col.separator(factor=0.5)
                    row = sub_col.row(align=True)
                    grid = row.grid_flow(columns=2, align=True)
                    for prop, name in sub_props:
                        grid.prop(self, prop, text=name)
            
            draw_panel_category(col, "Common Tools", 'SETTINGS', "enable_common_tools", [
                ("enable_tool_open_folder", "Open Folder"),
                ("enable_tool_extract_textures", "Extract Textures"),
                ("enable_tool_purge_orphans", "Purge Orphans"),
                ("enable_tool_replace_materials", "Replace Materials")
            ])
            
            draw_panel_category(col, "Cleanup Tools", 'BRUSH_DATA', "enable_cleanup_tools", [
                ("enable_tool_clean_objects", "Clean Objects"),
                ("enable_tool_checker_dissolve", "Checker Dissolve"),
                ("enable_tool_clear_seams", "Clear Seams"),
                ("enable_tool_clean_modifiers", "Clean Modifiers"),
                ("enable_tool_missing_textures", "Missing Textures Scanner")
            ])
            
            draw_panel_category(col, "PBR Material Tools", 'MATERIAL', "enable_pbr_tools", [
                ("enable_tool_pbr_loader", "Texture Auto Loader"),
                ("enable_tool_pbr_utils", "Texture Utilities"),
                ("enable_tool_pbr_viewport", "Viewport Color")
            ])
            
            draw_panel_category(col, "Batch Material Panel", 'TEXTURE_DATA', "enable_batch_material")
            
            draw_panel_category(col, "Node Helper & Layout", 'NODETREE', "enable_node_helper")
            
            draw_panel_category(col, "Object Tools", 'OBJECT_DATA', "enable_object_tools")
            
            draw_panel_category(col, "Edit Tools", 'EDITMODE_HLT', "enable_edit_tools", [
                ("enable_tool_angle_loop_select", "Angle Loop Select"),
                ("enable_tool_subdivide_tube", "Subdivide Tube")
            ])
            
            draw_panel_category(col, "Export Manager", 'EXPORT', "enable_export_panel")
            
            draw_panel_category(col, "Quick Asset Export", 'ASSET_MANAGER', "enable_quick_asset_export")
            
            draw_panel_category(col, "Pose Tools", 'POSE_HLT', "enable_pose_tools", [
                ("enable_tool_pose_init_weight", "Init Weight Paint"),
                ("enable_tool_setup_pose_copier", "Setup Pose Copier"),
                ("enable_tool_flipped_anim", "Flipped Anim")
            ])
            
            draw_panel_category(col, "Rigging Tools (Batch Rename)", 'ARMATURE_DATA', "enable_rig_tools")
            
            draw_panel_category(col, "Chain Constraints Adder", 'CONSTRAINT_BONE', "enable_chain_constraints")
            
            draw_panel_category(col, "Sculpt Tools", 'SCULPTMODE_HLT', "enable_sculpt_tools", [
                ("enable_tool_sculpt_navigation", "Pen Navigation"),
                ("enable_tool_sculpt_assets", "Sculpt Assets Previews")
            ])
            
            draw_panel_category(col, "UV Tools", 'UV_DATA', "enable_uv_tools", [
                ("enable_tool_uv_seam_from_sharp", "Seam From Sharp")
            ])
            
            draw_panel_category(col, "UV Mesh Tools", 'UV', "enable_uv_mesh_tools", [
                ("enable_tool_uv_mesh_area_seam", "Area Seam"),
                ("enable_tool_uv_mesh_angle_loop_seam", "Angle Loop Seam"),
                ("enable_tool_uv_mesh_seam_island_sharp", "Seam From Island & Sharp"),
                ("enable_tool_uv_mesh_area_seam_angle", "Area Seam by Angle"),
                ("enable_tool_uv_mesh_unwrap_quad", "Live Unwrap & Quad")
            ])
            
            draw_panel_category(col, "Weight Tools", 'WPAINT_HLT', "enable_weight_tools", [
                ("enable_tool_weight_init_weight", "Init Weight Paint"),
                ("enable_tool_weight_xray_brush", "X-Ray Brush Toggle")
            ])
            
            draw_panel_category(col, "Rename Tools", 'FONT_DATA', "enable_rename_tools", [
                ("enable_tool_rename_high_low", "Auto Rename High/Low")
            ])
            
        elif self.active_tab == 'SHORTCUTS':
            # --- Shortcut Tools Section ---
            col = layout.column()
            col.label(text="Shortcut Tools Configuration", icon='TOOL_SETTINGS')
            
            from .operators import smart_join, edit_delete_ops, context_aware_select

            shortcut_tools = [
                (self.enable_smart_join, "enable_smart_join", smart_join, "Smart Join (Object Mode: Ctrl+J)"),
                (self.enable_quick_delete, "enable_quick_delete", edit_delete_ops, "Quick Delete Modal (3D View: X)"),
                (self.enable_context_select, "enable_context_select", context_aware_select, "Context Aware Select (Mesh/Curve: Double Click)"),
            ]

            wm = context.window_manager
            kc = wm.keyconfigs.user

            for enabled, toggle_prop_name, module, title in shortcut_tools:
                box = col.box()
                
                # Header row with enable/disable toggle
                hdr = box.row()
                hdr.prop(self, toggle_prop_name, text=title)
                
                if enabled and hasattr(module, 'addon_keymaps'):
                    keymap_col = box.column(align=True)
                    import rna_keymap_ui
                    for km, kmi in module.addon_keymaps:
                        keymap_col.context_pointer_set("keymap", km)
                        rna_keymap_ui.draw_kmi(None, kc, km, kmi, keymap_col, 0)

        elif self.active_tab == 'PIES':
            # --- Pie Menus Section ---
            col = layout.column()
            col.label(text="Pie Menus Configuration", icon='MENU_PANEL')
            
            from .operators import rex_shading_pie, pie_test

            pie_tools = [
                (self.enable_shading_pie, "enable_shading_pie", rex_shading_pie, "Rex Shading & View Pies (3D View: Z / W)"),
                (self.enable_pie_test, "enable_pie_test", pie_test, "Pie Test (3D View: Shift+X)"),
            ]

            wm = context.window_manager
            kc = wm.keyconfigs.user

            for enabled, toggle_prop_name, module, title in pie_tools:
                box = col.box()
                
                # Header row with enable/disable toggle
                hdr = box.row()
                hdr.prop(self, toggle_prop_name, text=title)
                
                if enabled and hasattr(module, 'addon_keymaps'):
                    keymap_col = box.column(align=True)
                    import rna_keymap_ui
                    for km, kmi in module.addon_keymaps:
                        keymap_col.context_pointer_set("keymap", km)
                        rna_keymap_ui.draw_kmi(None, kc, km, kmi, keymap_col, 0)
