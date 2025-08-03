import bpy
from bpy.props import IntProperty, FloatProperty, BoolProperty, StringProperty, PointerProperty
from bpy.types import PropertyGroup


    
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
                       
def get_roughness_strength(self):
    """Get roughness strength from the actual node"""
    try:
        mat = bpy.context.active_object.active_material
        if not mat or not mat.use_nodes:
            return 1.0
        
        nodes = mat.node_tree.nodes
        principled = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if not principled:
            return 1.0
            
        inp = principled.inputs.get("Roughness")
        if inp and inp.is_linked and inp.links[0].from_node.type == 'MATH':
            return inp.links[0].from_node.inputs[1].default_value
    except:
        pass
    return 1.0

def set_roughness_strength(self, value):
    """Set roughness strength to the actual node"""
    try:
        mat = bpy.context.active_object.active_material
        if not mat or not mat.use_nodes:
            return
        
        nodes = mat.node_tree.nodes
        principled = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if not principled:
            return
            
        inp = principled.inputs.get("Roughness")
        if inp and inp.is_linked and inp.links[0].from_node.type == 'MATH':
            inp.links[0].from_node.inputs[1].default_value = max(0.0, min(value, 1.0))
    except:
        pass

def get_metallic_strength(self):
    """Get metallic strength from the actual node"""
    try:
        mat = bpy.context.active_object.active_material
        if not mat or not mat.use_nodes:
            return 1.0
        
        nodes = mat.node_tree.nodes
        principled = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if not principled:
            return 1.0
            
        inp = principled.inputs.get("Metallic")
        if inp and inp.is_linked and inp.links[0].from_node.type == 'MATH':
            return inp.links[0].from_node.inputs[1].default_value
    except:
        pass
    return 1.0

def set_metallic_strength(self, value):
    """Set metallic strength to the actual node"""
    try:
        mat = bpy.context.active_object.active_material
        if not mat or not mat.use_nodes:
            return
        
        nodes = mat.node_tree.nodes
        principled = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if not principled:
            return
            
        inp = principled.inputs.get("Metallic")
        if inp and inp.is_linked and inp.links[0].from_node.type == 'MATH':
            inp.links[0].from_node.inputs[1].default_value = max(0.0, min(value, 1.0))
    except:
        pass

class BoneRenameProperties(PropertyGroup):
    find_text: StringProperty(
        name="Find",
        description="Text to find in bone names",
        default=""
    )
    replace_text: StringProperty(
        name="Replace",
        description="Text to replace with",
        default=""
    )
    prefix_text: StringProperty(
        name="Prefix",
        description="Text to add before bone names",
        default=""
    )
    suffix_text: StringProperty(
        name="Suffix",
        description="Text to add after bone names",
        default=""
    )
    apply_prefix_suffix_to_matches_only: BoolProperty(
        name="Apply to Find/Replace matches only",
        description="Only apply prefix/suffix to bones matching the find string",
        default=False
    )
                    
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
    
class PBRMaterialSettings(PropertyGroup):
    use_separate_alpha_map: BoolProperty(
        name="Use Separate Alpha Map",
        description="Use a separate alpha map instead of Base Color's alpha channel",
        default=False,
        update=update_use_sep_alpha
    )
    
    roughness_strength: FloatProperty(
        name="Roughness Strength",
        default=1.0,
        min=0.0,
        max=1.0,
        get=get_roughness_strength,
        set=set_roughness_strength
    )
    
    metallic_strength: FloatProperty(
        name="Metallic Strength", 
        default=1.0,
        min=0.0,
        max=1.0,
        get=get_metallic_strength,
        set=set_metallic_strength
    )

def register_properties():
    wm = bpy.types.WindowManager
    wm.modal_x = IntProperty(name="Mouse X", default=0)
    wm.modal_y = IntProperty(name="Mouse Y", default=0)

    bpy.types.Scene.highlow_renamer_props = PointerProperty(type=HighLowRenamerProperties)
    bpy.types.Scene.bone_rename_props = PointerProperty(type=BoneRenameProperties)

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
    del bpy.types.Scene.bone_rename_props

    del wm.select_similar_threshold
    del wm.clear_inner_uv_area_seam
    del wm.reseam_uv_area_seam
    del wm.stop_loop_at_seam
    
    del bpy.types.Material.pbr_settings