import bpy
from bpy.types import Operator

# Modifier types and their required target object properties.
# If any of these properties are None, the modifier cannot function.
MODIFIER_REQUIRED_PROPERTIES = {
    'BOOLEAN': ('object',),
    'SHRINKWRAP': ('target',),
    'ARMATURE': ('object',),
    'HOOK': ('object',),
    'DATA_TRANSFER': ('object',),
    'MESH_DEFORM': ('object',),
    'LATTICE': ('object',),
    'SURFACE_DEFORM': ('target',),
    'WARP': ('object_from', 'object_to'),
    'CURVE': ('object',),
}

def is_modifier_broken(mod):
    """Check if the modifier requires a target object that is missing (None)."""
    required_props = MODIFIER_REQUIRED_PROPERTIES.get(mod.type)
    if not required_props:
        return False
        
    for prop in required_props:
        if hasattr(mod, prop):
            if getattr(mod, prop) is None:
                return True
    return False

def is_modifier_zero_influence(mod):
    """Check if the modifier has zeroed-out settings causing it to do nothing."""
    if mod.type == 'SUBSURF':
        return mod.levels == 0 and mod.render_levels == 0
    if mod.type == 'BEVEL':
        return mod.width == 0.0
    if mod.type == 'SOLIDIFY':
        return mod.thickness == 0.0
    return False

def is_modifier_useless(mod):
    """Legacy helper combining both checks, used by apply_modifiers.py."""
    return is_modifier_broken(mod) or is_modifier_zero_influence(mod)


class REXTOOLS3_OT_CleanModifiers(Operator):
    bl_idname = "rextools3.clean_modifiers"
    bl_label = "Clean Modifiers"
    bl_description = "Remove unused, invalid, or hidden modifiers from objects"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return bool(context.selected_objects)

    def execute(self, context):
        settings = context.scene.rex_common_settings
        scope = settings.clean_modifiers_selection
        validation = settings.clean_modifiers_validation
        
        orig_selection = context.selected_objects[:]
        orig_active = context.active_object
        orig_mode = context.mode

        # Determine target objects based on selection scope dropdown
        if scope == 'SELECTED':
            targets = [obj for obj in context.selected_objects if obj.type == 'MESH']
        elif scope == 'VISIBLE':
            targets = [obj for obj in context.view_layer.objects if obj.visible_get() and obj.type == 'MESH']
        else:  # ALL
            targets = [obj for obj in context.scene.objects if obj.type == 'MESH']

        if not targets:
            if scope == 'SELECTED':
                self.report({'ERROR'}, "Nothing selected. Select at least one object")
            else:
                self.report({'WARNING'}, "No mesh objects found in target scope")
            return {'CANCELLED'}

        # Switch to object mode if needed
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        removed_count = 0
        obj_count = 0

        for obj in targets:
            to_remove = []
            for mod in obj.modifiers:
                should_remove = False
                is_hidden = not mod.show_viewport
                
                # Calculate status based on validation dropdown setting
                if validation == 'UNAFFECTED':
                    should_remove = is_modifier_useless(mod)
                elif validation == 'HIDDEN':
                    should_remove = is_hidden
                elif validation == 'ALL':
                    should_remove = True
                
                if should_remove:
                    to_remove.append(mod)
            
            if to_remove:
                obj_count += 1
                for mod in to_remove:
                    obj.modifiers.remove(mod)
                    removed_count += 1

        # Restore mode
        if orig_mode != context.mode:
            try:
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
        
        # Restore active object
        if orig_active and orig_active.name in context.view_layer.objects:
            context.view_layer.objects.active = orig_active

        self.report({'INFO'}, f"Cleaned {removed_count} modifiers from {obj_count} objects")
        return {'FINISHED'}
