import bpy, bpy.utils.previews, os
from functools import reduce
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
from bpy.props import *
from bpy.types import Object
from mathutils import Vector
from winreg import *

from .settings import SettingItem

from .preferences import get_prefs
from .enums import *
from .uilist import *
from . import xml_util
from . import properties


def realpath(path:str):
    return bpy.path.abspath(path)

sep = os.path.sep
icon = None

def get_export_root():
    app_conf = get_prefs()
    export_path = realpath(os.path.join(os.path.split(bpy.data.filepath)[0], app_conf.output))
    if not os.path.exists(export_path): os.makedirs(export_path)
    return export_path
    
def get_directories(data_path:str):
    export_path = realpath(data_path)
    if not os.path.exists(export_path): os.makedirs(export_path)

    highpoly_path = realpath(os.path.join(export_path, "Highpoly"))
    if not os.path.exists(highpoly_path) : os.makedirs(highpoly_path)
    
    lowpoly_path = realpath(os.path.join(export_path, "Lowpoly"))
    if not os.path.exists(lowpoly_path) : os.makedirs(lowpoly_path)

    return export_path, highpoly_path, lowpoly_path

def write_xml(conf:SettingItem, xml_file, export_dir = ''):
    app_conf = get_prefs()

    export_path, highpoly_path, lowpoly_path = get_directories(export_dir)

    export_objects:list[tuple[list[Object], str, str, str]] = []

    settings_element = Element("Settings")
    settings_element.set('Version',"3.19.2")
    
    image_output = os.path.join(realpath(export_path), conf.name) + app_conf.img_format

    highpoly_element = SubElement(settings_element,'HighPolyModel')
    highpoly_element.set('DefaultMeshScale','1.000000')
    
    groups = list(set([g.group for g in conf.highpoly]))
    for group in groups :
        hp = [h for h in conf.highpoly if h.group == group and h.object is not None]
        if len(hp) == 0 : continue

        objs = [h.object for h in hp]
        filepath = os.path.join(highpoly_path,objs[0].name + '.obj')
        if not os.path.exists(filepath) or reduce(lambda a,b : a or b,[h.export for h in hp]) :
            export_objects.append((objs, filepath, 'HIGH', None))
        
        highpoly = hp[0]
        mesh_element = SubElement(highpoly_element, 'Mesh')
        xml_util.set_xml(mesh_element, "Visible", highpoly.visible)
        xml_util.set_xml(mesh_element, "Scale", highpoly.mesh_scale)
        xml_util.set_xml(mesh_element, "IgnorePerVertexColor", highpoly.ignore_vcolor)
        xml_util.set_xml(mesh_element, "AverageNormals", highpoly.normalsmoothing)
        xml_util.set_xml(mesh_element, "BaseTexIsTSNM", False)
        xml_util.set_xml(mesh_element, "File", filepath)
        xml_util.set_xml(mesh_element, "PositionOffset", highpoly.offset)

    lowpoly_element = SubElement(settings_element, 'LowPolyModel')
    lowpoly_element.set('DefaultMeshScale', '1.000000')

    lowpolies = sorted(conf.lowpoly, key = lambda l : l.cage.enabled)
    
    for lowpoly in lowpolies :
        obj = lowpoly.object
        if obj is None or obj.type != 'MESH' : continue

        cage_opt:xNormal_CageSettings = lowpoly.cage
        cage_enabled = cage_opt.enabled
        if cage_opt.enabled:
            cage_filepath = os.path.join(lowpoly_path, obj.name + '_Cage.obj')
            if cage_opt.type == cage_type[0][0]: #OBJECT
                cage_enabled = cage_opt.object is not None and cage_opt.object.type == 'MESH'
                if cage_enabled:
                    export_objects.append(([cage_opt.object], cage_filepath, 'LOW', None))
            elif cage_opt.type == cage_type[1][0]: #FILE
                cage_filepath = cage_opt.cage_file
                cage_enabled = os.path.exists(cage_filepath)
            elif cage_opt.type == cage_type[2][0]: #SHAPEKEY
                cage_enabled = cage_opt.shape_key and obj.data.shape_keys is not None and cage_opt.shape_key in obj.data.shape_keys.key_blocks
                if cage_enabled:
                    export_objects.append(([obj], cage_filepath, 'LOW', cage_opt.shape_key))
                
        
        filepath = os.path.join(lowpoly_path, obj.name + '.obj')
        if not os.path.exists(filepath) or lowpoly.export :
            export_objects.append(([obj], filepath, 'LOW', None))

        mesh_element = SubElement(lowpoly_element, 'Mesh')
        xml_util.set_xml(mesh_element, "Visible", lowpoly.visible)
        xml_util.set_xml(mesh_element, "File", filepath)
        xml_util.set_xml(mesh_element, "AverageNormals", lowpoly.normalsmoothing)
        xml_util.set_xml(mesh_element, "MaxRayDistanceFront", lowpoly.max_front_ray)
        xml_util.set_xml(mesh_element, "MaxRayDistanceBack", lowpoly.max_rear_ray)
        xml_util.set_xml(mesh_element, "UseCage", cage_enabled)
        xml_util.set_xml(mesh_element, "NormapMapType", "Tangent-space")
        xml_util.set_xml(mesh_element, "UsePerVertexColors", "true")
        xml_util.set_xml(mesh_element, "UseFresnel", "false")
        xml_util.set_xml(mesh_element, "FresnelRefractiveIndex", "1.330000")
        xml_util.set_xml(mesh_element, "ReflectHDRMult", "1.000000")
        xml_util.set_xml(mesh_element, "VectorDisplacementTS", "false")
        xml_util.set_xml(mesh_element, "VDMSwizzleX", "X+")
        xml_util.set_xml(mesh_element, "VDMSwizzleY", "Y+")
        xml_util.set_xml(mesh_element, "VDMSwizzleZ", "Z+")
        xml_util.set_xml(mesh_element, "BatchProtect", lowpoly.batch)
        xml_util.set_xml(mesh_element, "CastShadows", "true")
        xml_util.set_xml(mesh_element, "ReceiveShadows", "true")
        xml_util.set_xml(mesh_element, "BackfaceCull", "true")
        xml_util.set_xml(mesh_element, "NMSwizzleX", "X+")
        xml_util.set_xml(mesh_element, "NMSwizzleY", "Y+")
        xml_util.set_xml(mesh_element, "NMSwizzleZ", "Z+")
        xml_util.set_xml(mesh_element, "CageFile", cage_filepath if cage_enabled else '')
        xml_util.set_xml(mesh_element, "HighpolyNormalsOverrideTangentSpace", lowpoly.normals_override)
        xml_util.set_xml(mesh_element, "TransparencyMode", "None")
        xml_util.set_xml(mesh_element, "AlphaTestValue", "127")
        xml_util.set_xml(mesh_element, "Matte", "false")
        xml_util.set_xml(mesh_element, "Scale", lowpoly.mesh_scale)
        xml_util.set_xml(mesh_element, "MatchUVs", lowpoly.match_uvs)
        xml_util.set_xml(mesh_element, "UOffset", lowpoly.U_offset)
        xml_util.set_xml(mesh_element, "VOffset", lowpoly.V_offset)
        xml_util.set_xml(mesh_element, "PositionOffset", lowpoly.offset)
    
    generatemaps_element = SubElement(settings_element, 'GenerateMaps')
    xml_util.set_xml(generatemaps_element, "Width", conf.image.width)
    xml_util.set_xml(generatemaps_element, "Height", conf.image.height)
    xml_util.set_xml(generatemaps_element, "EdgePadding", conf.image.edge_padding)
    xml_util.set_xml(generatemaps_element, "BucketSize", conf.image.bucket_size)
    xml_util.set_xml(generatemaps_element, "ClosestIfFails", conf.closest_hit)
    xml_util.set_xml(generatemaps_element, "DiscardRayBackFacesHits", conf.discard_BF)
    xml_util.set_xml(generatemaps_element, "File", image_output)
    xml_util.set_xml(generatemaps_element, "AA", conf.image.AA_setting)
    xml_util.set_xml_color(generatemaps_element, "VDMBackgroundColor", Vector((0, 0, 0)))

    detail_element = SubElement(settings_element, "Detail")
    detail_element.set('Scale', "0.500000")
    detail_element.set('Method', "4Samples")

    for rendermap in properties.maps():
        rendermap.write(conf, settings_element)

    element_str = tostring(settings_element, 'utf-8')
    with xml_file as f :
        f.write(minidom.parseString(element_str).toprettyxml(indent="  "))

    return export_objects
