import bpy
import os
from bpy.types import Operator
from bpy.props import StringProperty

def has_any_override(overrides):
    """Check if any individual override flag is enabled."""
    if not overrides: return False
    flags = [
        'override_path', 'override_texture_copy_path', 'override_format', 'override_preset', 
        'override_remove_armature_root', 'override_rename_armature', 
        'override_reset_transform', 'override_pre_rotation', 'override_pre_scale',
        'override_single_mesh'
    ]
    return any(getattr(overrides, f, False) for f in flags)

def get_resolved_val(coll, prop_name, global_settings):
    """Find the resolved value for a property by checking the collection and its parents."""
    mapping = {
        'export_path': 'override_path',
        'texture_copy_path': 'override_texture_copy_path',
        'export_format': 'override_format',
        'export_preset': 'override_preset',
        'fbx_remove_armature_root': 'override_remove_armature_root',
        'rename_armature': 'override_rename_armature',
        'reset_transform': 'override_reset_transform',
        'pre_rotation': 'override_pre_rotation',
        'pre_scale': 'override_pre_scale',
        'single_mesh': 'override_single_mesh',
    }
    
    flag = mapping.get(prop_name)
    if not flag:
        return getattr(global_settings, prop_name)

    # 1. Check current collection
    overrides = getattr(coll, "rex_export_overrides", None)
    if overrides and getattr(overrides, flag, False):
        return getattr(overrides, prop_name)
    
    # 2. Check parents recursively
    parents = [c for c in bpy.data.collections if coll.name in c.children]
    for parent in parents:
        if parent.name == "Scene Collection" or parent == bpy.context.scene.collection:
            continue
        val = _find_in_parents(parent, prop_name, flag)
        if val is not None:
            return val
            
    # 3. Fallback to global
    return getattr(global_settings, prop_name)

def _find_in_parents(coll, prop_name, flag):
    overrides = getattr(coll, "rex_export_overrides", None)
    if overrides and getattr(overrides, flag, False):
        return getattr(overrides, prop_name)
    
    parents = [c for c in bpy.data.collections if coll.name in c.children.keys()]
    for parent in parents:
        if parent.name == "Scene Collection" or parent == bpy.context.scene.collection:
            continue
        val = _find_in_parents(parent, prop_name, flag)
        if val is not None:
            return val
    return None

def get_effective_overrides(coll, global_settings):
    """Recursively find the first active override in the collection hierarchy and resolve all properties."""
    overrides = getattr(coll, "rex_export_overrides", None)
    
    # If this collection has any override enabled, it's our "source" and we resolve all props starting here
    if has_any_override(overrides):
        from types import SimpleNamespace
        res = SimpleNamespace()
        
        props = [
            'export_path', 'texture_copy_path', 'export_format', 'export_preset', 
            'fbx_remove_armature_root', 'rename_armature', 
            'reset_transform', 'pre_rotation', 'pre_scale', 'single_mesh'
        ]
        
        for p in props:
            setattr(res, p, get_resolved_val(coll, p, global_settings))
            
        return coll, res
    
    # Otherwise, check if any parent has overrides enabled
    parents = [c for c in bpy.data.collections if coll.name in c.children]
    for parent in parents:
        if parent.name == "Scene Collection" or parent == bpy.context.scene.collection:
            continue
        source, res = get_effective_overrides(parent, global_settings)
        if res != global_settings:
            return source, res
            
    return bpy.context.scene, global_settings

