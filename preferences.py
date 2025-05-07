import bpy
from . import __name__ as addon_name
        
def get_prefs():
    return bpy.context.preferences.addons[addon_name].preferences