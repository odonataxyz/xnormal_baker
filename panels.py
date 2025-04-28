import bpy, os
from bpy.types import Panel, Object, Material
from bpy.props import *
from winreg import *

from .settings import SettingItem
from .icons import load_icon

from .preferences import get_prefs

from .operators import XNORMAL_OT_Export_xNormal, XNORMAL_OT_OpenDirectory, XNORMAL_OT_Sample
from .enums import *
from .uilist import *
from . import properties



class XNORMAL_PT_Panel(Panel):
    bl_label = "Bake - xNormal"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        confs = scene.xnormal_settings
        app_conf = get_prefs()
        
        if not confs:return

        if not os.path.exists(app_conf.execute_path):
            layout.label(text='Set the filepath of xNormal.exe from the add-on settings.', icon='ERROR')
        
        row = layout.row(align=True)
        row.scale_y = 1.5
        global icon

        loaded_icon = load_icon()

            
        row.operator(XNORMAL_OT_Export_xNormal.bl_idname, icon_value = loaded_icon.get("icon").icon_id).index = scene.xnormal_settings.active_index
        
        dirname = os.path.dirname(bpy.data.filepath)
        export_path = os.path.join(dirname, app_conf.output.replace("/", "\\"))
        row.operator(XNORMAL_OT_OpenDirectory.bl_idname, icon="FILE_FOLDER", text='').filepath = export_path

        layout.separator()
        
        setting_column = layout.column(align=True)
        row = setting_column.row(align=True)
        row.label(text="Settings:")
        row.operator(XNORMAL_OT_AddSetting.bl_idname, icon='ADD', text="")
        row.operator(XNORMAL_OT_RemoveSetting.bl_idname, icon='REMOVE', text="")

        setting_column.template_list("XNORMAL_UL_SettingList", "", scene.xnormal_settings, "settings", scene.xnormal_settings, "active_index", rows=2)

        if len(confs.settings) <= confs.active_index :
            return

        conf:SettingItem = confs.settings[confs.active_index]

        box = setting_column.box()
        row = box.row()
        row.prop(conf, 'discard_BF')
        row.prop(conf, 'closest_hit')

        box.label(text="Texture Size:")
        row = box.row(align = True)
        row.prop(conf.image, 'width', text = "")
        row.prop(conf.image, 'height', text = "")

        box.prop(conf.image, 'edge_padding', icon='BLENDER', toggle=True)
        box.prop(conf.image, 'bucket_size')
        box.prop(conf.image, 'AA_setting')
        
        lowpoly_column = box.column(align = True)
        row = lowpoly_column.row(align=True)
        row.label(text="Lowpoly:")
        row.operator(XNORMAL_OT_AddLowpoly.bl_idname, icon='ADD', text="")
        row.operator(XNORMAL_OT_RemoveLowpoly.bl_idname, icon='REMOVE', text="")
        lowpoly_box = lowpoly_column.box()
        lowpoly_box.template_list(XNORMAL_UL_LowpolyList.__name__, "", conf, "lowpoly", conf, "active_lowpoly_index", rows=2)

        highpoly_column = box.column(align=True)
        row = highpoly_column.row(align=True)
        row.label(text="Highpoly:")
        row.operator(XNORMAL_OT_AddHighpoly.bl_idname, icon='ADD', text="")
        row.operator(XNORMAL_OT_RemoveHighpoly.bl_idname, icon='REMOVE', text="")
        highpoly_box = highpoly_column.box()
        highpoly_box.template_list(XNORMAL_UL_HighpolyList.__name__, "", conf, "highpoly", conf, "active_highpoly_index", rows=2)
        
        mats:set[Material] = set()
        for lowpoly in conf.lowpoly:
            lp_obj:Object = lowpoly.object
            if lp_obj is None or lp_obj.type != 'MESH': continue
            for matslot in lp_obj.material_slots:
                if matslot.material is None: continue
                mats.add(matslot.material)
        
        if mats:
            box.label(text="Materials:")        
            materials_column = box.column(align=True)
            for mat in mats:
                row = materials_column.row()
                mat_opt = next(iter([m for m in conf.materials if m.material == mat]), None)
                matop = row.operator(XNORMAL_OT_ToggleMaterial.bl_idname, text='', icon='HIDE_OFF' if mat_opt is None or mat_opt.export else 'HIDE_ON')
                matop.index = confs.active_index
                matop.material = mat.name
                matop.active = (not mat_opt.export) if mat_opt else False
                row.label(text=mat.name, icon_value=layout.icon(mat))
        
        box.label(text='BakeMap:')
        row = box.row()
        column1 = row.column()
        column2 = row.column()
        column3 = row.column()
        for index, rendermap in enumerate(properties.maps()):
            prop = getattr(conf.maps, rendermap.__name__)
            if index % 3 == 0 :
                column = column1.column(align=True)
            elif index % 3 == 1 :
                column = column2.column(align=True)
            else :
                column = column3.column(align=True)

            column.template_icon(icon_value=loaded_icon.get(rendermap.name).icon_id, scale=3.0)
            column.prop(prop, rendermap.id)

            row = column.row()
            sample_render = row.operator(XNORMAL_OT_Sample.bl_idname, icon='FILE_IMAGE', text='', emboss=False)
            sample_render.map = rendermap.__name__
            sample_render.index = scene.xnormal_settings.active_index
            row.operator(properties.XNORMAL_OT_CallMenuRenderMap.bl_idname, icon='PREFERENCES', text='', emboss=False).map = rendermap.__name__
            column.separator()