def get_export_groups(context, settings):
    mode = settings.export_mode
    limit = settings.export_limit
    global_path = bpy.path.abspath(settings.export_path)
    
    # Determine items based on limit
    objs_to_check = []
    if limit == 'VISIBLE':
        objs_to_check = [obj for obj in context.view_layer.objects if obj.visible_get()]
    elif limit == 'SELECTED':
        objs_to_check = [obj for obj in context.selected_objects]
    elif limit == 'RENDER':
        objs_to_check = [obj for obj in context.view_layer.objects if not obj.hide_render]
        
    if not objs_to_check:
        return {}

    # Filter by type early to avoid non-exportable objects (cameras, lights) triggering groups
    objs_to_check = [o for o in objs_to_check if o.type in {'MESH', 'ARMATURE', 'EMPTY'}]
    
    if not objs_to_check:
        return {}

    # Grouping
    export_groups = {} # { name: {'objects': [], 'settings': settings, 'source': source, 'path': path} }

    # Shared Armature Pre-check
    shared_armature_obj = None
    if settings.shared_armature:
        armatures = [o for o in objs_to_check if o.type == 'ARMATURE']
        if len(armatures) == 1:
            shared_armature_obj = armatures[0]
            # Remove the armature from main list so it doesn't create its own group
            objs_to_check = [o for o in objs_to_check if o != shared_armature_obj]
        else:
            # If 0 or >1 armatures, shared armature mode is effectively disabled
            # We could report here, but get_export_groups is usually called multiple times
            pass

    if mode == 'OBJECTS':
        for obj in objs_to_check:
            if obj.type not in {'MESH', 'ARMATURE', 'EMPTY'}: continue
            
            # Find effective settings from collections
            source = context.scene
            eff_settings = settings
            for coll in obj.users_collection:
                s, es = get_effective_overrides(coll, settings)
                if es != settings:
                    source = s
                    eff_settings = es
                    break
            
            path = bpy.path.abspath(eff_settings.export_path) if eff_settings.export_path else global_path
            if not path: continue
            
            export_groups[obj.name] = {'objects': [obj], 'settings': eff_settings, 'source': source, 'path': path}
            
    elif mode == 'PARENTS':
        for obj in objs_to_check:
            root = obj
            while root.parent:
                root = root.parent
            
            if root.name not in export_groups:
                # Find effective settings from root object's collections
                source = context.scene
                eff_settings = settings
                for coll in root.users_collection:
                    s, es = get_effective_overrides(coll, settings)
                    if es != settings:
                        source = s
                        eff_settings = es
                        break
                
                path = bpy.path.abspath(eff_settings.export_path) if eff_settings.export_path else global_path
                if not path: continue
                
                export_groups[root.name] = {'objects': [], 'settings': eff_settings, 'source': source, 'path': path}
            
            if obj not in export_groups[root.name]['objects']:
                export_groups[root.name]['objects'].append(obj)
        
        # Fill in the rest of the children for root groups
        for r_name in export_groups:
            root_obj = bpy.data.objects.get(r_name)
            if root_obj:
                for child in root_obj.children_recursive:
                    if child.type == 'MESH' and child not in export_groups[r_name]['objects']:
                         if child not in context.view_layer.objects.values(): continue
                         if limit == 'VISIBLE' and not child.visible_get(): continue
                         if limit == 'RENDER' and child.hide_render: continue
                         export_groups[r_name]['objects'].append(child)
                
                if root_obj.type in {'MESH', 'ARMATURE', 'EMPTY'} and root_obj not in export_groups[r_name]['objects']:
                    if root_obj in context.view_layer.objects.values():
                        if limit == 'VISIBLE' and not root_obj.visible_get(): pass
                        elif limit == 'RENDER' and root_obj.hide_render: pass
                        else:
                            export_groups[r_name]['objects'].append(root_obj)

    elif mode == 'COLLECTIONS':
        for obj in objs_to_check:
            colls = obj.users_collection
            for coll in colls:
                # Check collection level limits
                if coll.name == "Scene Collection": continue
                if limit == 'RENDER' and coll.hide_render: continue
                if limit == 'VISIBLE' and coll.hide_viewport: continue
                
                # Shared Armature Exclusion: Skip collections that contain the shared armature
                if shared_armature_obj and coll in shared_armature_obj.users_collection:
                    continue
                
                if coll.name not in export_groups:
                    # Determine effective settings using hierarchy
                    source, eff_settings = get_effective_overrides(coll, settings)
                    
                    path = bpy.path.abspath(eff_settings.export_path) if eff_settings.export_path else global_path
                    if not path: continue
                    
                    export_groups[coll.name] = {'objects': [], 'settings': eff_settings, 'source': source, 'path': path}
                
                if obj not in export_groups[coll.name]['objects']:
                    export_groups[coll.name]['objects'].append(obj)
        
        # Fill in the rest of collection items
        for c_name in export_groups:
            coll = bpy.data.collections.get(c_name)
            if coll:
                for c_obj in coll.all_objects:
                    if c_obj.type in {'MESH', 'ARMATURE', 'EMPTY'} and c_obj not in export_groups[c_name]['objects']:
                         if c_obj not in context.view_layer.objects.values(): continue
                         if limit == 'VISIBLE' and not c_obj.visible_get(): continue
                         if limit == 'RENDER' and c_obj.hide_render: continue
                         export_groups[c_name]['objects'].append(c_obj)
                         
    # Remove empty groups (e.g. empty collections or collections with no valid meshes)
    if settings.shared_armature and shared_armature_obj:
        # In shared armature mode, we only want to export groups that contain at least one mesh.
        # This prevents the armature's own collection or collections with only helper empties from triggering an export.
        export_groups = {k: v for k, v in export_groups.items() if any(o.type == 'MESH' for o in v['objects'])}
    else:
        export_groups = {k: v for k, v in export_groups.items() if v['objects']}

    # Inject Shared Armature into every remaining group
    if shared_armature_obj:
        for data in export_groups.values():
            if shared_armature_obj not in data['objects']:
                data['objects'].append(shared_armature_obj)
    
    return export_groups

