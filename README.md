#  RexTools3

**RexTools3** is a collection of sub-tools for speeding up workflow in Blender.

## 🔧 Tools

### 📦 Batch Export

**Location:** `Top bar` and `Rex Tools panel> Export Manager.`

- **Instant Export**: One-click batch export.
- **Quick Config**: Global export path, per object and collection override.
- **Export Limiter**: Limit by selection, visible or render visible.
- **Export Format**: FBX, GLTF, OBJ.
- **Export Mode**: Single object, parent hierarchy, or collection.
- **Presets**: Use export presets.
- **Options saved in file**: all options are saved with blender file. So no more guessing what export settings were used.

### 🛠️ Easy PBR

**Location:** `Material Properties > Easy PBR`

A dedicated panel for rapid PBR material setup and management.

- **Texture Auto-Loader**: Load Base Color map, then user auto loader to load rest of the textures based on nameing convention.
- **Packed Texture Setup**: High-density UI in file selector for mapping R, G, B, A channels to PBR slots (e.g., ORM, RA, etc.) during manual assignment.
- **Channel Mapping**: Flexible routing of texture channels (R, G, B, A, or Full) to shader inputs.
- **Invert Maps**: Toggleable inversion for Roughness, Metallic, and AO maps.
- **Debug Preview**: Real-time visual debugging of individual texture slots or mixed shader outputs.
- **More Controls**: Easy access to strength, tint, and alpha clipping parameters.

### 🦴 Rigging Tools

Streamline bone management and constraint workflows.

**Location:** `Object Mode > Armeture Selected > RexTools3 panel`

- **Bone Batch Rename**: Batch rename bones with Find & Replace or Prefix/Suffix support. Automatically updates associated vertex groups.

**Location:** `Pose Mode > RexTools3 panel`

- **Chain Constraints Adder**: Quickly add constraints (Copy Rotation, etc.) to bone chains with linear influence gradients (From/To) or fixed values. Also remove all constraints from selected bones.

### 🏷️ Naming Tools

**Location:** `Object Mode > RexTools3 panel`

- **Auto Rename High/Low**: Automatically detect and rename high-poly and low-poly pairs based on vertex counts, essential for substance painter or marmoset baking.
- **Prefix Management**: Customizable suffixes for High/Low versions.

### 🛠️ Common Tools

**Location:** ` RexTools3 panel`

- **Open Folder:** Open the saved blender folder.
- **Extract Textures**: Pack and unpack all textures to a local `textures/` directory in one go.
- **Purge Orphans:** Clean all unused data from blend file.
- **Material Replacement**: Batch replace materials across multiple selected objects.

### 🧊 Object Tools

**Location:** `Object Mode > RexTools3 panel`

* **Smart Join**: Combine objects with an option to automatically apply modifiers, also checks for possible failed uv merge due to uv naming missmatch. Replaces default Object Join Operation.

### 🧹 Cleanup Tools

**Location:** ` RexTools3 panel`

* **Clean Objects:** Clear custom split normal, remove unused mats and do tris to quad in one button.
* **Clear Seams:** Clear all seams from Mesh.
* **Clean Modifiers:** Remove hidden or all modifiers.
* **Cheker Dissolve:** Easy way to decimate evenly looped cylendrical geometries.

### 📐 UV Tools

- **Seam Tools**:

  - **Area Seam**: Mark seams around selected areas.
  - **Angle Loop Seam**: Select and mark seams along edge loops based on angle thresholds.
  - **Seam From Island/Sharp**: Generate seams from existing UV islands or sharp edges.
- **Unwrap Tools:**

  - **Live Unwrap Toggle**: Quick access to Blender's live unwrap feature.
  - **Quad Follow:** Quick button to make quad follow a 1 click thing instead of two.

### 🧪 Shader Tools

**Location:** `Shader Editor > RexTools3 panel`

- **Node Socket Inspector**: View detailed socket info (names, IDs, types) for any selected node in the Shader Editor.
- **Node Layout**: Automatically organize shader nodes into a clean, hierarchical layout. Accessible via Shader Editor context menu or the `RexTools3` sidebar.

## 📥 Installation

1. Download the latest release as a `.zip` file.
2. In Blender, go to **Edit > Preferences > Add-ons**.
3. Click **Install...** and select the downloaded `.zip` file.
4. Enable **RexTools3** from the list.

## 📋 Requirements

- Blender 4.2.0 or later.
