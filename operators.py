import bpy
import os
import re
from . import utils

class SAF_OT_ImportModel(bpy.types.Operator):
    bl_idname = "saf.import_model"
    bl_label = "Import Selected Model"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        race = context.scene.saf_selected_race
        subfolder = context.scene.saf_selected_subfolder
        filename = context.scene.saf_selected_model
        
        if race == "NONE" or filename == "NONE":
            self.report({'WARNING'}, "Please select a valid Race and Model.")
            return {'CANCELLED'}

        target_dir = os.path.join(utils.get_templates_dir(), race)
        
        if subfolder and subfolder != "NONE" and os.path.isdir(os.path.join(target_dir, subfolder)):
            target_dir = os.path.join(target_dir, subfolder)
            
        filepath = os.path.join(target_dir, filename)
        
        if not os.path.exists(filepath):
            self.report({'ERROR'}, f"Could not find {filepath}")
            return {'CANCELLED'}

        bpy.ops.import_scene.gltf(
            filepath=filepath,
            guess_original_bind_pose=False,
            bone_heuristic='BLENDER'
        )
        
        for obj in context.selected_objects:
            if obj.type == 'ARMATURE':
                obj.data.display_type = 'OCTAHEDRAL'
                obj.show_in_front = True
        
        self.report({'INFO'}, f"Imported {filename} successfully.")
        return {'FINISHED'}


class SAF_OT_CleanAndExport(bpy.types.Operator):
    bl_idname = "saf.clean_and_export"
    bl_label = "Clean Actor & Export GLTF"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        target_name = context.scene.saf_export_target
        if target_name == "NONE" or target_name not in context.scene.objects:
            self.report({'WARNING'}, "Please select a valid Target Actor from the dropdown.")
            return {'CANCELLED'}

        top_root = context.scene.objects[target_name]

        if not bpy.data.filepath:
            self.report({'WARNING'}, "Please save your .blend file first to establish an export directory.")
            return {'CANCELLED'}

        custom_name = context.scene.saf_export_filename.strip()
        if not custom_name:
            self.report({'WARNING'}, "Please type a GLTF file name before exporting!")
            return {'CANCELLED'}

        if custom_name.lower().endswith(".gltf"):
            custom_name = custom_name[:-5]

        if context.active_object and context.active_object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
            
        for obj in context.view_layer.objects:
            obj.select_set(False)

        # 1. Prep Hierarchy
        utils.prepare_and_select_hierarchy(top_root)
        armature = utils.find_armature_in_hierarchy(top_root)
        
        # 2. Map Hierarchy
        hierarchy_objs = set()
        def get_hierarchy(obj):
            hierarchy_objs.add(obj)
            for child in obj.children:
                get_hierarchy(child)
        get_hierarchy(top_root)

        export_dir = os.path.dirname(bpy.data.filepath)
        export_path = os.path.join(export_dir, f"{custom_name}.gltf")
        export_result = {'CANCELLED'}

        PREFIX = "SAF_TMP_"
        renamed_others = []
        hierarchy_renamed = []

        def clean_name(name_str):
            # Safely strips .001, .002, .099, etc. from anywhere in the string
            return re.sub(r'\.\d+', '', name_str)

        try:
            # --- PHASE A: FREE UP THE NAMESPACE ---
            for obj in bpy.data.objects:
                if obj not in hierarchy_objs:
                    try:
                        renamed_others.append((obj, obj.name))
                        obj.name = PREFIX + obj.name
                    except Exception:
                        pass
                    if obj.data and not obj.data.name.startswith(PREFIX):
                        try:
                            renamed_others.append((obj.data, obj.data.name))
                            obj.data.name = PREFIX + obj.data.name
                        except Exception:
                            pass
            
            hierarchy_actions = set()
            for obj in hierarchy_objs:
                if obj.animation_data and obj.animation_data.action:
                    hierarchy_actions.add(obj.animation_data.action)
                    
            for act in bpy.data.actions:
                if act not in hierarchy_actions:
                    try:
                        renamed_others.append((act, act.name))
                        act.name = PREFIX + act.name
                    except Exception:
                        pass

            # --- PHASE B: PURIFY OUR EXPORT ACTOR ---
            def apply_clean(item, force_root=False):
                if item and hasattr(item, 'name'):
                    old_name = item.name
                    # --- FIX: Only force the literal top object to be "Root" ---
                    new_name = "Root" if force_root else clean_name(old_name)
                    
                    if old_name != new_name:
                        hierarchy_renamed.append((item, old_name))
                        try:
                            item.name = new_name
                        except Exception:
                            pass

            for obj in hierarchy_objs:
                # Force "Root" exclusively on the top_root object
                apply_clean(obj, force_root=(obj == top_root))
                
                # Everything else just gets the numbers stripped off
                apply_clean(obj.data)
                
                if obj.type == 'ARMATURE':
                    for bone in obj.data.bones:
                        apply_clean(bone)
                        
                if obj.animation_data and obj.animation_data.action:
                    apply_clean(obj.animation_data.action)

            # --- PHASE C: RUN THE EXPORT ---
            if armature:
                context.view_layer.objects.active = armature
            else:
                context.view_layer.objects.active = top_root
                
            bpy.context.view_layer.update()

            export_result = bpy.ops.export_scene.gltf(
                filepath=export_path,
                export_format='GLTF_EMBEDDED',
                use_selection=True,
                export_yup=True,
                export_apply=False,
                export_texcoords=False,
                export_normals=False,
                export_tangents=False,
                export_colors=False,
                export_materials='NONE',
                export_morph=False, 
                export_skins=False, 
                export_animations=True,
                export_animation_mode='ACTIONS',  
                export_force_sampling=True,
                export_reset_pose_bones=True,
                export_optimize_animation_size=False,
                export_nla_strips=False
            )

        finally:
            # --- PHASE D: THE MAGIC REVERT ---
            for item, old_name in reversed(hierarchy_renamed):
                try:
                    item.name = old_name
                except Exception:
                    pass
            
            for item, old_name in reversed(renamed_others):
                try:
                    item.name = old_name
                except Exception:
                    pass

        if 'FINISHED' not in export_result:
            self.report({'ERROR'}, "Blender's GLTF exporter failed internally.")
            return {'CANCELLED'}

        if not os.path.exists(export_path):
            self.report({'ERROR'}, f"Blender claimed it exported, but no file was found at {export_path}")
            return {'CANCELLED'}

        self.report({'INFO'}, f"Successfully cleaned and exported GLTF to {export_path}")
        return {'FINISHED'}