class REXTOOLS3_OT_Export(Operator):
    bl_idname = "rextools3.export"
    bl_label = "Export"
    bl_description = "Export objects based on settings"
    
    def execute(self, context):
        global_settings = context.scene.rex_export_settings
        export_mode = global_settings.export_mode
        export_groups = get_export_groups(context, global_settings)
            
        if not export_groups:
            self.report({'ERROR'}, "No objects found to export with current settings.")
            return {'CANCELLED'}

        # Execution
        orig_active = context.view_layer.objects.active
        orig_selection = context.selected_objects[:]
        orig_mode = context.active_object.mode if context.active_object else 'OBJECT'

        # Switch to object mode if needed
        if orig_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        for name, data in export_groups.items():
            objs = data['objects']
            if not objs: continue
            
            # Use settings for this group (either global or override)
            item_settings = data['settings']
            fmt = item_settings.export_format
            preset_name = item_settings.export_preset
            
            # Fetch preset arguments
            preset_args = self.get_preset_args(fmt, preset_name)

            dest_dir = data.get('path') or bpy.path.abspath(item_settings.export_path)
            if not dest_dir:
                dest_dir = bpy.path.abspath(global_settings.export_path)
            
            if not dest_dir:
                self.report({'WARNING'}, f"Skipping {name}: No export path defined.")
                continue

            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir, exist_ok=True)
            
            filepath = os.path.join(dest_dir, f"{name}.{fmt.lower()}")
            
            bpy.ops.object.select_all(action='DESELECT')
            valid_objs = []
            for o in objs:
                try:
                    o.select_set(True)
                    valid_objs.append(o)
                except Exception as e:
                    print(f"Skipping selection for {o.name}: {e}")
            
            if not valid_objs:
                continue
            
            # --- Single Mesh Option (Collections mode only) ---
            temp_single_mesh_objs = []
            if export_mode == 'COLLECTIONS' and getattr(item_settings, 'single_mesh', False):
                mesh_objs = [o for o in valid_objs if o.type == 'MESH']
                non_mesh_objs = [o for o in valid_objs if o.type != 'MESH']
                
                if mesh_objs:
                    dup_objs = []
                    for o in mesh_objs:
                        dup_o = o.copy()
                        dup_o.data = o.data.copy()
                        context.scene.collection.objects.link(dup_o)
                        dup_objs.append(dup_o)
                    
                    bpy.ops.object.select_all(action='DESELECT')
                    for dup_o in dup_objs:
                        context.view_layer.objects.active = dup_o
                        dup_o.select_set(True)
                        for mod in list(dup_o.modifiers):
                            if mod.type != 'ARMATURE':
                                try:
                                    bpy.ops.object.modifier_apply(modifier=mod.name)
                                except Exception as e:
                                    print(f"Could not apply modifier {mod.name} on {dup_o.name}: {e}")
                        dup_o.select_set(False)
                    
                    bpy.ops.object.select_all(action='DESELECT')
                    for dup_o in dup_objs:
                        dup_o.select_set(True)
                    context.view_layer.objects.active = dup_objs[0]
                    
                    if len(dup_objs) > 1:
                        bpy.ops.object.join()
                    
                    merged_obj = context.active_object
                    merged_obj.name = name
                    if merged_obj.data:
                        merged_obj.data.name = name
                    
                    temp_single_mesh_objs.append(merged_obj)
                    valid_objs = [merged_obj] + non_mesh_objs

                    # Refresh selection for updated valid_objs
                    bpy.ops.object.select_all(action='DESELECT')
                    for o in valid_objs:
                        try:
                            o.select_set(True)
                        except Exception as e:
                            print(f"Skipping selection for {o.name}: {e}")

            # Sort by hierarchy depth (root first) to ensure parents are reset before children
            def get_obj_depth(obj):
                depth = 0
                curr = obj
                while curr.parent:
                    curr = curr.parent
                    depth += 1
                return depth
            
            valid_objs.sort(key=get_obj_depth)
            
            context.view_layer.objects.active = valid_objs[0]
            
            # Prepare export arguments
            op_args = {'filepath': filepath, 'use_selection': True}
            if fmt == 'OBJ':
                op_args = {'filepath': filepath, 'export_selected': True}
            
            # Update with preset args
            op_args.update(preset_args)
            
            # Check for Modifiers + Shape Keys conflict
            for o in valid_objs:
                if (o.type == 'MESH' and o.data.shape_keys and 
                    any(m.show_viewport for m in o.modifiers)):
                    
                    from ..core import notify
                    notify.error("Shape keys won't be exported. Modifier found in object.")
                    break

            # --- Rename Armature ---
            saved_armature_names = {} # { armature_obj: (orig_obj_name, orig_data_name) }
            clash_backups = [] # [(object_or_data, original_name)]
            
            if item_settings.rename_armature:
                # 1. Clear the 'Armature' name slot by renaming existing clashing items
                # Objects
                for obj in bpy.data.objects:
                    if obj.name == "Armature":
                        clash_backups.append((obj, obj.name))
                        obj.name = "Armature_REX_TEMP"
                
                # Armature Data
                for arm in bpy.data.armatures:
                    if arm.name == "Armature":
                        clash_backups.append((arm, arm.name))
                        arm.name = "Armature_REX_TEMP"

                # 2. Rename our target armatures to 'Armature'
                for o in valid_objs:
                    if o.type == 'ARMATURE':
                        saved_armature_names[o] = (o.name, o.data.name)
                        o.data.name = "Armature"
                        o.name = "Armature"
            
            # --- Check Armature Rest Position ---
            saved_armature_pose_position = {} # { armature_obj: original_pose_position }
            for o in valid_objs:
                if o.type == 'ARMATURE' and o.data.pose_position == 'REST':
                    saved_armature_pose_position[o] = 'REST'
                    o.data.pose_position = 'POSE'

            # --- Reset Transform ---
            import mathutils
            saved_transforms = {}
            # In COLLECTIONS mode, we treat the entire collection as a single unit.
            # We find the first top-level object to use as a shared pivot, then move everything by that offset.
            # This prevents siblings from overlapping at the origin.
            export_mode = global_settings.export_mode
            source_coll = data['source'] if isinstance(data['source'], bpy.types.Collection) else None
            
            if item_settings.reset_transform:
                # In COLLECTIONS mode, the user wants to treat the collection as the root (always at center).
                # To center the model, we must move the "1st level children" (direct members of the collection) to the origin.
                # Deeper children (parented to these 1st level objects) should follow their parents and not be reset individually.
                if export_mode == 'COLLECTIONS' and source_coll:
                    for o in source_coll.objects:
                        # Safety: only process if the object is actually being exported
                        if o in valid_objs:
                            try:
                                saved_transforms[o] = o.matrix_world.copy()
                                _, _, scl = o.matrix_world.decompose()
                                # Move to world origin (0,0,0) with identity rotation, preserving scale
                                o.matrix_world = mathutils.Matrix.LocRotScale((0, 0, 0), mathutils.Quaternion((1, 0, 0, 0)), scl)
                            except Exception as e:
                                print(f"Failed to reset transform for collection member {o.name}: {e}")
                else:
                    # For OBJECTS or PARENTS mode, or if no collection is found:
                    # Move every root object in the group to origin individually.
                    for o in valid_objs:
                        # Only reset transform for "root" objects in this group (no parent in group).
                        if o.parent and o.parent in valid_objs:
                            continue
                            
                        try:
                            saved_transforms[o] = o.matrix_world.copy()
                            _, _, scl = o.matrix_world.decompose()
                            o.matrix_world = mathutils.Matrix.LocRotScale((0, 0, 0), mathutils.Quaternion((1, 0, 0, 0)), scl)
                        except Exception as e:
                            print(f"Failed to reset transform for {o.name}: {e}")
                
                # Ensure children transforms are updated based on moved parents before export
                context.view_layer.update()

            # --- Pre-export transforms ---
            pre_rot = item_settings.pre_rotation
            pre_scl = item_settings.pre_scale
            needs_pre_rotation = any(v != 0.0 for v in pre_rot)
            needs_pre_scale = pre_scl != 1.0

            if needs_pre_rotation or needs_pre_scale:
                # Select only valid objects for transform
                bpy.ops.object.select_all(action='DESELECT')
                for o in valid_objs:
                    try: o.select_set(True)
                    except: pass

                if needs_pre_rotation:
                    for o in valid_objs:
                        # Inverse Step: Subtract pre_rot to prepare for application
                        o.rotation_euler.x -= pre_rot[0]
                        o.rotation_euler.y -= pre_rot[1]
                        o.rotation_euler.z -= pre_rot[2]
                    # Freeze Step: Bake the inverse rotation into mesh/armature data
                    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
                    for o in valid_objs:
                        # Offset Step: Restore visual state by adding back pre_rot
                        # This leaves the rotation values in the fields for export
                        o.rotation_euler.x += pre_rot[0]
                        o.rotation_euler.y += pre_rot[1]
                        o.rotation_euler.z += pre_rot[2]

                if needs_pre_scale:
                    for o in valid_objs:
                        # Inverse Step: Divide by pre_scl to prepare for application
                        o.scale /= pre_scl
                    # Freeze Step: Bake the inverse scale into mesh/armature data
                    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
                    for o in valid_objs:
                        # Offset Step: Restore visual state by multiplying back pre_scl
                        # This leaves the scale values in the fields for export
                        o.scale *= pre_scl

            try:
                if fmt == 'FBX':
                    if item_settings.fbx_remove_armature_root:
                        from ..core import fbx_utils
                        fbx_utils.run_patched_fbx_export(context, **op_args)
                    else:
                        bpy.ops.export_scene.fbx(**op_args)
                elif fmt == 'GLTF':
                    op_args['export_format'] = 'GLB'
                    bpy.ops.export_scene.gltf(**op_args)
                elif fmt == 'OBJ':
                    bpy.ops.wm.obj_export(**op_args)
                
                # Update last export path to this successfully used directory
                global_settings.last_export_path = dest_dir
            except Exception as e:
                self.report({'ERROR'}, f"Failed to export {name}: {e}")
            finally:
                # --- Restore pre-export transforms ---
                if needs_pre_rotation or needs_pre_scale:
                    bpy.ops.object.select_all(action='DESELECT')
                    for o in valid_objs:
                        try: o.select_set(True)
                        except: pass

                    if needs_pre_scale:
                        # Finalize Step: Bring the object back to 1.0 applied
                        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

                    if needs_pre_rotation:
                        # Finalize Step: Bring the object back to (0,0,0) applied
                        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
                
                # --- Restore Reset Transform ---
                if item_settings.reset_transform:
                    for o, mat in saved_transforms.items():
                        try:
                            o.matrix_world = mat
                        except Exception as e:
                            print(f"Failed to restore transform for {o.name}: {e}")
                    
                    # Ensure children transforms are updated after restoring parents
                    context.view_layer.update()

                # --- Restore Armature Names ---
                if item_settings.rename_armature:
                    # Restore our targets first
                    for o, (orig_obj_name, orig_data_name) in saved_armature_names.items():
                        try:
                            o.name = orig_obj_name
                            o.data.name = orig_data_name
                        except Exception as e:
                            print(f"Failed to restore armature name: {e}")
                    
                    # Restore clashing items (in reverse to avoid chain collisions)
                    for item, orig_name in reversed(clash_backups):
                        try:
                            item.name = orig_name
                        except Exception as e:
                            print(f"Failed to restore clashing name: {e}")
                
                # --- Restore Armature Pose Position ---
                for o, orig_pos in saved_armature_pose_position.items():
                    try:
                        o.data.pose_position = orig_pos
                    except Exception as e:
                        print(f"Failed to restore armature pose position: {e}")

                # --- Clean up Temporary Single Mesh Object ---
                if temp_single_mesh_objs:
                    for t_obj in temp_single_mesh_objs:
                        try:
                            t_mesh = t_obj.data
                            bpy.data.objects.remove(t_obj, do_unlink=True)
                            if t_mesh and t_mesh.users == 0:
                                bpy.data.meshes.remove(t_mesh)
                        except Exception as e:
                            print(f"Failed to remove temporary single mesh object: {e}")

        # Restore
        bpy.ops.object.select_all(action='DESELECT')
        for o in orig_selection:
            try: o.select_set(True)
            except: pass
        context.view_layer.objects.active = orig_active
        
        if orig_mode != 'OBJECT':
            try:
                bpy.ops.object.mode_set(mode=orig_mode)
            except Exception as e:
                print(f"Failed to restore mode {orig_mode}: {e}")

        # Detailed console output
        print("\n--- RexTools3 Export Summary ---")
        for name, data in export_groups.items():
            objs_names = ", ".join([o.name for o in data['objects']])
            print(f"Exported: {name} -> {data['path']} (Objects: {objs_names})")
        print("--------------------------------\n")


        self.report({'INFO'}, f"Batch Export Finished. Exported {len(export_groups)} items.")
        return {'FINISHED'}

    def get_preset_args(self, fmt, preset_name):
        if preset_name == 'NONE':
            return {}
            
        import os
        import bpy
        
        fmt_folder = {
            'FBX': "export_scene.fbx",
            'GLTF': "export_scene.gltf",
            'OBJ': "export_scene.obj"
        }.get(fmt)
        
        if not fmt_folder:
            return {}
            
        paths = bpy.utils.preset_paths(os.path.join("operator", fmt_folder))
        preset_file = None
        for p in paths:
            potential = os.path.join(p, f"{preset_name}.py")
            if os.path.exists(potential):
                preset_file = potential
                break
        
        if not preset_file:
            return {}
            
        args = {}
        try:
            with open(preset_file, 'r') as f:
                lines = f.readlines()
                for line in lines:
                    if line.strip().startswith("op."):
                        parts = line.split("=")
                        if len(parts) == 2:
                            prop = parts[0].replace("op.", "").strip()
                            val_str = parts[1].strip()
                            
                            # Ignore path-related properties from presets
                            if prop in {'filepath', 'directory', 'filename'}:
                                continue
                                
                            try:
                                val = eval(val_str, {"__builtins__": None}, {})
                                args[prop] = val
                            except:
                                if val_str.startswith("'") or val_str.startswith('"'):
                                    args[prop] = val_str.strip("'\"")
        except Exception as e:
            print(f"Error parsing preset {preset_name}: {e}")
            
        return args

