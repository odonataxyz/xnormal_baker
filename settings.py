from bpy.types import PropertyGroup, Object, Material
from bpy.props import *
from .enums import normal_smoothing, image_size, bucket_size, cage_type

class xNormal_ImageSettings(PropertyGroup):
    width: EnumProperty(items = image_size, name = "Image Size X", default = "512")
    height: EnumProperty(items = image_size, name = "Image Size Y", default = "512")
    AA_setting: EnumProperty(items = [('1', '1x', ''), ('2', '2x', ''), ('4', '4x', '')], name = "Antialiasing samples")
    edge_padding: IntProperty(name = "Edge Padding", description = "Image edge padding", default = 16, min = 0, max = 128, step= 1)
    bucket_size: EnumProperty(items = bucket_size, name = "Bucket size")

class xNormal_CageSettings(PropertyGroup):
    enabled: BoolProperty(name = 'Use cage', default = False)
    type: EnumProperty(items=cage_type, default=cage_type[0][0], name = "Type")
    object: PointerProperty(name = "Cage object", type=Object)
    shape_key: StringProperty(name = "Cage shape key")
    cage_external: BoolProperty(name = "Use external file", description = "Use external file for cage object", default = False)
    cage_file: StringProperty(subtype='FILE_PATH')

class xNormal_LowpolySettings(PropertyGroup):
    object: PointerProperty(name='Object', type=Object)
    export: BoolProperty(name='Export', default=True)
    cage: PointerProperty(type = xNormal_CageSettings)
    visible: BoolProperty(name = 'Visible', default = True)
    show_expands: BoolProperty(name = 'Expands', default = False)
    max_front_ray: FloatProperty(name = 'Maximum frontal ray distance', default = 0.5,min=0)
    max_rear_ray: FloatProperty(name=  'Maximum rear ray distance', default = 0.5,min=0)
    normalsmoothing: EnumProperty(items = normal_smoothing, name = 'Smoothing', default = 'UseExportedNormals')
    batch: BoolProperty(name = 'Batch protection', default = False)
    normals_override: BoolProperty(name = 'Hipoly normals override tangent space', description = 'High poly normals override tangent space', default = True)
    mesh_scale: FloatProperty(name=  'Mesh scale', default = 1.000, precision = 3)
    match_uvs: BoolProperty(name = 'Match UVs', default = False)
    U_offset: FloatProperty(name = 'U offset', default = 0.000, precision = 3)
    V_offset: FloatProperty(name = 'V offset', default = 0.000, precision = 3)
    offset: FloatVectorProperty(name = 'Position Offset', description = 'Position Offset', default = (0.0, 0.0, 0.0), min = 0.0, max = 1.0)
    
class xNormal_HighpolySettings(PropertyGroup):
    export: BoolProperty(name='Export', default=True)
    group: IntProperty(name='Group', default=1,min=1)
    object: PointerProperty(name='Object', type=Object)
    use_selection: BoolProperty(name = 'Use Selection', default = False)
    visible: BoolProperty(name = 'Visible', default = True)
    show_expands: BoolProperty(name = 'Expands', default = False)
    mesh_scale: FloatProperty(name = 'Mesh scale', default = 1.000, precision = 3)
    ignore_vcolor: BoolProperty(name = 'Ignore per-vertex color', default = True)
    normalsmoothing: EnumProperty(items = normal_smoothing, name = 'Smoothing', default = 'UseExportedNormals')
    offset: FloatVectorProperty(name = 'Position Offset', description = 'Position Offset', default = (0.0, 0.0, 0.0), min = 0.0, max = 1.0)
    
    
class xNormal_MaterialSettings(PropertyGroup):
    export: BoolProperty(name='Export', default=True)
    material: PointerProperty(type=Material)
    
    
class SettingItem():
    name: StringProperty(default="xNormal")
    image: PointerProperty(type = xNormal_ImageSettings)
    highpoly: CollectionProperty(type = xNormal_HighpolySettings)
    active_lowpoly_index: IntProperty()
    lowpoly: CollectionProperty(type = xNormal_LowpolySettings)
    active_highpoly_index: IntProperty()
    materials: CollectionProperty(type = xNormal_MaterialSettings)
    render_base_texture: BoolProperty(name = "Render Base Texture Map", description = "xNormal will generate base texture map.", default = False)
    discard_BF: BoolProperty(name = "Discard backfaces hits", description = "Baking option", default = True)
    closest_hit: BoolProperty(name = "Closest hit if ray fails", description = "Baking option", default = True)
    show_expands: BoolProperty(name='Expand', default=False)
