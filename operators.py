import bpy
import os
import re
import json
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
            # Stamp the top-level root with the Race metadata!
            if obj.parent is None:
                obj["saf_race"] = f"{race}Race"
                
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

        custom_path = context.scene.saf_custom_export_path.strip()
        
        if custom_path:
            export_dir = bpy.path.abspath(custom_path)
            if not os.path.isdir(export_dir):
                self.report({'WARNING'}, "The custom export directory does not exist!")
                return {'CANCELLED'}
        else:
            if not bpy.data.filepath:
                self.report({'WARNING'}, "Please save your .blend file first, or set a Custom Export Path.")
                return {'CANCELLED'}
            export_dir = os.path.dirname(bpy.data.filepath)

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

        utils.prepare_and_select_hierarchy(top_root)
        armature = utils.find_armature_in_hierarchy(top_root)
        
        hierarchy_objs = set()
        def get_hierarchy(obj):
            hierarchy_objs.add(obj)
            for child in obj.children:
                get_hierarchy(child)
        get_hierarchy(top_root)

        export_path = os.path.join(export_dir, f"{custom_name}.gltf")
        export_result = {'CANCELLED'}

        PREFIX = "SAF_TMP_"
        renamed_others = []
        hierarchy_renamed = []

        def clean_name(name_str):
            return re.sub(r'\.\d+', '', name_str)

        try:
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

            def apply_clean(item, force_root=False):
                if item and hasattr(item, 'name'):
                    old_name = item.name
                    new_name = "Root" if force_root else clean_name(old_name)
                    
                    if old_name != new_name:
                        hierarchy_renamed.append((item, old_name))
                        try:
                            item.name = new_name
                        except Exception:
                            pass

            for obj in hierarchy_objs:
                apply_clean(obj, force_root=(obj == top_root))
                apply_clean(obj.data)
                
                if obj.type == 'ARMATURE':
                    for bone in obj.data.bones:
                        apply_clean(bone)
                        
                if obj.animation_data and obj.animation_data.action:
                    apply_clean(obj.animation_data.action)

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

    def invoke(self, context, event):
        target_name = context.scene.saf_export_target
        if target_name == "NONE" or target_name not in context.scene.objects:
            self.report({'WARNING'}, "Please select a valid Target Actor from the dropdown.")
            return {'CANCELLED'}
            
        top_root = context.scene.objects[target_name]
        
        # If it has the stamped metadata AND the file exists, bypass the warning!
        if "saf_race" in top_root:
            expected_path = os.path.join(utils.get_skeletons_dir(), f"{top_root['saf_race']}.json")
            if os.path.exists(expected_path):
                return self.execute(context)
            
        # Otherwise, pop up the safety verification
        return context.window_manager.invoke_props_dialog(self, width=350)

    def draw(self, context):
        layout = self.layout
        target_name = context.scene.saf_export_target
        
        dict_name = context.scene.saf_json_dropdown
        if dict_name == "CREATE_NEW":
            dict_name = context.scene.saf_json_filename
            
        if dict_name.lower().endswith(".json"):
            dict_name = dict_name[:-5]
            
        layout.label(text="⚠️ UNKNOWN ACTOR ORIGIN ⚠️", icon='ERROR')
        layout.separator()
        layout.label(text=f"Extracting bones from:  {target_name}")
        layout.label(text=f"Saving into:  {dict_name}.json")
        layout.separator()
        layout.label(text="Are you sure you have the correct dictionary selected?")

    def execute(self, context):
        target_name = context.scene.saf_export_target
        if target_name == "NONE" or target_name not in context.scene.objects:
            self.report({'WARNING'}, "Please select a valid Target Actor from the dropdown.")
            return {'CANCELLED'}

        top_root = context.scene.objects[target_name]

        # Use metadata ONLY if the file exists, otherwise fallback to UI selection
        use_metadata = False
        if "saf_race" in top_root:
            expected_path = os.path.join(utils.get_skeletons_dir(), f"{top_root['saf_race']}.json")
            if os.path.exists(expected_path):
                use_metadata = True

        if use_metadata:
            custom_json_name = top_root["saf_race"]
        else:
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

        def clean_name(name_str):
            import re
            return re.sub(r'\.\d+', '', name_str)

        current_bones = []
        current_bones.append("Root_")
        
        arm_name = clean_name(armature.name)
        if arm_name not in current_bones:
            current_bones.append(arm_name)

        for bone in armature.data.bones:
            cleaned_bone = clean_name(bone.name)
            if cleaned_bone not in current_bones and cleaned_bone != "Root":
                current_bones.append(cleaned_bone)

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

        if "Root" in master_bones:
            master_bones.remove("Root")

        if arm_name in master_bones:
            master_bones.remove(arm_name)
            master_bones.insert(0, arm_name)
            
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


class SAF_OT_OpenExportFolder(bpy.types.Operator):
    """Opens your OS file explorer to the directory where the GLTF will be saved"""
    bl_idname = "saf.open_export_folder"
    bl_label = "Open Export Folder"

    def execute(self, context):
        custom_path = context.scene.saf_custom_export_path.strip()
        
        if custom_path:
            export_dir = bpy.path.abspath(custom_path)
        else:
            if not bpy.data.filepath:
                self.report({'WARNING'}, "Please save your .blend file first, or set a Custom Export Path!")
                return {'CANCELLED'}
            export_dir = os.path.dirname(bpy.data.filepath)
        
        if os.path.isdir(export_dir):
            bpy.ops.wm.path_open(filepath=export_dir)
        else:
            self.report({'WARNING'}, "The target directory does not exist yet.")
            
        return {'FINISHED'}


class SAF_OT_OpenSkeletonsFolder(bpy.types.Operator):
    """Opens your OS file explorer to the plugin's skeletons dictionary folder"""
    bl_idname = "saf.open_skeletons_folder"
    bl_label = "Open Skeletons Folder"

    def execute(self, context):
        skel_dir = utils.get_skeletons_dir()
        bpy.ops.wm.path_open(filepath=skel_dir)
        return {'FINISHED'}