class REXTOOLS3_OT_BrowseExportPath(Operator):
    bl_idname = "rextools3.browse_export_path"
    bl_label = "Browse"
    
    directory: StringProperty(subtype='DIR_PATH')
    target: StringProperty() # 'SCENE', 'COLLECTION'
    target_name: StringProperty() # Name of the collection
    
    def execute(self, context):
        if self.target == 'SCENE':
            context.scene.rex_export_settings.export_path = self.directory
        elif self.target == 'COLLECTION':
            name = self.target_name
            coll = bpy.data.collections.get(name) or context.view_layer.active_layer_collection.collection
            if coll:
                coll.rex_export_overrides.export_path = self.directory
                coll.rex_export_overrides.override_path = True
            else:
                self.report({'ERROR'}, "No valid collection found.")
                return {'CANCELLED'}
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class REXTOOLS3_OT_OpenExportFolder(Operator):
    bl_idname = "rextools3.open_export_folder"
    bl_label = "Open Export Folder"
    bl_description = "Open the folder containing the last exported file"

    def execute(self, context):
        import subprocess
        import sys
        
        path = context.scene.rex_export_settings.last_export_path
        if not path or not os.path.exists(path):
            self.report({'ERROR'}, "No valid export path found.")
            return {'CANCELLED'}

        if sys.platform.startswith('win'):
            os.startfile(path)
        elif sys.platform == 'darwin':
            subprocess.Popen(['open', path])
        else:
            subprocess.Popen(['xdg-open', path])

        return {'FINISHED'}