class SAF_OT_GenerateJSON(bpy.types.Operator):
    bl_idname = "saf.generate_json"
    bl_label = "Update Master JSON"
    bl_options = {'REGISTER'}

    def execute(self, context):
        target_name = context.scene.saf_export_target
        if target_name == "NONE" or target_name not in context.scene.objects:
            self.report({'WARNING'}, "Please select a valid Target Actor from the dropdown.")
            return {'CANCELLED'}

        top_root = context.scene.objects[target_name]

        if context.scene.saf_json_dropdown == "CREATE_NEW":
            custom_json_name = context.scene.saf_json_filename.strip()
            if not custom_json_name:
                self.report({'WARNING'}, "Please type a new Race name in the box!")
                return {'CANCELLED'}
        else:
            custom_json_name = context.scene.saf_json_dropdown

        if custom_json_name.lower().endswith(".json"):
            custom_json_name = custom_json_name[:-5]

        armature = utils.find_armature_in_hierarchy(top_root)

        if not armature:
            self.report({'WARNING'}, "No Armature found in this hierarchy!")
            return {'CANCELLED'}

        current_bones = [bone.name for bone in armature.data.bones]
        master_bones = []
        
        export_dir = utils.get_skeletons_dir()
        export_path = os.path.join(export_dir, f"{custom_json_name}.json")

        if os.path.exists(export_path):
            try:
                with open(export_path, 'r') as json_file:
                    existing_data = json.load(json_file)
                    if "nodes" in existing_data:
                        master_bones = existing_data["nodes"]
            except Exception as e:
                self.report({'ERROR'}, f"Failed to read existing JSON: {e}")
                return {'CANCELLED'}

        added_count = 0
        for bone in current_bones:
            if bone not in master_bones:
                master_bones.append(bone)
                added_count += 1

        if "COM" in master_bones:
            master_bones.remove("COM")
            master_bones.insert(0, "COM")
        if "Root_" in master_bones:
            master_bones.remove("Root_")
            master_bones.insert(0, "Root_")

        saf_data = {"nodes": master_bones}
        with open(export_path, 'w') as json_file:
            json.dump(saf_data, json_file, indent="\t")

        if added_count > 0:
            self.report({'INFO'}, f"Success! Added {added_count} new bones to {custom_json_name}.json")
        else:
            self.report({'INFO'}, f"No new bones found. {custom_json_name}.json is already up to date!")
            
        return {'FINISHED'}


# --- NEW: OPEN FOLDER OPERATORS ---

class SAF_OT_OpenExportFolder(bpy.types.Operator):
    """Opens your OS file explorer to the directory where this .blend file is saved"""
    bl_idname = "saf.open_export_folder"
    bl_label = "Open Export Folder"

    def execute(self, context):
        if not bpy.data.filepath:
            self.report({'WARNING'}, "Please save your .blend file first so Blender knows where it is!")
            return {'CANCELLED'}
        
        export_dir = os.path.dirname(bpy.data.filepath)
        bpy.ops.wm.path_open(filepath=export_dir)
        return {'FINISHED'}


class SAF_OT_OpenSkeletonsFolder(bpy.types.Operator):
    """Opens your OS file explorer to the plugin's skeletons dictionary folder"""
    bl_idname = "saf.open_skeletons_folder"
    bl_label = "Open Skeletons Folder"

    def execute(self, context):
        skel_dir = utils.get_skeletons_dir()
        bpy.ops.wm.path_open(filepath=skel_dir)
        return {'FINISHED'}