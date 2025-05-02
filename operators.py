from .xnormal_xml import realpath, setup_xnormal
import bpy, os, subprocess
from bpy.types import Operator, Object
from bpy.props import *
from winreg import *

from .preferences import get_prefs

from .xnormal_xml import get_export_root
from .enums import *
from .uilist import *
from . import properties
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

    def export(self, context:Context, export_path:str, mesh_path:str, conf:SettingItem, wait = False):
        proj_name = conf.name
        app_conf = get_prefs()
        xml_file =  os.path.join(export_path, proj_name) + '.xml'
        
        active_object = context.view_layer.objects.active
        obj_states:dict[Object, tuple[bool, bool]] = {}
        for o in bpy.context.scene.objects:
            obj_states[o] = o.select_get(), o.hide_get()
            
        setup_xnormal(self, conf, export_path, mesh_path)
        
        for ob, (selected, hided) in obj_states.items():
            ob.select_set(selected)
            ob.hide_set(hided)
        context.view_layer.objects.active = active_object

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
        self.export(context, export_path, get_export_root(), conf, wait = True)

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
        self.export(context, export_path, export_path, conf, wait = False)   

        return {'FINISHED'}
