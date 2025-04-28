import bpy
import os
import bpy.utils.previews

icon = None

def load_icon():
    global icon
    if icon: return icon
    icons_dir = os.path.join(os.path.dirname(__file__), "icons\\")
    files = os.listdir(icons_dir)
    icon = bpy.utils.previews.new()
    for file in files:
        if not file.endswith(".png"): continue
        icon.load(os.path.splitext(file)[0], os.path.join(icons_dir, file), 'IMAGE')
    return icon
