import bpy, os
from functools import reduce
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
from bpy.props import *
from bpy.types import Object, MultiresModifier, Context, Material
from mathutils import Vector
from winreg import *

from .settings import SettingItem

from .preferences import get_prefs
from .enums import *
from .uilist import *
from . import xml_util
from . import properties
from .utils import unlink_xnormal_collection, xnormal_collection, snapshot_mesh

def realpath(path:str):
    return bpy.path.abspath(path)

sep = os.path.sep
icon = None

def get_export_root():
    app_conf = get_prefs()
    root = os.path.split(bpy.data.filepath)[0] if bpy.data.filepath else bpy.app.tempdir
    export_path = realpath(os.path.join(root, app_conf.output))
    if not os.path.exists(export_path): os.makedirs(export_path)
    return export_path
    
def get_directories(data_path:str, mesh_dir:str = ''):
    app_conf = get_prefs()
    export_path = realpath(data_path)
    if not mesh_dir:
        mesh_dir = export_path
    if not os.path.exists(export_path): os.makedirs(export_path)

    highpoly_path = realpath(os.path.join(mesh_dir, app_conf.hipoly_dir))
    if not os.path.exists(highpoly_path) : os.makedirs(highpoly_path)
    
    lowpoly_path = realpath(os.path.join(mesh_dir, app_conf.lowpoly_dir))
    if not os.path.exists(lowpoly_path) : os.makedirs(lowpoly_path)

    return export_path, highpoly_path, lowpoly_path

def export_obj(context:Context, objects:list[Object], filepath:str, type:str, ignore_materials:list[Material], shapekey:str, uv:str = None):
    #一時コレクション
    collection = xnormal_collection()

    # 一時コレクションにリンクしておく
    for ob in objects:
        if ob.name not in collection.objects:
            collection.objects.link(ob)

    is_snapshot = type == "LOW"

    # 解像度モディファイア切り替え
    multires_mods:dict[MultiresModifier, int] = {}
    for ob in objects:
        for modifier in ob.modifiers:
            if modifier.type != 'MULTIRES': continue

            multires_mods[modifier] = modifier.levels
            modifier.levels = 0 if type == "LOW" else modifier.total_levels
    
    if is_snapshot:
        snapshots = [snapshot_mesh(context, o, ignore_materials, shapekey, uv) for o in objects]
        objects = [o for o in snapshots if o is not None]
        if not len(objects): return False
        for ob in objects:
            collection.objects.link(ob)
    
    for o in bpy.data.objects:
        if o.name not in context.view_layer.objects: continue
        o.hide_set(o not in objects)
        o.select_set(o in objects)    
    context.view_layer.objects.active = objects[0]
    bpy.ops.wm.obj_export( \
        filepath=filepath, \
        check_existing=False, \
        export_animation=False,
        forward_axis='NEGATIVE_Z',
        up_axis='Y',
        global_scale=1,
        apply_modifiers=True,
        export_eval_mode='DAG_EVAL_VIEWPORT',
        export_selected_objects=True,
        export_uv=True,
        export_normals=True,
        export_colors=True,
        export_materials=False,
        export_pbr_extensions=False,
        path_mode='AUTO',
        export_triangulated_mesh=type == "HIGH",
        export_curves_as_nurbs=False,
        export_object_groups=False,
        export_material_groups=False,
        export_vertex_groups=False,
        export_smooth_groups=False,
        smooth_group_bitflags=False
    )

    for multires, level in multires_mods.items() :
        multires.levels = level
    
    #スナップショットメッシュの解消
    if is_snapshot:
        for ob in objects:
            mesh = ob.data
            bpy.data.objects.remove(ob, do_unlink=True)
            bpy.data.meshes.remove(mesh, do_unlink=True)
    
    return True

def setup_xnormal(op:Operator, conf:SettingItem, export_dir, mesh_dir):
    app_conf = get_prefs()

    export_path, highpoly_path, lowpoly_path = get_directories(export_dir, mesh_dir)
    xml_file =  open(os.path.join(export_path, conf.name) + '.xml', 'w')

    settings_element = Element("Settings")
    settings_element.set('Version', '3.19.2')
    
    image_output = os.path.join(realpath(export_path), conf.name) + app_conf.img_format

    highpoly_element = SubElement(settings_element, 'HighPolyModel')
    highpoly_element.set('DefaultMeshScale', '1.000000')
    
    for highpoly in conf.highpoly :
        obj = highpoly.object
        if obj is None:
            op.report({'WARNING'}, "Highpoly object not found!")
            continue

        filepath = os.path.join(highpoly_path, obj.name + '.obj')
        export = True
        if not os.path.exists(filepath) or highpoly.export:
            export = export_obj(bpy.context, [highpoly.object], filepath, 'HIGH', [], None)
        
        if export:
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

    ignore_materials = [m.material for m in conf.materials if not m.export]
    
    for lowpoly in lowpolies :
        obj = lowpoly.object
        if obj is None:
            op.report({'WARNING'}, "Lowpoly object not found!")
            continue

        cage_opt:xNormal_CageSettings = lowpoly.cage
        cage_enabled = cage_opt.enabled
        if cage_opt.enabled:
            cage_filepath = os.path.join(lowpoly_path, obj.name + '_Cage.obj')
            if cage_opt.type == cage_type[0][0]: #OBJECT
                cage_enabled = cage_opt.object is not None
                if cage_enabled:
                    export_obj(bpy.context, [cage_opt.object], cage_filepath, 'LOW', [], None)
                else :
                    op.report({'WARNING'}, "Cage object not found! %s" % obj.name)
            elif cage_opt.type == cage_type[1][0]: #FILE
                cage_filepath = cage_opt.cage_file
                cage_enabled = os.path.exists(cage_filepath)
                if not cage_enabled:
                    op.report({'WARNING'}, "Cage file not found! %s" % obj.name)
            elif cage_opt.type == cage_type[2][0]: #SHAPEKEY
                cage_enabled = cage_opt.shape_key and obj.data.shape_keys is not None and cage_opt.shape_key in obj.data.shape_keys.key_blocks
                if cage_enabled:
                    export_obj(bpy.context, [obj], cage_filepath, 'LOW', ignore_materials, cage_opt.shape_key)
                else :
                    op.report({'WARNING'}, "Cage shape key not found! %s" % obj.name)
                
        export = True
        filepath = os.path.join(lowpoly_path, obj.name + '.obj')
        if not os.path.exists(filepath) or lowpoly.export :
            export = export_obj(bpy.context, [obj], filepath, 'LOW', ignore_materials, cage_opt.shape_key, lowpoly.uv)

        if export:
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
    
    unlink_xnormal_collection()

    for rendermap in properties.maps():
        rendermap.write(conf, settings_element)

    element_str = tostring(settings_element, 'utf-8')
    with xml_file as f :
        f.write(minidom.parseString(element_str).toprettyxml(indent="  "))
