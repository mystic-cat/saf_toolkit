import bpy
import re
import os

def get_templates_dir():
    return os.path.join(os.path.dirname(__file__), "templates")

def get_skeletons_dir():
    dir_path = os.path.join(os.path.dirname(__file__), "skeletons")
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    return dir_path

def get_skeleton_items(self, context):
    items = []
    skel_dir = get_skeletons_dir()
    
    if os.path.exists(skel_dir):
        for f in os.listdir(skel_dir):
            if f.lower().endswith(".json"):
                display_name = os.path.splitext(f)[0]
                items.append((display_name, display_name, f"Update {display_name}.json"))
                
    items.append(("CREATE_NEW", "-- Create New --", "Create a new JSON dictionary"))
    return items

def get_scene_root_objects(self, context):
    items = []
    for obj in context.scene.objects:
        if obj.parent is None:
            items.append((obj.name, obj.name, f"Select {obj.name} as the export target"))
    if not items:
        items.append(("NONE", "No Roots Found", "There are no objects in the scene"))
    return items

def get_race_items(self, context):
    items = []
    temp_dir = get_templates_dir()
    if os.path.exists(temp_dir):
        for d in os.listdir(temp_dir):
            if os.path.isdir(os.path.join(temp_dir, d)):
                items.append((d, d, f"{d} Race Folder"))
    if not items:
        items.append(("NONE", "No Races Found", "Add folders to the templates directory"))
    return items

def get_subfolder_items(self, context):
    items = []
    if hasattr(context, "scene"):
        race = context.scene.saf_selected_race
        if race and race != "NONE":
            race_dir = os.path.join(get_templates_dir(), race)
            if os.path.exists(race_dir):
                for d in os.listdir(race_dir):
                    if os.path.isdir(os.path.join(race_dir, d)):
                        items.append((d, d, f"{d} Variant"))
                        
    if not items:
        items.append(("NONE", "None", ""))
    return items

def get_model_items(self, context):
    items = []
    temp_dir = get_templates_dir()
    if hasattr(context, "scene"):
        race = context.scene.saf_selected_race
        subfolder = context.scene.saf_selected_subfolder
        
        if race and race != "NONE":
            target_dir = os.path.join(temp_dir, race)
            
            if subfolder and subfolder != "NONE" and os.path.isdir(os.path.join(target_dir, subfolder)):
                target_dir = os.path.join(target_dir, subfolder)
                
            if os.path.exists(target_dir):
                for f in os.listdir(target_dir):
                    if f.lower().endswith((".gltf", ".glb")):
                        display_name = os.path.splitext(f)[0]
                        items.append((f, display_name, f"Import {display_name}"))
                        
    if not items:
        items.append(("NONE", "No Models Found", "Add .gltf files to this folder"))
    return items

def get_top_parent(obj):
    if obj.parent is None:
        return obj
    return get_top_parent(obj.parent)

def clean_name_string(name_str):
    # Removing the $ anchor ensures it strips numbers from the middle of the string (e.g. COM.001Action)
    return re.sub(r'\.\d+', '', name_str)

# Replace 'clean_name_string' and 'clean_and_select_hierarchy' with this:

def prepare_and_select_hierarchy(obj):
    """
    Recursively selects the hierarchy and skips geometry (MESH).
    We no longer manipulate animation data here, as that breaks NLA tracks and poses.
    """
    # 1. Select the object ONLY if it's not geometry
    if obj.type != 'MESH':
        obj.select_set(True)
    else:
        obj.select_set(False)

    # 2. Recurse through children
    for child in obj.children:
        prepare_and_select_hierarchy(child)

def find_armature_in_hierarchy(obj):
    if obj.type == 'ARMATURE':
        return obj
    for child in obj.children:
        result = find_armature_in_hierarchy(child)
        if result:
            return result
    return None