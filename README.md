SAF Toolkit (Starfield Animation Framework)
A Blender 3.6 add-on designed to streamline the animation creation pipeline for the Starfield Animation Framework (SAF/NAF). This toolkit automates hierarchy cleanup, prevents namespace collisions, handles strict .gltf export parameters, and manages your master bone dictionary JSONs—all without destructively modifying your working .blend file.

 Key Features
Non-Destructive Namespace Cleanup: Blender strictly enforces unique names, often appending .001 to duplicated bones or actions. This plugin temporarily clears the global namespace, strips the .001 numbers from your target export, forces the top node to "Root", runs the export, and reverts everything back in milliseconds. Your Blender scene stays exactly how you organized it, but SAF gets the pristine naming it requires.

One-Click NAF Export: Automatically exports using the exact glTF 2.0 parameters required by NAF (Embedded, Active Actions, correct sampling, no meshes).

Smart Hierarchy Detection: Automatically detects whether your top root is an Empty or an Armature and ensures the correct object is active so IK constraints and keyframes bake correctly.

JSON Dictionary Manager: Instantly append newly created bones from your rig into your master Race JSON dictionary.

Model Importer: Quickly spawn base race models and skeletons directly from your templates folder.

 Installation
Download the latest release of the SAF Toolkit (usually a .zip file).

Open Blender 3.6.

Go to Edit > Preferences > Add-ons.

Click Install... and select the downloaded .zip file.

Check the box next to Animation: SAF Toolkit to enable it.

The toolkit will appear in the 3D Viewport Sidebar (press N to open) under the SAF Toolkit tab.

 Usage Guide
1. Model Importer
Quickly bring base .gltf skeletons into your scene to start animating.

Race: Select the base race folder.

Variant: Select the subfolder (e.g., Male / Female).

Model: Select the specific .gltf file to import.

Click Import Selected Model.

Note: Skeletons import with their bone display type automatically set to 'Octahedral' and 'In Front' so you can immediately see the rig.

[Screenshot of the Model Importer section in the Blender UI]

2. Export Animation
Exporting animations for Starfield requires pristine naming conventions. If an action or bone has .001 attached to it, the SAF in-game hooks will fail.

Ensure your .blend file is saved (the plugin exports to the same directory).

Select your Target Actor from the dropdown. This should be the absolute top-level parent of your hierarchy (e.g., HeatleechRoot or HumanRoot).

Type your desired File Name (e.g., Heatleech_Attack_01).

Click Clean Actor & Export GLTF.

What happens under the hood?
The plugin safely hides the rest of your scene, removes any .001 suffixes from your target's bones and action tracks, renames the top node to "Root", runs the Starfield-compliant GLTF export, and then reverts your Blender scene back to normal. You can safely have multiple actors in the same scene without Blender fighting your naming conventions!

[Screenshot of the Export Animation section in the Blender UI]
[Screenshot showing a clean, exported GLTF hierarchy side-by-side with a messy Blender Outliner to show the plugin's cleanup magic]

3. Dictionary Manager
SAF requires a master .json file that registers every possible bone for a specific race so the engine knows how to hook into them.

Ensure your Target Actor is selected in the Export panel.

Under the Dictionary dropdown, select an existing Race Dictionary or choose -- Create New --.

If creating a new one, type the name in the New Name field.

Click Update Master JSON.

The plugin will scan your active Armature, compare its bones against the JSON, and append any missing bones. It also automatically ensures that "Root_" and "COM" are placed at the very top of the dictionary.

[Screenshot of the Dictionary Manager section in the Blender UI]

 Folder Structure Setup
For the Model Importer and Dictionary Manager to function properly, your plugin folder must contain the following subdirectories:

templates/ - Place your base .gltf skeletons here. Organize them by RaceName/SubVariant/model.gltf (e.g., templates/Human/Male/human_base.gltf).

skeletons/ - This is where your generated .json master dictionaries are saved and read from.

(You can quickly open these directories via your OS file explorer by clicking the folder icons in the plugin UI!)

 Important Notes
Blender Version: This plugin was built and tested on Blender 3.6. Using newer versions of Blender (4.0+) may change how the GLTF exporter handles bone data under the hood.

Animations Only: This export tool is built exclusively for exporting skeleton animation data. It automatically prevents MESH objects from being exported to keep file sizes minimal and engine-compliant.
