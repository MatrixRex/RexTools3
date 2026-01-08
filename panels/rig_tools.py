import bpy
from bpy.types import Panel

class VIEW3D_PT_bone_batch_rename(Panel):
    bl_label = "Bone Batch Rename"
    bl_idname = "VIEW3D_PT_bone_batch_rename"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "RexTools3"
    @classmethod
    def poll(cls, context):
        return (context.active_object and 
                context.active_object.type == 'ARMATURE' and 
                context.mode == 'OBJECT')

    def draw(self, context):
        layout = self.layout
        props = context.scene.bone_rename_props
        armature = context.active_object
        layout.label(text=f"Armature: {armature.name}", icon='ARMATURE_DATA')
        layout.label(text=f"Bones: {len(armature.data.bones)}")

        layout.separator()

        has_find_replace = bool(props.find_text)
        has_prefix_suffix = bool(props.prefix_text or props.suffix_text)

        box = layout.box()
        box.label(text="Find & Replace:", icon='FILE_REFRESH')
        col = box.column(align=True)
        col.prop(props, "find_text")
        col.prop(props, "replace_text")

        box = layout.box()
        box.label(text="Prefix & Suffix:", icon='PLUS')
        col = box.column(align=True)
        col.prop(props, "prefix_text")
        col.prop(props, "suffix_text")

        if has_find_replace and has_prefix_suffix:
            col.separator()
            col.prop(props, "apply_prefix_suffix_to_matches_only")

        layout.separator()

        if has_find_replace or has_prefix_suffix:
            box = layout.box()
            box.label(text="Preview:", icon='ZOOM_IN')
            preview_count = 0

            for bone in armature.data.bones:
                old_name = bone.name
                new_name = old_name
                should_show = False
                found_match = False

                if has_find_replace and props.find_text in old_name:
                    new_name = new_name.replace(props.find_text, props.replace_text)
                    should_show = True
                    found_match = True

                if has_prefix_suffix:
                    should_apply = props.apply_prefix_suffix_to_matches_only and found_match or not props.apply_prefix_suffix_to_matches_only
                    if should_apply:
                        if props.prefix_text:
                            new_name = props.prefix_text + new_name
                        if props.suffix_text:
                            new_name = new_name + props.suffix_text
                        should_show = True

                if should_show and new_name != old_name:
                    preview_count += 1
                    if preview_count <= 5:
                        row = box.row()
                        row.scale_y = 0.8
                        row.label(text=f"{old_name} → {new_name}", icon='BONE_DATA')

            if preview_count > 5:
                box.label(text=f"... and {preview_count - 5} more", icon='THREE_DOTS')
            elif preview_count == 0:
                msg = "No matches found" if has_find_replace else "Will add prefix/suffix to all bones"
                box.label(text=msg, icon='INFO')

        layout.separator()

        row = layout.row()
        row.scale_y = 1.5
        row.enabled = has_find_replace or has_prefix_suffix
        row.operator("armature.batch_rename_bones", icon='FILE_REFRESH')

        box = layout.box()
        box.label(text="Info:", icon='INFO')
        col = box.column(align=True)
        col.scale_y = 0.8
        col.label(text="• Vertex groups will be automatically updated")
        col.label(text="• Make sure to be in Object mode")