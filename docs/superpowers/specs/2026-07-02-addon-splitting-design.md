# Design Specification: RexTools3 Addon Splitting

This design document outlines the plan to split the monolithic `RexTools3` Blender addon into four independent, single-purpose extensions. This will resolve the coherent theme rejection issue on the Blender Extensions Platform while keeping all code in a single Git repository.

---

## 🎯 Goal
Split the addon into:
1. `rextools`: General utilities (selection, rename, cleanup, uv, rigging, animation, object tools, pie menus, Quick Blender Assets).
2. `rexport`: High-efficiency batch mesh exporter (RExport).
3. `easy_pbr`: PBR material manager, texture auto-loader, and missing texture scanner.
4. `texture_oven`: Automated high-to-low texture baker.

---

## 📁 Repository Structure & Directory Junctions

To avoid code duplication during development, all shared utilities (`core/notify.py`, `core/theme.py`, the `ui/` overlay system, and `assets/` icons) will live in a single source of truth under `/shared`.

During development, directory junctions (non-admin Windows symlinks) will mirror the shared directories into each addon folder. When packaging for release, junctions will be replaced with real copies of the files to ensure the ZIPs are fully self-contained.

```
/ (Repository Root)
  ├── shared/                     # Single source of truth for common utilities
  │     ├── core/
  │     │     ├── notify.py
  │     │     └── theme.py
  │     ├── ui/
  │     │     ├── drawing.py
  │     │     ├── elements.py
  │     │     ├── legacy.py
  │     │     ├── manager.py
  │     │     ├── overlay.py
  │     │     ├── templates.py
  │     │     └── utils.py
  │     ├── assets/
  │     │     ├── error.png
  │     │     ├── info.png
  │     │     ├── success.png
  │     │     └── warning.png
  │     └── auto_load.py          # Shared class discovery script
  │
  ├── rextools/                   # Addon 1: General Utility Tools
  ├── rexport/                    # Addon 2: RExport Batch Mesh Export
  ├── easy_pbr/                   # Addon 3: Easy PBR Material Manager
  ├── texture_oven/               # Addon 4: Texture Imposter Baker
  │
  ├── setup_dev.py                # Setup Windows Directory Junctions for dev
  ├── package.py                  # Sync and build standalone ZIP files for release
  ├── verify_addons.py            # Headless Blender registration and validation tests
  ├── README.md                   # Monorepo-wide README and installation guide
  └── .gitignore                  # Configured to ignore generated/synced files
```

---

## 📦 Addon File Mappings

### 1. `rextools` (General Utility Tools)
* **Operators:**
  - `animation_tools.py`, `keyframe_offset.py`
  - `chain_constraints_adder.py`
  - `checker_dissolve.py`, `cleanup_tools.py`, `clean_modifiers.py`
  - `context_aware_select.py`, `select_operators.py`, `select_similar_modal.py`
  - `edit_delete_ops.py`, `edit_delete_ops_custom.py`, `quick_delete_modal.py`
  - `engine_vertex_stats.py`
  - `object_auto_rename_low_high.py`, `rig_batch_rename_bones.py`, `rig_chained_bone_name.py`
  - `quick_asset_export.py` (Quick Blender Assets)
  - `rex_shading_pie.py`
  - `sculpt_operators.py`, `weight_operators.py`
  - `setup_pose_copier.py`, `smart_join.py`
  - `uv_angle_loop_seam.py`, `uv_area_seam.py`, `uv_from_sharp.py`, `uv_live_unwrap_toggle.py`, `uv_loop_seam.py`, `uv_seam_area_by_angle.py`
  - `open_folder.py`, `copy_text.py`, `debug_toasts.py`, `test_overlay.py`
* **Panels:**
  - `animation_tools.py`, `chain_constraints_panel.py`
  - `cleanup_tools.py`, `common_tools.py`
  - `edit_tools.py`, `engine_vertex_stats.py`
  - `object_tools.py`, `pose_tools.py`, `sculpt_panel.py`, `weight_tools.py`
  - `rename_tools.py`, `quick_asset_export.py`
  - `top_bar.py` (modified to list rextools utilities only)
  - `uv_mesh_tools.py`, `uv_tools.py`
  - `node_helper_panel.py`
* **Root Files:**
  - `menu.py` (registers UV viewport menu hook)

### 2. `rexport` (Batch Exporter)
* **Operators:**
  - `export_operators.py`
* **Panels:**
  - `export_panel.py`
* **Core File:**
  - `core/fbx_utils.py` (FBX exporter patch)

### 3. `easy_pbr` (PBR & Material Tools)
* **Operators:**
  - `pbr_assign.py`, `pbr_batch.py`, `pbr_create.py`, `pbr_debug.py`, `pbr_layout.py`, `pbr_remove.py`, `pbr_rename_textures.py`, `pbr_reset_tint.py`, `pbr_save_textures.py`, `pbr_viewport_color.py`
  - `extract_textures.py`, `missing_textures.py`, `material_tools.py`
* **Panels:**
  - `pbr_panel.py`
  - `batch_material_panel.py`

### 4. `texture_oven` (Mesh Texture Imposter Baker)
* **Operators:**
  - `texture_oven.py`
