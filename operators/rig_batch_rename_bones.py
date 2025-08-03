import bpy
from bpy.types import Operator

class ARMATURE_OT_batch_rename_bones(Operator):
    """Batch rename bones using find and replace"""
    bl_idname = "armature.batch_rename_bones"
    bl_label = "Rename Bones"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.active_object and 
                context.active_object.type == 'ARMATURE' and
                context.mode == 'OBJECT')

    def execute(self, context):
        props = context.scene.bone_rename_props
        armature = context.active_object

        has_find_replace = bool(props.find_text)
        has_prefix_suffix = bool(props.prefix_text or props.suffix_text)

        if not has_find_replace and not has_prefix_suffix:
            self.report({'WARNING'}, "Specify find/replace text or prefix/suffix")
            return {'CANCELLED'}

        original_mode = context.mode
        bpy.context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(mode='EDIT')

        renamed_count = 0

        try:
            for bone in armature.data.edit_bones:
                old_name = bone.name
                new_name = old_name
                should_rename = False
                found_match = False

                if has_find_replace and props.find_text in old_name:
                    new_name = new_name.replace(props.find_text, props.replace_text)
                    should_rename = True
                    found_match = True

                if has_prefix_suffix:
                    should_apply_prefix_suffix = props.apply_prefix_suffix_to_matches_only and found_match or not props.apply_prefix_suffix_to_matches_only

                    if should_apply_prefix_suffix:
                        if props.prefix_text:
                            new_name = props.prefix_text + new_name
                        if props.suffix_text:
                            new_name = new_name + props.suffix_text
                        should_rename = True

                if should_rename and new_name != old_name:
                    bone.name = new_name
                    renamed_count += 1
                    print(f"Renamed: {old_name} -> {bone.name}")

        except Exception as e:
            self.report({'ERROR'}, f"Error renaming bones: {str(e)}")
            return {'CANCELLED'}

        finally:
            bpy.ops.object.mode_set(mode='OBJECT')

        if renamed_count > 0:
            self.report({'INFO'}, f"Renamed {renamed_count} bone(s)")
        else:
            if has_find_replace:
                self.report({'WARNING'}, f"No bones found containing '{props.find_text}'")
            else:
                self.report({'WARNING'}, "No bones were renamed")

        return {'FINISHED'}
