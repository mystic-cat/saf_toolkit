bl_info = {
    "name": "SAF Toolkit",
    "author": "Your Name",
    "version": (1, 6, 8),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > SAF Toolkit",
    "description": "Automates hierarchy cleanup, GLTF export, JSON updating, and model importing for SAF.",
    "category": "Animation",
}

import bpy

if "bpy" in locals():
    import importlib
    if "utils" in locals():
        importlib.reload(utils)
    if "operators" in locals():
        importlib.reload(operators)
    if "ui" in locals():
        importlib.reload(ui)

from . import utils
from . import operators
from . import ui

classes = (
    operators.SAF_OT_ImportModel,
    operators.SAF_OT_CleanAndExport,
    operators.SAF_OT_GenerateJSON,
    operators.SAF_OT_OpenExportFolder,
    operators.SAF_OT_OpenSkeletonsFolder,
    ui.SAF_PT_Panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
    bpy.types.Scene.saf_selected_race = bpy.props.EnumProperty(
        name="Race",
        description="Select the Race category folder from the plugin templates directory",
        items=utils.get_race_items
    )
    
    bpy.types.Scene.saf_selected_subfolder = bpy.props.EnumProperty(
        name="Variant",
        description="Select the sub-variant (e.g., Male/Female)",
        items=utils.get_subfolder_items
    )
    
    bpy.types.Scene.saf_selected_model = bpy.props.EnumProperty(
        name="Model",
        description="Select the specific .gltf skeleton/mesh to import into the scene",
        items=utils.get_model_items
    )

    bpy.types.Scene.saf_export_target = bpy.props.EnumProperty(
        name="Target Actor",
        description="Select the top-level 'Root' object in your scene that you want to export. (Must be an object with no parent)",
        items=utils.get_scene_root_objects
    )

    bpy.types.Scene.saf_custom_export_path = bpy.props.StringProperty(
        name="Export Path",
        description="Leave blank to export to the .blend file's directory, or click the folder icon to select a specific path",
        default="",
        subtype='DIR_PATH' 
    )

    bpy.types.Scene.saf_export_filename = bpy.props.StringProperty(
        name="GLTF Name",
        description="Type the desired name for your exported animation file (e.g., X_HeatleechNursing1)",
        default="MyAnimation"
    )
    
    bpy.types.Scene.saf_json_dropdown = bpy.props.EnumProperty(
        name="Dictionary",
        description="Select a Race Dictionary from the skeletons folder",
        items=utils.get_skeleton_items
    )
    
    bpy.types.Scene.saf_json_filename = bpy.props.StringProperty(
        name="New Name",
        description="Type the name of the new Race Dictionary to create. It will be saved directly into the plugin's 'skeletons' folder.",
        default="NewRaceName"
    )

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        
    del bpy.types.Scene.saf_custom_export_path
    del bpy.types.Scene.saf_export_filename
    del bpy.types.Scene.saf_json_filename
    del bpy.types.Scene.saf_json_dropdown
    del bpy.types.Scene.saf_selected_race
    del bpy.types.Scene.saf_selected_subfolder
    del bpy.types.Scene.saf_selected_model
    del bpy.types.Scene.saf_export_target

if __name__ == "__main__":
    register()