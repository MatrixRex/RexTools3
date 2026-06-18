import bpy
from bpy.props import BoolProperty, EnumProperty

def update_keymap_active_states(self, context):
    try:
        from .operators import smart_join, rex_shading_pie, edit_delete_ops, context_aware_select
        
        if hasattr(smart_join, 'addon_keymaps'):
            for km, kmi in smart_join.addon_keymaps:
                kmi.active = self.enable_smart_join
                
        if hasattr(rex_shading_pie, 'addon_keymaps'):
            for km, kmi in rex_shading_pie.addon_keymaps:
                kmi.active = self.enable_shading_pie
                
        if hasattr(edit_delete_ops, 'addon_keymaps'):
            for km, kmi in edit_delete_ops.addon_keymaps:
                kmi.active = self.enable_quick_delete
                
        if hasattr(context_aware_select, 'addon_keymaps'):
            for km, kmi in context_aware_select.addon_keymaps:
                kmi.active = self.enable_context_select
    except Exception as e:
        print("[RexTools3] Error updating keymap active states:", e)

def update_panel_redraw(self, context):
    try:
        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if area.type in {'VIEW_3D', 'NODE_EDITOR'}:
                    area.tag_redraw()
    except Exception as e:
        print("[RexTools3] Error tagging redraw:", e)



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
        update=update_panel_redraw,
    )
    enable_cleanup_tools: BoolProperty(
        name="Cleanup Tools",
        description="Enable/Disable the Cleanup Tools panel",
        default=True,
        update=update_panel_redraw,
    )
    enable_pbr_tools: BoolProperty(
        name="EasyPBR",
        description="Enable/Disable the EasyPBR panel",
        default=True,
        update=update_panel_redraw,
    )
    enable_batch_material: BoolProperty(
        name="Material Tools",
        description="Enable/Disable the Material Tools panel",
        default=True,
        update=update_panel_redraw,
    )
    enable_node_helper: BoolProperty(
        name="Node Helper & Layout",
        description="Enable/Disable the Node Helper and Node Layout panels",
        default=True,
        update=update_panel_redraw,
    )
    enable_object_tools: BoolProperty(
        name="Object Tools",
        description="Enable/Disable the Object Tools panel",
        default=True,
        update=update_panel_redraw,
    )
    enable_edit_tools: BoolProperty(
        name="Edit Tools",
        description="Enable/Disable the Edit Tools panel",
        default=True,
        update=update_panel_redraw,
    )
    enable_rexport: BoolProperty(
        name="RExport",
        description="Enable/Disable RExport and its sub-components",
        default=True,
        update=update_panel_redraw,
    )
    enable_quick_asset_export: BoolProperty(
        name="Quick Asset Export",
        description="Enable/Disable the Quick Asset Export panel",
        default=True,
        update=update_panel_redraw,
    )
    enable_pose_tools: BoolProperty(
        name="Pose Tools",
        description="Enable/Disable the Pose Tools panel",
        default=True,
        update=update_panel_redraw,
    )

    enable_chain_constraints: BoolProperty(
        name="Chain Constraints Adder",
        description="Enable/Disable the Chain Constraints Adder panel",
        default=True,
        update=update_panel_redraw,
    )
    enable_sculpt_tools: BoolProperty(
        name="Sculpt Tools",
        description="Enable/Disable the Sculpt Tools panel",
        default=True,
        update=update_panel_redraw,
    )
    enable_uv_tools: BoolProperty(
        name="UV Tools",
        description="Enable/Disable the UV Tools panel",
        default=True,
        update=update_panel_redraw,
    )
    enable_uv_mesh_tools: BoolProperty(
        name="UV Mesh Tools",
        description="Enable/Disable the UV Mesh Tools panel",
        default=True,
        update=update_panel_redraw,
    )
    enable_weight_tools: BoolProperty(
        name="Weight Tools",
        description="Enable/Disable the Weight Tools panel",
        default=True,
        update=update_panel_redraw,
    )
    enable_rename_tools: BoolProperty(
        name="Rename Tools",
        description="Enable/Disable the Rename Tools panel",
        default=True,
        update=update_panel_redraw,
    )

    # Common Tools Sub-tools
    enable_tool_open_folder: BoolProperty(name="Open Folder", default=True, update=update_panel_redraw)
    enable_tool_extract_textures: BoolProperty(name="Extract Textures", default=True, update=update_panel_redraw)
    enable_tool_purge_orphans: BoolProperty(name="Purge Orphans", default=True, update=update_panel_redraw)
    enable_tool_replace_materials: BoolProperty(name="Replace Materials", default=True, update=update_panel_redraw)
    enable_tool_batch_texture_assign: BoolProperty(name="Batch Texture Assign", default=True, update=update_panel_redraw)
    enable_tool_bone_batch_rename: BoolProperty(name="Bone Batch Rename", default=True, update=update_panel_redraw)
    enable_tool_mesh_highlow_rename: BoolProperty(name="Mesh High/Low Rename", default=True, update=update_panel_redraw)

    # Cleanup Tools Sub-tools
    enable_tool_clean_objects: BoolProperty(name="Clean Objects", default=True, update=update_panel_redraw)
    enable_tool_checker_dissolve: BoolProperty(name="Checker Dissolve", default=True, update=update_panel_redraw)
    enable_tool_clear_seams: BoolProperty(name="Clear Seams", default=True, update=update_panel_redraw)
    enable_tool_clean_modifiers: BoolProperty(name="Clean Modifiers", default=True, update=update_panel_redraw)
    enable_tool_missing_textures: BoolProperty(name="Missing Textures Scanner", default=True, update=update_panel_redraw)

    # Edit Tools Sub-tools
    enable_tool_angle_loop_select: BoolProperty(name="Angle Loop Select", default=True, update=update_panel_redraw)
    enable_tool_subdivide_tube: BoolProperty(name="Subdivide Tube", default=True, update=update_panel_redraw)

    # Pose Tools Sub-tools
    enable_tool_pose_init_weight: BoolProperty(name="Init Weight Paint", default=True, update=update_panel_redraw)
    enable_tool_setup_pose_copier: BoolProperty(name="Setup Pose Copier", default=True, update=update_panel_redraw)
    enable_tool_flipped_anim: BoolProperty(name="Flipped Anim", default=True, update=update_panel_redraw)

    # Sculpt Tools Sub-tools
    enable_tool_sculpt_navigation: BoolProperty(name="Pen Navigation", default=True, update=update_panel_redraw)
    enable_tool_sculpt_assets: BoolProperty(name="Sculpt Assets Previews", default=True, update=update_panel_redraw)

    # UV Mesh Tools Sub-tools
    enable_tool_uv_mesh_area_seam: BoolProperty(name="Area Seam", default=True, update=update_panel_redraw)
    enable_tool_uv_mesh_angle_loop_seam: BoolProperty(name="Angle Loop Seam", default=True, update=update_panel_redraw)
    enable_tool_uv_mesh_seam_island_sharp: BoolProperty(name="Seam From Island & Sharp", default=True, update=update_panel_redraw)
    enable_tool_uv_mesh_area_seam_angle: BoolProperty(name="Area Seam by Angle", default=True, update=update_panel_redraw)
    enable_tool_uv_mesh_unwrap_quad: BoolProperty(name="Live Unwrap & Quad Follow", default=True, update=update_panel_redraw)

    # Weight Tools Sub-tools
    enable_tool_weight_init_weight: BoolProperty(name="Init Weight Paint", default=True, update=update_panel_redraw)
    enable_tool_weight_xray_brush: BoolProperty(name="X-Ray Brush Toggle", default=True, update=update_panel_redraw)

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
            
            def draw_panel_category(layout, label, icon, enable_prop, sub_props=None, info_text=None):
                box = layout.box()
                hdr = box.row()
                hdr.prop(self, enable_prop, text=label, icon=icon)
                
                if getattr(self, enable_prop):
                    if info_text:
                        lines = info_text.split("\n")
                        box.label(text=lines[0], icon='INFO')
                        for line in lines[1:]:
                            box.label(text="    " + line)
                    if sub_props:
                        sub_col = box.column(align=True)
                        sub_col.separator(factor=0.5)
                        row = sub_col.row(align=True)
                        grid = row.grid_flow(columns=2, align=True)
                        for prop, name in sub_props:
                            grid.prop(self, prop, text=name)
            
            # --- Group 1: 3D Viewport Sidebar (RexTools3 Tab) ---
            box_3d = col.box()
            box_3d.label(text="3D Viewport Sidebar (RexTools3 Tab)", icon='VIEW3D')
            col_3d = box_3d.column()
            
            # Sub-group: Any Mode
            box_any = col_3d.box()
            box_any.label(text="Any Mode Tools", icon='WORLD')
            col_any = box_any.column()
            draw_panel_category(col_any, "Common Tools", 'SETTINGS', "enable_common_tools", [
                ("enable_tool_open_folder", "Open Folder"),
                ("enable_tool_purge_orphans", "Purge Orphans")
            ])
            draw_panel_category(col_any, "Material Tools", 'TEXTURE_DATA', "enable_batch_material", [
                ("enable_tool_extract_textures", "Extract Textures"),
                ("enable_tool_replace_materials", "Replace Materials"),
                ("enable_tool_batch_texture_assign", "Batch Texture Assign")
            ])
            draw_panel_category(col_any, "Quick Asset Export", 'ASSET_MANAGER', "enable_quick_asset_export")

            # Sub-group: Object Mode
            box_obj = col_3d.box()
            box_obj.label(text="Object Mode Tools", icon='OBJECT_DATA')
            col_obj = box_obj.column()
            draw_panel_category(col_obj, "Object Tools", 'OBJECT_DATA', "enable_object_tools")
            draw_panel_category(col_obj, "UV Tools", 'UV_DATA', "enable_uv_tools")
            draw_panel_category(col_obj, "Rename Tools", 'FONT_DATA', "enable_rename_tools", [
                ("enable_tool_bone_batch_rename", "Bone Batch Rename"),
                ("enable_tool_mesh_highlow_rename", "Mesh High/Low Rename")
            ])

            # Sub-group: Edit Mode
            box_edit = col_3d.box()
            box_edit.label(text="Edit Mode Tools", icon='EDITMODE_HLT')
            col_edit = box_edit.column()
            draw_panel_category(col_edit, "Edit Tools", 'EDITMODE_HLT', "enable_edit_tools", [
                ("enable_tool_angle_loop_select", "Angle Loop Select"),
                ("enable_tool_subdivide_tube", "Subdivide Tube")
            ])
            draw_panel_category(col_edit, "UV Mesh Tools", 'UV', "enable_uv_mesh_tools", [
                ("enable_tool_uv_mesh_area_seam", "Area Seam"),
                ("enable_tool_uv_mesh_angle_loop_seam", "Angle Loop Seam"),
                ("enable_tool_uv_mesh_seam_island_sharp", "Seam From Island & Sharp"),
                ("enable_tool_uv_mesh_area_seam_angle", "Area Seam by Angle"),
                ("enable_tool_uv_mesh_unwrap_quad", "Live Unwrap & Quad")
            ])

            # Sub-group: Object & Edit Mode
            box_obj_edit = col_3d.box()
            box_obj_edit.label(text="Object & Edit Mode Tools", icon='LOOP_BACK')
            col_obj_edit = box_obj_edit.column()
            draw_panel_category(col_obj_edit, "Cleanup Tools", 'BRUSH_DATA', "enable_cleanup_tools", [
                ("enable_tool_clean_objects", "Clean Objects"),
                ("enable_tool_checker_dissolve", "Checker Dissolve"),
                ("enable_tool_clear_seams", "Clear Seams"),
                ("enable_tool_clean_modifiers", "Clean Modifiers"),
                ("enable_tool_missing_textures", "Missing Textures Scanner")
            ])

            # Sub-group: Pose Mode
            box_pose = col_3d.box()
            box_pose.label(text="Pose Mode Tools", icon='POSE_HLT')
            col_pose = box_pose.column()
            draw_panel_category(col_pose, "Pose Tools", 'POSE_HLT', "enable_pose_tools", [
                ("enable_tool_pose_init_weight", "Init Weight Paint"),
                ("enable_tool_setup_pose_copier", "Setup Pose Copier"),
                ("enable_tool_flipped_anim", "Flipped Anim")
            ])
            draw_panel_category(col_pose, "Chain Constraints Adder", 'CONSTRAINT_BONE', "enable_chain_constraints")

            # Sub-group: Paint & Sculpt Modes
            box_paint = col_3d.box()
            box_paint.label(text="Paint & Sculpt Mode Tools", icon='SCULPTMODE_HLT')
            col_paint = box_paint.column()
            draw_panel_category(col_paint, "Sculpt Tools", 'SCULPTMODE_HLT', "enable_sculpt_tools", [
                ("enable_tool_sculpt_navigation", "Pen Navigation"),
                ("enable_tool_sculpt_assets", "Sculpt Assets Previews")
            ])
            draw_panel_category(col_paint, "Weight Tools", 'WPAINT_HLT', "enable_weight_tools", [
                ("enable_tool_weight_init_weight", "Init Weight Paint"),
                ("enable_tool_weight_xray_brush", "X-Ray Brush Toggle")
            ])
            
            # --- Group 2: RExport Panel & Tools ---
            col.separator()
            box_rexport = col.box()
            box_rexport.label(text="RExport Panel & Tools", icon='EXPORT')
            col_rexport = box_rexport.column()
            
            draw_panel_category(col_rexport, "RExport", 'EXPORT', "enable_rexport",
                                info_text="Locations:\n1. 3D View > side panel > RExport\n2. TopBar header > RExport\n3. Collection properties > RExport\n4. Scene properties > RExport")
            
            # --- Group 3: EasyPBR Panel & Tools ---
            col.separator()
            box_pbr = col.box()
            box_pbr.label(text="EasyPBR Panel & Tools", icon='MATERIAL')
            col_pbr = box_pbr.column()
            
            draw_panel_category(col_pbr, "EasyPBR", 'MATERIAL', "enable_pbr_tools",
                                info_text="Location:\n1. Properties Editor > Material Properties > Easy PBR")
            
            # --- Group 4: Other Editors & Windows ---
            col.separator()
            box_other = col.box()
            box_other.label(text="Other Editors & Windows", icon='WINDOW')
            col_other = box_other.column()
            
            draw_panel_category(col_other, "Node Helper & Layout", 'NODETREE', "enable_node_helper",
                                info_text="Location:\n1. Shader Editor > Sidebar > RexTools3 Tab")
            
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
            
            from .operators import rex_shading_pie

            pie_tools = [
                (self.enable_shading_pie, "enable_shading_pie", rex_shading_pie, "Rex Shading & View Pies (3D View: Z / W)"),
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