class REXTOOLS3_OT_ClearAllOverrides(Operator):
    bl_idname = "rextools3.clear_all_overrides"
    bl_label = "Clear All Overrides"
    bl_description = "Disable all overrides and reset flags for this collection"
    
    @classmethod
    def poll(cls, context):
        return context.collection is not None

    def execute(self, context):
        coll = context.collection
        overrides = coll.rex_export_overrides
        
        overrides.override_path = False
        overrides.override_texture_copy_path = False
        overrides.override_format = False
        overrides.override_preset = False
        overrides.override_remove_armature_root = False
        overrides.override_rename_armature = False
        overrides.override_reset_transform = False
        overrides.override_pre_rotation = False
        overrides.override_pre_scale = False
        overrides.override_single_mesh = False
        
        self.report({'INFO'}, f"Cleared all overrides for {coll.name}")
        return {'FINISHED'}

FORMAT_EXTENSIONS = {
    'BMP': '.bmp',
    'PNG': '.png',
    'JPEG': '.jpg',
    'JPEG2000': '.jp2',
    'TARGA': '.tga',
    'TARGA_RAW': '.tga',
    'CINEON': '.cin',
    'DPX': '.dpx',
    'MULTILAYER': '.exr',
    'OPEN_EXR': '.exr',
    'OPEN_EXR_MULTILAYER': '.exr',
    'HDR': '.hdr',
    'TIFF': '.tif',
    'WEBP': '.webp',
}


