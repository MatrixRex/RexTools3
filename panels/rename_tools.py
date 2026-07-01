import bpy
from ..ui import utils


class RexTools3RenameToolsPanel(bpy.types.Panel):
    bl_label = "Rename Tools"
    bl_idname = "VIEW3D_PT_rextools3_rename_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'  # sidebar
    bl_category = "RexTools3"  # tab name
    
    @classmethod
    def poll(cls, context):
        try:
            addon_name = ".".join(__package__.split(".")[:3]) if __package__ and __package__.startswith("bl_ext.") else (__package__.partition('.')[0] if __package__ else "RexTools3")
            prefs = context.preferences.addons[addon_name].preferences
            if not prefs.enable_rename_tools:
                return False
        except Exception:
            pass
        return context.mode == 'OBJECT'
    
    def draw(self, context):
        layout = self.layout
        
        addon_name = ".".join(__package__.split(".")[:3]) if __package__ and __package__.startswith("bl_ext.") else (__package__.partition('.')[0] if __package__ else "RexTools3")
        try:
            prefs = context.preferences.addons[addon_name].preferences
        except Exception:
            prefs = None
            
        # 1. Bone Batch Rename Section (Armature only)
        active_obj = context.active_object
        if (not prefs or prefs.enable_tool_bone_batch_rename) and active_obj and active_obj.type == 'ARMATURE':
            bone_props = context.scene.bone_rename_props
            
            bone_box = layout.box()
            bone_row = bone_box.row()
            bone_row.prop(bone_props, "show_in_panel",
                          icon='TRIA_DOWN' if bone_props.show_in_panel else 'TRIA_RIGHT',
                          text="Bone Batch Rename",
                          emboss=False)
            
            if bone_props.show_in_panel:
                col_bone = bone_box.column(align=True)
                col_bone.label(text=f"Armature: {active_obj.name}", icon='ARMATURE_DATA')
                col_bone.label(text=f"Bones: {len(active_obj.data.bones)}")
                
                col_bone.separator()
                
                has_find_replace = bool(bone_props.find_text)
                has_prefix_suffix = bool(bone_props.prefix_text or bone_props.suffix_text)
                
                col_bone.label(text="Find & Replace:")
                col_fr = col_bone.column(align=True)
                col_fr.prop(bone_props, "find_text")
                col_fr.prop(bone_props, "replace_text")
                
                col_bone.separator()
                
                col_bone.label(text="Prefix & Suffix:")
                col_ps = col_bone.column(align=True)
                col_ps.prop(bone_props, "prefix_text")
                col_ps.prop(bone_props, "suffix_text")
                
                if has_find_replace and has_prefix_suffix:
                    col_ps.separator()
                    col_ps.prop(bone_props, "apply_prefix_suffix_to_matches_only")
                    
                col_bone.separator()
                
                if has_find_replace or has_prefix_suffix:
                    preview_box = col_bone.box()
                    preview_box.label(text="Preview:", icon='ZOOM_IN')
                    preview_count = 0
                    
                    for bone in active_obj.data.bones:
                        old_name = bone.name
                        new_name = old_name
                        should_show = False
                        found_match = False
                        
                        if has_find_replace and bone_props.find_text in old_name:
                            new_name = new_name.replace(bone_props.find_text, bone_props.replace_text)
                            should_show = True
                            found_match = True
                            
                        if has_prefix_suffix:
                            should_apply = bone_props.apply_prefix_suffix_to_matches_only and found_match or not bone_props.apply_prefix_suffix_to_matches_only
                            if should_apply:
                                if bone_props.prefix_text:
                                    new_name = bone_props.prefix_text + new_name
                                if bone_props.suffix_text:
                                    new_name = new_name + bone_props.suffix_text
                                should_show = True
                                
                        if should_show and new_name != old_name:
                            preview_count += 1
                            if preview_count <= 5:
                                row_p = preview_box.row()
                                row_p.scale_y = 0.8
                                row_p.label(text=f"{old_name} → {new_name}", icon='BONE_DATA')
                                
                    if preview_count > 5:
                        preview_box.label(text=f"... and {preview_count - 5} more", icon='THREE_DOTS')
                    elif preview_count == 0:
                        msg = "No matches found" if has_find_replace else "Will add prefix/suffix to all bones"
                        preview_box.label(text=msg, icon='INFO')
                        
                col_bone.separator()
                
                btn_row = col_bone.row()
                btn_row.scale_y = 1.5
                btn_row.enabled = has_find_replace or has_prefix_suffix
                btn_row.operator("armature.batch_rename_bones", icon='FILE_REFRESH')
                
                col_bone.separator()
                
                info_box = col_bone.box()
                info_box.label(text="Info:", icon='INFO')
                col_info = info_box.column(align=True)
                col_info.scale_y = 0.8
                col_info.label(text="• Vertex groups will be automatically updated")
                col_info.label(text="• Make sure to be in Object mode")
            
            layout.separator()
            
        # 2. Mesh High/Low Rename Section
        if not prefs or prefs.enable_tool_mesh_highlow_rename:
            props = context.scene.highlow_renamer_props
            selected_meshes = [obj for obj in context.selected_objects if obj.type == 'MESH']
            
            mesh_box = layout.box()
            mesh_row = mesh_box.row()
            mesh_row.prop(props, "show_in_panel",
                          icon='TRIA_DOWN' if props.show_in_panel else 'TRIA_RIGHT',
                          text="Mesh High/Low Rename",
                          emboss=False)
                          
            if props.show_in_panel:
                col_mesh = mesh_box.column(align=True)
                
                if len(selected_meshes) == 1:
                    col_mesh.label(text="1 selected, select another", icon='INFO')
                elif len(selected_meshes) != 2:
                    col_mesh.label(text="Please select two mesh objects", icon='ERROR')
                else:
                    col_mesh.label(text="Selected Objects:")
                    depsgraph = context.evaluated_depsgraph_get()
                    for obj in selected_meshes:
                        obj_eval = obj.evaluated_get(depsgraph)
                        vertex_count = len(obj_eval.data.vertices)
                        col_mesh.label(text=f"{obj.name} ({vertex_count} verts)", icon='MESH_DATA')
                        
                    col_mesh.separator()
                    row = col_mesh.row(align=True)
                    row.prop(props, "obj_name")
                    row.operator("mesh.auto_rename_high_low_detect", text="", icon='EYEDROPPER')
                    row.operator("mesh.auto_rename_high_low_pick_collection", text="", icon='OUTLINER_COLLECTION')
                    op = row.operator("wm.context_set_string", text="", icon='X')
                    op.data_path = "scene.highlow_renamer_props.obj_name"
                    op.value = ""
                    
                    col_mesh.prop(props, "high_prefix")
                    col_mesh.prop(props, "low_prefix")
                    
                    col_mesh.separator()
                    utils.draw_call_to_action(col_mesh, "mesh.auto_rename_high_low", "Auto Rename High/Low", icon='FILE_REFRESH', type='PRIMARY')


