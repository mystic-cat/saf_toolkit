import bpy
import os
from . import utils

class SAF_PT_Panel(bpy.types.Panel):
    bl_label = "SAF Toolkit"
    bl_idname = "SAF_PT_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SAF Toolkit'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # --- IMPORT SECTION ---
        layout.label(text="Model Importer", icon='IMPORT')
        box = layout.box()
        box.prop(scene, "saf_selected_race", text="Race")
        
        race_dir = os.path.join(utils.get_templates_dir(), scene.saf_selected_race)
        has_subfolders = False
        if os.path.exists(race_dir):
            for d in os.listdir(race_dir):
                if os.path.isdir(os.path.join(race_dir, d)):
                    has_subfolders = True
                    break
                    
        if has_subfolders:
            box.prop(scene, "saf_selected_subfolder", text="Variant")
            
        box.prop(scene, "saf_selected_model", text="Model")
        box.operator("saf.import_model", text="Import Selected Model", icon='MESH_MONKEY')

        layout.separator()

        # --- EXPORT SECTION ---
        row1 = layout.row()
        row1.label(text="Export Animation", icon='EXPORT')
        row1.operator("saf.open_export_folder", text="", icon='FILE_FOLDER')
        
        box2 = layout.box()
        box2.prop(scene, "saf_export_target", text="Target")
        box2.prop(scene, "saf_custom_export_path", text="Export Path")
        box2.prop(scene, "saf_export_filename", text="File Name")
        box2.operator("saf.clean_and_export", icon='EXPORT')

        layout.separator()
        
        # --- JSON SECTION ---
        row2 = layout.row()
        row2.label(text="Dictionary Manager", icon='TEXT')
        row2.operator("saf.open_skeletons_folder", text="", icon='FILE_FOLDER')
        
        box3 = layout.box()
        box3.prop(scene, "saf_export_target", text="Target Actor")
        
        # Smart Metadata UI Logic
        target_name = scene.saf_export_target
        target_obj = scene.objects.get(target_name) if target_name != "NONE" else None
        
        # Check if it has metadata AND if the file actually exists
        has_valid_metadata = False
        if target_obj and "saf_race" in target_obj:
            expected_json = f"{target_obj['saf_race']}.json"
            expected_path = os.path.join(utils.get_skeletons_dir(), expected_json)
            if os.path.exists(expected_path):
                has_valid_metadata = True

        if has_valid_metadata:
            box3.label(text=f"Dictionary: {target_obj['saf_race']}.json", icon='LOCKED')
            box3.label(text="(Auto-Detected from Template)", icon='INFO')
        else:
            if target_obj and "saf_race" in target_obj:
                box3.label(text=f"Template: {target_obj['saf_race']} (Dict Not Found)", icon='INFO')
                
            box3.prop(scene, "saf_json_dropdown", text="Dictionary")
            if scene.saf_json_dropdown == "CREATE_NEW":
                box3.prop(scene, "saf_json_filename", text="New Name")
            
        box3.operator("saf.generate_json", icon='FILE_TICK')