def _get_image_filename(img):
    """Determine a safe and valid filename for the image datablock."""
    raw_name = ""
    ext = ""
    if img.filepath:
        basename = os.path.basename(img.filepath)
        if basename:
            raw_name, ext = os.path.splitext(basename)
            
    if not raw_name:
        raw_name = bpy.path.clean_name(img.name)
    if not raw_name:
        raw_name = "texture"
        
    if not ext:
        ext = FORMAT_EXTENSIONS.get(img.file_format, '.png')
        
    return f"{raw_name}{ext}"


def _collect_images_from_material(mat):
    """Recursively collect all image datablocks from a material's node tree, including node groups."""
    images = set()
    if not mat or not mat.use_nodes or not mat.node_tree:
        return images
        
    def _traverse(tree, visited):
        if not tree or tree in visited:
            return
        visited.add(tree)
        for node in tree.nodes:
            if node.type == 'TEX_IMAGE' and node.image:
                images.add(node.image)
            elif node.type == 'GROUP' and getattr(node, 'node_tree', None):
                _traverse(node.node_tree, visited)
                
    _traverse(mat.node_tree, set())
    return images


def _collect_images_from_object(obj):
    """Collect all unique images from all material slots and mesh data of an object."""
    images = set()
    if not obj:
        return images
        
    mats = set()
    if hasattr(obj, "material_slots"):
        for slot in obj.material_slots:
            if slot.material:
                mats.add(slot.material)
    if hasattr(obj, "data") and hasattr(obj.data, "materials"):
        for mat in obj.data.materials:
            if mat:
                mats.add(mat)
                
    for mat in mats:
        images.update(_collect_images_from_material(mat))
        
    return images


