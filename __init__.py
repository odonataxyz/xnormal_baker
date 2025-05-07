'''
MIT License

Copyright (C) 2025 odonata

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''


bl_info = {
    "name": "xNormal Baker",
    "author": "odonata",
    "version": (1, 0, 2),
    "blender": (4, 0, 0),
    "location": "Properties > Render > Bake - xNormal",
    "description": "Texture baking with xNormal.",
    "wiki_url": "https://odonata.xyz/",
    "category": "Image"
}

import bpy
from bpy.types import PropertyGroup, AddonPreferences
from bpy.props import *
from winreg import *

from .enums import *
from .uilist import *
from . import properties
from .settings import SettingItem, xNormal_ImageSettings, xNormal_CageSettings, xNormal_LowpolySettings, xNormal_HighpolySettings, xNormal_MaterialSettings

from .operators import XNORMAL_OT_Sample, XNORMAL_OT_Export_xNormal, XNORMAL_OT_OpenDirectory
from .panels import XNORMAL_PT_Panel
from .properties import XNORMAL_OT_CallMenuRenderMap
from .uilist import XNORMAL_OT_AddHighpoly, XNORMAL_OT_AddLowpoly, XNORMAL_OT_AddSetting, XNORMAL_OT_RemoveHighpoly, XNORMAL_OT_RemoveLowpoly, XNORMAL_OT_RemoveSetting, XNORMAL_UL_HighpolyList, XNORMAL_UL_LowpolyList, XNORMAL_UL_SettingList, XNORMAL_OT_ToggleMaterial

class xNormal_Preferences(AddonPreferences):
    bl_idname = __name__
    execute_path: StringProperty(name = "Path to xNormal", description = "Path to the xNormal .exe", subtype = 'DIR_PATH')
    img_format: EnumProperty(
    items = [('.png', 'PNG', ''),
    ('.tga', 'TGA', ''), 
    ('.jpg', 'JPG', '')],
    name = "Image format",
    description = "")
    sample_size: EnumProperty(items = image_size, name = "Sample Bake Size", default = "512")
    output: StringProperty(name = "Export path", description = "Location for exporting maps", default = """./Textures/Bakes/""")
    hipoly_dir: StringProperty(name = "Hipoly path", default = "Highpoly")
    lowpoly_dir: StringProperty(name = "Lowpoly path", default = "Lowpoly")
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'execute_path')
        layout.prop(self, 'img_format')
        layout.prop(self, 'output')
        row = layout.row()
        row.prop(self, 'hipoly_dir')
        row.prop(self, 'lowpoly_dir')
        layout.prop(self, 'sample_size')

classes = [
    xNormal_Preferences,
    xNormal_ImageSettings,
    xNormal_CageSettings,
    xNormal_LowpolySettings,
    xNormal_HighpolySettings,
    xNormal_MaterialSettings,
    XNORMAL_OT_Sample,
    XNORMAL_OT_Export_xNormal,
    XNORMAL_OT_OpenDirectory,
    XNORMAL_PT_Panel,
    XNORMAL_OT_CallMenuRenderMap,
    XNORMAL_OT_AddHighpoly,
    XNORMAL_OT_AddLowpoly,
    XNORMAL_OT_AddSetting,
    XNORMAL_OT_RemoveHighpoly,
    XNORMAL_OT_RemoveLowpoly,
    XNORMAL_OT_RemoveSetting,
    XNORMAL_OT_ToggleMaterial,
    XNORMAL_UL_HighpolyList,
    XNORMAL_UL_LowpolyList,
    XNORMAL_UL_SettingList
]
    
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    class xNormal_RenderMaps(PropertyGroup):
        pass

    for rendermap in properties.maps() :
        map_name = rendermap.__name__
        bpy.utils.register_class(rendermap)
        xNormal_RenderMaps.__annotations__[map_name] = PointerProperty(type=rendermap)

    class xNormal_SettingItem(PropertyGroup, SettingItem):
        maps:PointerProperty(type=xNormal_RenderMaps)

    class xNormal_Setting(PropertyGroup):
        settings:CollectionProperty(type=xNormal_SettingItem)
        active_index:IntProperty()

    bpy.utils.register_class(xNormal_RenderMaps)
    bpy.utils.register_class(xNormal_SettingItem)
    bpy.utils.register_class(xNormal_Setting)

    bpy.types.Scene.xnormal_settings = PointerProperty(type = xNormal_Setting)

def unregister():
    del bpy.types.Scene.xnormal_settings
    for cls in classes:
        bpy.utils.unregister_class(cls)
    for rendermap in properties.maps() :
        bpy.utils.unregister_class(rendermap)

if __name__ == "__main__":
    register()
    