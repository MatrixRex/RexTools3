import bpy
from ..core import texture_oven_core as core
from ..core import notify

class REXTOOLS3_OT_texture_oven_assign_object(bpy.types.Operator):
    bl_idname = "rextools3.texture_oven_assign_object"
    bl_label = "Assign Selection"
    bl_description = "Assign active object to the slot"
    bl_options = {'REGISTER', 'UNDO'}

    role: bpy.props.StringProperty(default="target")

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        props = context.scene.rex_texture_oven_props
        active_obj = context.active_object

        if self.role == "target":
            props.target_object = active_obj
            notify.success(f"Target set to: {active_obj.name}")
        elif self.role == "source":
            props.source_object = active_obj
            notify.success(f"Source set to: {active_obj.name}")
        
        return {'FINISHED'}


class REXTOOLS3_OT_texture_oven_clear_object(bpy.types.Operator):
    bl_idname = "rextools3.texture_oven_clear_object"
    bl_label = "Clear"
    bl_description = "Clear object from the slot"
    bl_options = {'REGISTER', 'UNDO'}

    role: bpy.props.StringProperty(default="target")

    def execute(self, context):
        props = context.scene.rex_texture_oven_props

        if self.role == "target":
            props.target_object = None
        elif self.role == "source":
            props.source_object = None
            
        return {'FINISHED'}


class REXTOOLS3_OT_texture_oven_bake(bpy.types.Operator):
    bl_idname = "rextools3.texture_oven_bake"
    bl_label = "Bake Imposter"
    bl_description = "Setup materials and bake Diffuse, AO, and Normal maps using Cycles"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        props = context.scene.rex_texture_oven_props
        return props.target_object is not None and props.source_object is not None

    def execute(self, context):
        props = context.scene.rex_texture_oven_props
        success = core.bake_imposter(context, props)
        if success:
            return {'FINISHED'}
        else:
            return {'CANCELLED'}


class REXTOOLS3_OT_texture_oven_save_images(bpy.types.Operator):
    bl_idname = "rextools3.texture_oven_save_images"
    bl_label = "Save Images"
    bl_description = "Save baked images to the specified directory"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        props = context.scene.rex_texture_oven_props
        return props.target_object is not None and props.save_directory != ""

    def execute(self, context):
        props = context.scene.rex_texture_oven_props
        core.save_baked_textures(props.target_object, props.save_directory)
        return {'FINISHED'}
