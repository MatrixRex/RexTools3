import bpy
from bpy.props import IntProperty, FloatProperty, BoolProperty, StringProperty, PointerProperty
from bpy.types import PropertyGroup

class HighLowRenamerProperties(PropertyGroup):
    obj_name: StringProperty(
        name="Object Name",
        description="Base name for the objects",
        default="Asset"
    )
    high_prefix: StringProperty(
        name="High Prefix",
        description="Prefix for high poly mesh",
        default="_high"
    )
    low_prefix: StringProperty(
        name="Low Prefix",
        description="Prefix for low poly mesh",
        default="_low"
    )
    
def update_use_sep_alpha(self, context):
        mat = self.id_data
        if not mat.use_nodes:
            return
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        principled = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if not principled:
            return

        alpha_inp = principled.inputs.get('Alpha')
        # remove any existing alpha links
        for link in list(alpha_inp.links):
            links.remove(link)

        # if we're falling back to Base Color alpha, reconnect it
        if not self.use_separate_alpha_map:
            base_inp = principled.inputs.get('Base Color')
            if base_inp and base_inp.is_linked:
                base_node = base_inp.links[0].from_node
                if base_node.type == 'TEX_IMAGE':
                    links.new(base_node.outputs['Alpha'], alpha_inp)
                    mat.blend_method = 'HASHED'
    
class PBRMaterialSettings(PropertyGroup):
    use_separate_alpha_map: BoolProperty(
        name="Use Separate Alpha Map",
        description="Use a separate alpha map instead of Base Color’s alpha channel",
        default=False,
        update=update_use_sep_alpha
    )

def register_properties():
    wm = bpy.types.WindowManager
    wm.modal_x = IntProperty(name="Mouse X", default=0)
    wm.modal_y = IntProperty(name="Mouse Y", default=0)

    bpy.types.Scene.highlow_renamer_props = PointerProperty(type=HighLowRenamerProperties)

    wm.select_similar_threshold = FloatProperty(
        name="Threshold",
        description="Face-normal select similarity threshold",
        default=0.0,
        min=0.0,
        max=1.0
    )
    wm.clear_inner_uv_area_seam = BoolProperty(
        name="Clear Inner",
        description="Clear all seams before marking the loop seam",
        default=False
    )
    wm.reseam_uv_area_seam = BoolProperty(
        name="Reseam",
        description="Deselect seams on the selected loop instead of marking",
        default=False
    )
    
    wm.stop_loop_at_seam = BoolProperty(
        name="Stop at Seam",
        description="Stop edge loop selection when a seam is encountered",
        default=True
    )
   
    bpy.types.Material.pbr_settings = PointerProperty(type=PBRMaterialSettings)

def unregister_properties():
    wm = bpy.types.WindowManager
    del wm.modal_x
    del wm.modal_y

    del bpy.types.Scene.highlow_renamer_props

    del wm.select_similar_threshold
    del wm.clear_inner_uv_area_seam
    del wm.reseam_uv_area_seam
    del wm.stop_loop_at_seam
    
    del bpy.types.Material.pbr_settings
    

