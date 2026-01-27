import bpy
from bpy.types import Operator
from .clean_modifiers import is_modifier_useless

class REXTOOLS3_OT_ApplyModifiers(Operator):
    """Apply all modifiers on selected objects with an ignore list"""
    bl_idname = "rextools3.apply_modifiers"
    bl_label = "Apply Modifiers"
    bl_description = "Apply all modifiers from all selected objects, ignoring specified types"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        settings = context.scene.rex_common_settings
        if len(settings.apply_modifiers_ignore_list) == 0:
            item = settings.apply_modifiers_ignore_list.add()
            item.modifier_type = 'ARMATURE'
        
        return self.execute(context)

    def execute(self, context):
        settings = context.scene.rex_common_settings
        ignore_types = {item.modifier_type for item in settings.apply_modifiers_ignore_list}
        
        targets = [obj for obj in context.selected_objects if obj.type == 'MESH']

        if not targets:
            self.report({'ERROR'}, "No mesh objects selected")
            return {'CANCELLED'}

        orig_mode = context.mode
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        applied_total = 0
        obj_count = 0

        for obj in targets:
            context.view_layer.objects.active = obj
            
            # We need to collect names first because applying changes the stack
            to_apply = []
            for mod in obj.modifiers:
                # 1. Skip if hidden in viewport
                if not mod.show_viewport:
                    continue
                
                # 2. Skip if in ignore list
                if mod.type in ignore_types:
                    continue
                
                # 3. Skip if "useless" (broken or zero influence)
                if is_modifier_useless(mod):
                    continue
                
                to_apply.append(mod.name)

            if to_apply:
                obj_count += 1
                for mod_name in to_apply:
                    try:
                        # modifier_apply works on the active object
                        bpy.ops.object.modifier_apply(modifier=mod_name)
                        applied_total += 1
                    except Exception as e:
                        self.report({'WARNING'}, f"Failed to apply {mod_name} on {obj.name}: {e}")

        # Restore mode
        if orig_mode != context.mode:
            try:
                bpy.ops.object.mode_set(mode=orig_mode)
            except:
                pass

        self.report({'INFO'}, f"Applied {applied_total} modifiers across {obj_count} objects")
        return {'FINISHED'}


class REXTOOLS3_OT_ApplyModifiersAddIgnore(Operator):
    bl_idname = "rextools3.apply_modifiers_add_ignore"
    bl_label = "Add Ignore Type"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        context.scene.rex_common_settings.apply_modifiers_ignore_list.add()
        return {'FINISHED'}


class REXTOOLS3_OT_ApplyModifiersRemoveIgnore(Operator):
    bl_idname = "rextools3.apply_modifiers_remove_ignore"
    bl_label = "Remove Ignore Type"
    bl_options = {'INTERNAL'}
    
    index: bpy.props.IntProperty()

    def execute(self, context):
        context.scene.rex_common_settings.apply_modifiers_ignore_list.remove(self.index)
        return {'FINISHED'}


def register():
    # Initialize default ignore list if empty
    # Note: This runs on register, but might be better in an init hook or check
    pass
