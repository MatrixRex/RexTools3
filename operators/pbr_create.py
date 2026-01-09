import bpy
from bpy.types import Operator

class PBR_OT_CreateMaterial(Operator):
    bl_idname = "pbr.create_material"
    bl_label = "Create PBR Material"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if not obj:
            self.report({'WARNING'}, "No active object")
            return {'CANCELLED'}

        material = bpy.data.materials.new(name="PBR_Material")
        material.use_nodes = True

        if obj.data.materials:
            obj.data.materials[0] = material
        else:
            obj.data.materials.append(material)

        nodes = material.node_tree.nodes
        nodes.clear()

        principled = nodes.new('ShaderNodeBsdfPrincipled')
        principled.inputs['Base Color'].default_value = (1.0, 1.0, 1.0, 1.0)
        output = nodes.new('ShaderNodeOutputMaterial')
        principled.location = (0, 0)
        output.location = (300, 0)

        material.node_tree.links.new(principled.outputs['BSDF'], output.inputs['Surface'])

        return {'FINISHED'}
