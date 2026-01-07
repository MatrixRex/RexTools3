import bpy
from bpy.types import Operator

class REXTOOLS3_OT_CleanModifiers(Operator):
    bl_idname = "rextools3.clean_modifiers"
    bl_label = "Clean Modifiers"
    bl_description = "Remove unused or invalid modifiers from objects"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        settings = context.scene.rex_common_settings
        all_objs = settings.clean_modifiers_all
        
        orig_selection = context.selected_objects[:]
        orig_active = context.active_object
        orig_mode = context.mode

        # Determine target objects
        if all_objs:
            targets = [obj for obj in context.view_layer.objects if obj.visible_get() and obj.type == 'MESH']
        else:
            targets = [obj for obj in context.selected_objects if obj.type == 'MESH']

        if not targets:
            if not all_objs:
                self.report({'ERROR'}, "Nothing selected. Select at least one object or enable 'All'")
            else:
                self.report({'WARNING'}, "No visible mesh objects found")
            return {'CANCELLED'}

        # Switch to object mode if needed
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        removed_count = 0
        obj_count = 0

        for obj in targets:
            to_remove = []
            for mod in obj.modifiers:
                if settings.clean_modifiers_hidden and not mod.show_viewport:
                    to_remove.append(mod)
                    continue
                if self.is_useless(mod):
                    to_remove.append(mod)
            
            if to_remove:
                obj_count += 1
                for mod in to_remove:
                    obj.modifiers.remove(mod)
                    removed_count += 1

        # Restore mode
        try:
            if orig_mode != context.mode:
                bpy.ops.object.mode_set(mode=orig_mode)
        except:
            pass

        # Restore selection
        bpy.ops.object.select_all(action='DESELECT')
        for obj in orig_selection:
            try:
                obj.select_set(True)
            except:
                pass
        context.view_layer.objects.active = orig_active

        self.report({'INFO'}, f"Cleaned {removed_count} modifiers from {obj_count} objects")
        return {'FINISHED'}

    def is_useless(self, mod):
        # 1. Check for missing target objects (Broken modifiers)
        target_props = ['object', 'target', 'map_object', 'vertex_group_object', 'control_object']
        for prop in target_props:
            if hasattr(mod, prop):
                val = getattr(mod, prop)
                if val is None:
                    # Specific types that absolutely need a target to function
                    if mod.type in {
                        'BOOLEAN', 'SHRINKWRAP', 'ARMATURE', 'HOOK', 
                        'DATA_TRANSFER', 'MESH_DEFORM', 'LATTICE', 
                        'SURFACE_DEFORM', 'WARP', 'CURVE', 'CAST'
                    }:
                        return True
                    if mod.type == 'MIRROR' and prop == 'mirror_object' and val is None:
                        pass
        # 2. Check for zeroed out influence/levels (Useless modifiers)
        if mod.type == 'SUBSURF' and mod.levels == 0 and mod.render_levels == 0:
            return True
        if mod.type == 'BEVEL' and mod.width == 0.0:
            return True
        if mod.type == 'SOLIDIFY' and mod.thickness == 0.0:
            return True
        return False