* **Panels:**
  - `texture_oven_panel.py`
* **Core File:**
  - `core/texture_oven_core.py`

---

## ⚙️ Properties and Preferences Distribution

Each addon will have its own localized `properties.py` and `preferences.py`.

### 1. `rextools`
* **Properties:**
  - `Scene.bone_rename_props` (`BoneRenameProperties`)
  - `Scene.highlow_renamer_props` (`HighLowRenamerProperties`)
  - `Scene.chain_constraints_props` (`ChainConstraintsAdderProperties`)
  - `Scene.rex_common_settings` (`RexCommonSettings`)
  - `Scene.rex_auto_frame_range` (`BoolProperty`)
  - `Scene.rex_cleanup_props` (`CleanupProperties`)
  - `Scene.weight_tools_props` (`WeightToolsProperties`)
  - `Scene.pose_tools_props` (`PoseToolsProperties`)
  - `Scene.sculpt_tools_props` (`SculptToolsProperties`)
  - `Scene.rextools3_keyframe_offset_props` (`Rextools3KeyframeOffsetProperties`)
  - `Scene.rex_engine_vertex_stats` (`EngineVertexStatsProperties`)
  - `Scene.rex_asset_export_settings` (`RexAssetExportSettings`)
  - `WindowManager.modal_x`, `WindowManager.modal_y`
  - `WindowManager.select_similar_threshold`
  - `WindowManager.clear_inner_uv_area_seam`, `WindowManager.reseam_uv_area_seam`
  - `WindowManager.stop_loop_at_seam`
* **Preferences:** Toggles and category customizations for modeling, selection, keymaps, and shortcuts.

### 2. `rexport`
* **Properties:**
  - `Scene.rex_export_settings` (`RexExportSettings`)
  - `Collection.rex_export_overrides` (`RexCollectionExportOverrides`)
* **Preferences:** Target directory defaults and FBX/GLTF specific properties.

### 3. `easy_pbr`
* **Properties:**
  - `Material.pbr_settings` (`PBRMaterialSettings`)
  - `Scene.rex_batch_mat_props` (`BatchMaterialProperties`)
  - `Scene.rex_missing_texture_scanner` (`Rextools3MissingTextureScanner`)
* **Preferences:** Naming conventions, PBR maps suffixes list configuration.

### 4. `texture_oven`
* **Properties:**
  - `Scene.rex_texture_oven_props` (`TextureOvenProperties`)
* **Preferences:** Standard baking settings.

---

## 🛠️ Automation Scripts

### 1. `setup_dev.py` (Local Development Setup)
Creates Directory Junctions on Windows:
```python
import os
import subprocess
import shutil

ADDONS = ['rextools', 'rexport', 'easy_pbr', 'texture_oven']
SHARED_DIRS = ['core', 'ui', 'assets']

def setup_junctions():
    root = os.path.dirname(os.path.abspath(__file__))
    shared = os.path.join(root, 'shared')
    
    for addon in ADDONS:
        addon_dir = os.path.join(root, addon)
        os.makedirs(addon_dir, exist_ok=True)
        
        # Copy auto_load.py (file-level copy)
        shutil.copy2(os.path.join(shared, 'auto_load.py'), os.path.join(addon_dir, 'auto_load.py'))
        
        # Link shared folders (core, ui, assets)
        for sdir in SHARED_DIRS:
            target = os.path.join(addon_dir, sdir)
            source = os.path.join(shared, sdir)
            
            # Clean up existing folders/links
            if os.path.exists(target) or os.path.islink(target):
                if os.path.isdir(target) and not os.path.islink(target):
                    shutil.rmtree(target)
                else:
                    os.remove(target)
            
            # Create Windows directory junction
            subprocess.run(['cmd', '/c', f'mklink /J "{target}" "{source}"'], check=True)
    print("Development junction setup complete!")

if __name__ == '__main__':
    setup_junctions()
```

### 2. `package.py` (Release Builder)
Compiles self-contained extensions:
1. Validates that `verify_addons.py` passes.
2. Zips the directory structure of each addon, resolving symlinks into actual files for release.
3. Outputs zipped packages into the `dist/` folder.

---

## 🧪 Verification Plan

### Headless Blender Verification (`verify_addons.py`)
Runs programmatically inside Blender to load and register each addon:
```powershell
blender --background --python verify_addons.py
```
* **Verify Imports:** Ensures all local module paths and references resolve correctly.
* **Verify Registration:** Checks that Blender registers all classes (`Operator`, `Panel`, `PropertyGroup`) without errors.
* **Verify Cleanup:** Checks that unregistration removes all classes and custom property hooks from `bpy.types`.

### Git Exclusions
We will configure `.gitignore` to prevent any generated directories from being committed:
```
# Ignore synced shared folders inside addons
rextools/core/
rextools/ui/
rextools/assets/
rextools/auto_load.py
rexport/core/
rexport/ui/
rexport/assets/
rexport/auto_load.py
easy_pbr/core/
easy_pbr/ui/
easy_pbr/assets/
easy_pbr/auto_load.py
texture_oven/core/
texture_oven/ui/
texture_oven/assets/
texture_oven/auto_load.py

# Ignore packaged builds
dist/
```
