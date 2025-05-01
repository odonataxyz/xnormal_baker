from .xnormal_xml import realpath, write_xml
import bpy, os, subprocess
from bpy.types import Operator, Object, MultiresModifier
from bpy.props import *
from winreg import *

from .preferences import get_prefs

from .xnormal_xml import get_export_root
from .enums import *
from .uilist import *
from . import properties
from .utils import xnormal_collection, unlink_xnormal_collection, snapshot_mesh
from .settings import SettingItem

class XNORMAL_OT_OpenDirectory(Operator):
    bl_idname = "directory.open"
    bl_label = "Open Directory"
    bl_description = "Open Direcotry"
    bl_options = {"REGISTER"}
    filepath: StringProperty(name = "DirectoryPath", subtype="DIR_PATH")
    
    def execute(self, context):
        if os.path.exists(self.filepath):
            subprocess.Popen('explorer "' + self.filepath +'"')
        return {"FINISHED"}


class ExportOperation():
    @classmethod
    def poll(cls,context):
        app_conf = get_prefs()
        confs = context.scene.xnormal_settings
        return bpy.data.filepath and os.path.exists(app_conf.execute_path) and len(confs.settings) >= confs.active_index

    def export(self, context:Context, export_path:str, conf:SettingItem, wait = False):
        proj_name = conf.name
        app_conf = get_prefs()
        xml_file =  os.path.join(export_path, proj_name) + '.xml'
        export_objects = write_xml(self, conf, open(xml_file, 'w'), export_dir = export_path)

        #一時コレクション
        collection = xnormal_collection()
        
        active_object = context.view_layer.objects.active
        obj_states:dict[Object, tuple[bool, bool]] = {}
        for o in bpy.data.objects:
            if o.name not in context.view_layer.objects: continue
            obj_states[o] = o.select_get(), o.hide_get()

        for objects, filepath, type, shapekey in export_objects:

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
                    if type == "LOW":
                        modifier.levels = 0
                    elif type == "HIGH":
                        modifier.levels = modifier.total_levels
            
            if is_snapshot:
                objects = [snapshot_mesh(context, o, [m.material for m in conf.materials if not m.export], shapekey, 1.0) for o in objects]
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
        
        for ob, (selected, hided) in obj_states.items():
            ob.select_set(selected)
            ob.hide_set(hided)
        
        context.view_layer.objects.active = active_object
        unlink_xnormal_collection()

        xN_exe = os.path.join(realpath(app_conf.execute_path), 'xNormal.exe')
        args = (xN_exe, xml_file)
        try:
            proc = subprocess.Popen(args, bufsize=-1, cwd=export_path, shell=False)
            if wait: proc.wait()
        except PermissionError:
            print("Darn. Couldn't open xNormal. Check permissions and/or xNormal path.")


class XNORMAL_OT_Sample(Operator, ExportOperation):
    bl_idname = "xnormal.sample"
    bl_label = "xNormal Sample Bake"
    bl_description = ""
    bl_options = {'REGISTER'}
    index: IntProperty()
    map: EnumProperty(items=properties.get_bake_maps)
    
    @classmethod
    def poll(cls,context):
        app_conf = get_prefs()
        confs = context.scene.xnormal_settings
        return os.path.exists(app_conf.execute_path) and len(confs.settings) >= confs.active_index

    
    def execute(self, context:Context):
        conf = context.scene.xnormal_settings.settings[self.index]
        app_conf = get_prefs()
        proj_name = conf.name
        
        map_gen = {}
        for map in properties.maps() :
            map_gen[map.__name__] = getattr(getattr(conf.maps,map.__name__), map.id)
            setattr(getattr(conf.maps, map.__name__), map.id, map.__name__ == self.map)

        width, height = conf.image.width, conf.image.height
        aspect = int(width) / int(height)
        
        conf.image.width, conf.image.height = app_conf.sample_size, str(int(int(app_conf.sample_size) / aspect))
        
        export_path = bpy.app.tempdir

        self.export(context, export_path, conf, wait = True)

        for map in properties.maps() :
            if map.__name__ == self.map :
                image_path = os.path.join(export_path,'%s_%s%s' % (proj_name, map.name, app_conf.img_format))
                if os.path.exists(image_path):
                    subprocess.Popen([image_path],shell=True)

        conf.image.width, conf.image.height = width, height
        for map in properties.maps() :
            setattr(getattr(conf.maps,map.__name__), map.id, map_gen[map.__name__])
        return {'FINISHED'}


class XNORMAL_OT_Export_xNormal(Operator, ExportOperation):
    bl_idname = "xnormal.export"
    bl_label = "Bake xNormal"
    bl_description = "Export selected objects to xNormal."
    bl_options = {'REGISTER'}
    index: IntProperty()
    def execute(self, context:Context):
        conf = context.scene.xnormal_settings.settings[self.index]

        export_path = get_export_root()
        self.export(context, export_path, conf, wait = False)   

        return {'FINISHED'}