def _resolve_image_on_disk(img, filename):
    """Attempt to find the image on disk across original and local project candidate locations."""
    candidates = []
    
    # 1. Direct resolution via image.filepath
    if img.filepath:
        abs_path = bpy.path.abspath(img.filepath)
        if abs_path:
            candidates.append(abs_path)
        norm_path = os.path.normpath(img.filepath)
        if norm_path and norm_path not in candidates:
            candidates.append(norm_path)
            
    # 2. Blend file directory candidates (if blend is saved)
    if bpy.data.is_saved and bpy.data.filepath:
        blend_dir = os.path.dirname(bpy.data.filepath)
        candidates.append(os.path.join(blend_dir, "textures", filename))
        candidates.append(os.path.join(blend_dir, filename))
        candidates.append(os.path.join(blend_dir, "Textures", filename))
        
        if img.filepath:
            clean_rel = img.filepath.lstrip("/\\")
            candidates.append(os.path.join(blend_dir, clean_rel))
            
    for cand in candidates:
        if cand and os.path.isfile(cand):
            return os.path.abspath(cand)
            
    return None


def _save_memory_image_to_disk(img, target_path):
    """Save an in-memory, packed, or generated image datablock to disk at target_path."""
    try:
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
        # 1. If packed into .blend, write raw bytes directly (exact, lossless)
        if img.packed_file and hasattr(img.packed_file, "data") and img.packed_file.data:
            with open(target_path, "wb") as f:
                f.write(img.packed_file.data)
            return True
            
        # 2. Force pixel data load into memory if needed
        if not img.has_data:
            try:
                _ = img.pixels[0]
            except Exception:
                pass
                
        # 3. Try saving via filepath_raw
        orig_filepath = img.filepath_raw
        try:
            img.filepath_raw = target_path
            img.save()
            if os.path.isfile(target_path):
                return True
        except Exception:
            pass
        finally:
            img.filepath_raw = orig_filepath
            
        # 4. Fallback to save_render
        try:
            img.save_render(target_path)
            if os.path.isfile(target_path):
                return True
        except Exception as e:
            print(f"[RexTools3] save_render failed for {img.name}: {e}")
            
    except Exception as e:
        print(f"[RexTools3] Failed to save image {img.name} to {target_path}: {e}")
        
    return False


