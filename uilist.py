import bpy
from bpy.types import UIList, Operator, Context, UILayout
from bpy.props import IntProperty, StringProperty, BoolProperty

from .settings import xNormal_CageSettings
from .xml_util import *
from .enums import cage_type

class XNORMAL_UL_SettingList(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.prop(item,'name', icon='SCENE',text='', emboss=False)


class XNORMAL_UL_HighpolyList(UIList):
    def draw_item(self, context:Context, layout:UILayout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            col = layout.column()
            row = col.row(align=True)
            obj = item.object

            row.prop(item, 'show_expands', icon='DISCLOSURE_TRI_DOWN' if item.show_expands else 'DISCLOSURE_TRI_RIGHT', text='', emboss=False)
            
            if obj is None:
                row.label(text="Object Missing!", icon='ERROR')
            else:
                row.label(text = item.object.name, icon="OBJECT_DATA")
                row.scale_x = 0.2
                row.prop(item, 'group', emboss=False, text='')
                
                row.scale_x = 1.0
                row.prop(item, 'export', icon='EXPORT', text='')

                multires = [m for m in obj.modifiers if m.type == 'MULTIRES']
                if len(multires) :
                    row.label(text="", icon='MOD_MULTIRES')

            if item.show_expands:
                col.prop(item, 'object', text="", icon="OBJECT_DATA")

                multires_mods = [m for m in obj.modifiers if m.type == 'MULTIRES']
                if len(multires_mods):
                    row.prop(item, 'multires')

                row = col.row()
                row.prop(item, 'ignore_vcolor', text = 'Ignore per-vertex colors')
                
                row = col.row()
                row.prop(item, 'mesh_scale')
                row.prop(item, 'normalsmoothing')
            
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="")


class XNORMAL_UL_LowpolyList(UIList):
    def draw_item(self, context:Context, layout, data, item, icon, active_data, active_propname, index):
        scene = context.scene
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            col = layout.column()
            col.alignment = 'RIGHT'
            row = col.row(align=True)
            obj = item.object
            
            row.prop(item,'show_expands',icon='DISCLOSURE_TRI_DOWN' if item.show_expands else 'DISCLOSURE_TRI_RIGHT',text='',emboss=False)
            
            if obj is None:
                row.label(text="Object Missing!", icon='ERROR')
                return
            elif obj.type != 'MESH':
                row.label(text="Object is not Mesh!", icon='ERROR')
                return
            else:
                row.label(text=item.object.name, icon="OBJECT_DATA")
                row.prop(item, 'export', icon='EXPORT', text='')

            if item.cage.enabled :
                row.label(text="", icon='MOD_SUBSURF')
            if item.show_expands :
                cage_opt:xNormal_CageSettings = item.cage
                split = col.split(factor=0.9, align=False)
                column = split.column(align=False)
                column.prop(item, 'object', text="", icon="OBJECT_DATA")
                
                row = column.row()
                row.prop(item, 'batch')
                
                row = column.row()
                row.prop(item, 'match_uvs')
                row.prop(item, 'normals_override', text = 'High poly normals override')
                
                row = column.row()
                row.prop(cage_opt, 'enabled')
                if cage_opt.enabled:
                    row.prop(cage_opt, 'type', text = "Use external cage file")
                    row = column.row()
                    if cage_opt.type == cage_type[0][0]: #OBJECT
                        row.prop_search(cage_opt, 'object', scene,'objects', icon = "OBJECT_DATA")
                    elif cage_opt.type == cage_type[1][0]: #FILE
                        row.prop(cage_opt, 'cage_file', text = "Cage file")
                    else : #SHAPEKEY
                        if obj.data.shape_keys is None or len(obj.data.shape_keys.key_blocks) == 0:
                            row.label(text='No shape keys', icon='ERROR')
                        else :
                            row.prop_search(cage_opt, 'shape_key', obj.data.shape_keys, 'key_blocks', icon = "SHAPEKEY_DATA")
                        
                row = column.row(align=True)
                row.prop(item, 'max_front_ray')
                row.prop(item, 'max_rear_ray')
                
                row = column.row(align=True)
                row.prop(item, 'U_offset')
                row.prop(item, 'V_offset')
                
                row = column.row()
                row.prop(item, 'mesh_scale')
                row.prop(item, 'normalsmoothing')

        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="")


class UIListOperator():
    bl_options = {'UNDO','INTERNAL'}
    @classmethod
    def poll(cls, context):
        return True

class XNORMAL_OT_AddHighpoly(Operator, UIListOperator):
    bl_idname = "xnormal.add_highpoly"
    bl_label = "Add HighpolyModel"
    def execute(self, context):
        conf = context.scene.xnormal_settings
        item = conf.settings[conf.active_index]
        group_max = max([h.group for h in item.highpoly] + [0])
        exists = [h.object for h in item.highpoly]
        index = 1
        for obj in context.selected_objects :
            if obj in exists: continue
            highpoly = item.highpoly.add()
            highpoly.object = obj
            highpoly.group = group_max + index
            index+=1
        return {'FINISHED'}

class XNORMAL_OT_RemoveHighpoly(Operator, UIListOperator):
    bl_idname = "xnormal.remove_highpoly"
    bl_label = "Remove HighpolyModel"
    def execute(self, context):
        conf = context.scene.xnormal_settings
        item = conf.settings[conf.active_index]
        item.highpoly.remove(item.active_highpoly_index)
        return {'FINISHED'}


class XNORMAL_OT_AddLowpoly(Operator, UIListOperator):
    bl_idname = "xnormal.add_lowpoly"
    bl_label = "Add LowpolyModel"
    def execute(self, context):
        conf = context.scene.xnormal_settings
        item = conf.settings[conf.active_index]
        exists = [h.object for h in item.lowpoly]
        for obj in context.selected_objects :
            if obj.type != 'MESH' or obj in exists : continue
            lowpoly = item.lowpoly.add()
            lowpoly.object = obj
        return {'FINISHED'}

class XNORMAL_OT_RemoveLowpoly(Operator, UIListOperator):
    bl_idname = "xnormal.remove_lowpoly"
    bl_label = "Remove LowpolyModel"
    def execute(self, context):
        conf = context.scene.xnormal_settings
        item = conf.settings[conf.active_index]
        item.lowpoly.remove(item.active_lowpoly_index)
        return {'FINISHED'}


class XNORMAL_OT_AddSetting(Operator, UIListOperator):
    bl_idname = "xnormal.add_setting"
    bl_label = "Add Setting"    
    def execute(self, context):
        conf = context.scene.xnormal_settings
        conf.settings.add()
        return {'FINISHED'}

class XNORMAL_OT_RemoveSetting(Operator, UIListOperator):
    bl_idname = "xnormal.remove_setting"
    bl_label = "Add Setting"
    def execute(self, context):
        layout = self.layout
        conf = context.scene.xnormal_settings
        conf.settings.remove(conf.active_index)
        return {'FINISHED'}

class XNORMAL_OT_ToggleMaterial(Operator):
    bl_options = {'UNDO','INTERNAL'}
    bl_idname = "xnormal.toggle_material"
    bl_label = "Toggle Material"
    index: IntProperty(name="Index", min=0)
    material: StringProperty()
    active: BoolProperty()
    
    @classmethod
    def poll(cls,context):
        return True
    
    def execute(self, context):
        mat = bpy.data.materials[self.material]
        confs = context.scene.xnormal_settings
        conf = confs.settings[self.index]
        mat_opt = next(iter([m for m in conf.materials if m.material == mat]), None) or conf.materials.add()
        mat_opt.material = mat
        mat_opt.export = self.active
        return {'FINISHED'}