class REXTOOLS3_OT_CopyTextures(Operator):
    bl_idname = "rextools3.copy_textures"
    bl_label = "Copy Textures"
    bl_description = "Copy textures used by materials on the current export targets to a specified folder"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        import shutil
        from ..core import notify
        
        settings = context.scene.rex_export_settings
        export_groups = get_export_groups(context, settings)
        if not export_groups:
            self.report({'ERROR'}, "No export targets found with current settings.")
            return {'CANCELLED'}
            
        # Collect textures per-destination directory
        # { resolved_dest_dir: set_of_images }
        dest_images = {}
        
        for name, data in export_groups.items():
            item_settings = data['settings']
            # Resolve destination directory, fallback to global scene-level setting if empty
            dest_dir = bpy.path.abspath(item_settings.texture_copy_path) if hasattr(item_settings, 'texture_copy_path') and item_settings.texture_copy_path else bpy.path.abspath(settings.texture_copy_path)
            
            if not dest_dir:
                self.report({'WARNING'}, f"Skipping texture copy for group '{name}': No copy path defined.")
                continue
                
            if dest_dir not in dest_images:
                dest_images[dest_dir] = set()
                
            # Collect all mesh/object textures for this group
            for obj in data['objects']:
                dest_images[dest_dir].update(_collect_images_from_object(obj))
                                        
        total_images = sum(len(imgs) for imgs in dest_images.values())
        if total_images == 0:
            self.report({'WARNING'}, "No textures found in export materials.")
            return {'FINISHED'}
            
        copied_count = 0
        skipped_count = 0
        missing_count = 0
        dest_dir_names = set()
        
        for dest_dir, images in dest_images.items():
            if not images:
                continue
                
            # Ensure destination directory exists
            if not os.path.exists(dest_dir):
                try:
                    os.makedirs(dest_dir, exist_ok=True)
                except Exception as e:
                    self.report({'ERROR'}, f"Failed to create directory {dest_dir}: {str(e)}")
                    continue
                    
            dest_dir_names.add(os.path.basename(dest_dir) or dest_dir)
            
            for img in images:
                # Handle UDIM / Tiled images
                is_udim = (img.source == 'TILED') or (img.filepath and ("<UDIM>" in img.filepath or "<udim>" in img.filepath))
                
                if is_udim and hasattr(img, "tiles") and len(img.tiles) > 0:
                    base_filename = _get_image_filename(img)
                    for tile in img.tiles:
                        tile_str = str(tile.number)
                        tile_filename = base_filename.replace("<UDIM>", tile_str).replace("<udim>", tile_str)
                        if "<UDIM>" not in base_filename and "<udim>" not in base_filename:
                            name_part, ext_part = os.path.splitext(base_filename)
                            tile_filename = f"{name_part}_{tile_str}{ext_part}"
                            
                        # Look on disk
                        src_path = _resolve_image_on_disk(img, tile_filename)
                        if not src_path:
                            # Try resolving tile filepath directly
                            if img.filepath:
                                t_path = bpy.path.abspath(img.filepath).replace("<UDIM>", tile_str).replace("<udim>", tile_str)
                                if os.path.isfile(t_path):
                                    src_path = t_path
                                    
                        dest_path = os.path.join(dest_dir, tile_filename)
                        if src_path and os.path.isfile(src_path):
                            try:
                                should_copy = True
                                if os.path.exists(dest_path):
                                    try:
                                        if os.path.samefile(src_path, dest_path):
                                            should_copy = False
                                        elif os.path.getmtime(src_path) <= os.path.getmtime(dest_path):
                                            should_copy = False
                                    except Exception:
                                        if os.path.normcase(os.path.abspath(src_path)) == os.path.normcase(os.path.abspath(dest_path)):
                                            should_copy = False
                                        else:
                                            try:
                                                if os.path.getmtime(src_path) <= os.path.getmtime(dest_path):
                                                    should_copy = False
                                            except Exception:
                                                pass
                                if should_copy:
                                    shutil.copy2(src_path, dest_path)
                                    copied_count += 1
                                else:
                                    skipped_count += 1
                            except Exception as e:
                                self.report({'WARNING'}, f"Failed to copy tile {tile_filename}: {str(e)}")
                        else:
                            missing_count += 1
                    continue
                
                # Standard / Non-UDIM image handling
                filename = _get_image_filename(img)
                src_path = _resolve_image_on_disk(img, filename)
                
                # If not found on disk, attempt saving from memory/packed data
                if not src_path:
                    has_memory_data = (img.packed_file is not None) or img.has_data or img.is_dirty or (img.size[0] > 0 and img.size[1] > 0)
                    if has_memory_data:
                        if bpy.data.is_saved and bpy.data.filepath:
                            blend_dir = os.path.dirname(bpy.data.filepath)
                            local_textures_dir = os.path.join(blend_dir, "textures")
                            local_file_path = os.path.join(local_textures_dir, filename)
                            if _save_memory_image_to_disk(img, local_file_path):
                                src_path = local_file_path
                                # Link image to local textures folder
                                img.filepath = f"//textures/{filename}"
                        else:
                            # Blend file not saved: save directly to destination
                            dest_path = os.path.join(dest_dir, filename)
                            if _save_memory_image_to_disk(img, dest_path):
                                copied_count += 1
                                continue
                                
                if not src_path or not os.path.isfile(src_path):
                    print(f"[RexTools3] Texture could not be found or extracted: {img.name} ({img.filepath})")
                    missing_count += 1
                    continue
                    
                dest_path = os.path.join(dest_dir, filename)
                
                try:
                    should_copy = True
                    if os.path.exists(dest_path):
                        try:
                            if os.path.samefile(src_path, dest_path):
                                should_copy = False
                            elif os.path.getmtime(src_path) <= os.path.getmtime(dest_path):
                                should_copy = False
                        except Exception:
                            if os.path.normcase(os.path.abspath(src_path)) == os.path.normcase(os.path.abspath(dest_path)):
                                should_copy = False
                            else:
                                try:
                                    if os.path.getmtime(src_path) <= os.path.getmtime(dest_path):
                                        should_copy = False
                                except Exception:
                                    pass
                    if should_copy:
                        shutil.copy2(src_path, dest_path)
                        copied_count += 1
                    else:
                        skipped_count += 1
                except Exception as e:
                    self.report({'WARNING'}, f"Failed to copy {filename}: {str(e)}")
                    
        dest_desc = ", ".join(f"'{name}'" for name in dest_dir_names)
        msg = f"Copied {copied_count} texture(s)"
        if skipped_count > 0:
            msg += f", {skipped_count} already existed"
        if missing_count > 0:
            msg += f", {missing_count} missing"
        msg += f" in {dest_desc}."
        
        self.report({'INFO'}, msg)
        if copied_count > 0:
            notify.success(msg)
        elif skipped_count > 0:
            notify.info(msg)
        else:
            notify.warning(msg)
            
        return {'FINISHED'}

