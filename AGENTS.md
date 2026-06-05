# RexTools3 — Agent Guide

Purpose: Help AI coding agents become productive in the RexTools3 Blender add-on.

## Project Essentials & Quick Orientation

- **Blender add-on** (Python, `bpy`). No pip/venv/pyproject. No external deps. No tests. No CI.
- **Entry**: `__init__.py` → `auto_load.init()` discovers modules from `operators/`, `panels/`, `core/`, `ui/`.
- **Registering classes**: never call `bpy.utils.register_class` directly at module import time. Add class to an `operators/` or `panels/` module; `auto_load` handles ordering via type annotations and `bl_parent_id`.
- **Properties**: define `PropertyGroup` in `properties.py`, register in `register_properties()`, unregister in `unregister_properties()`. Always update both.
- **Keymaps**: register in per-module `register()`/`unregister()` (see `context_aware_select.py`).

## Architecture Quick Reference

```
__init__.py       bl_info, register/unregister, auto_load.init()
auto_load.py      Dynamic discovery + topological sort for registration
properties.py     All PropertyGroups + global PointerProperty registration
operators/        49 files — business logic
panels/           17 files — UI panels
core/             theme.py, notify.py, fbx_utils.py
ui/               Custom viewport overlay (GPU drawing, widget elements, manager)
```

## Important Files and Patterns

- `auto_load.py`: Central to registration. Prefer adding new `Operator`, `Panel`, or `PropertyGroup` classes to `operators/` or `panels/` and rely on `auto_load` to discover them.
- `properties.py`: Defines `PropertyGroup` types and registers global properties on `bpy.types` (e.g., `Scene.bone_rename_props`, `Material.pbr_settings`). Use the same pattern when adding new properties and put update callbacks here. Attach `PointerProperty` instances inside `register_properties()` and remove in `unregister_properties()`.
- `operators/`: Place command logic in individual modules. Keep one or two closely related classes per file (many operator files define both an `Operator` and a small panel; replicate that style). Follow existing naming: `REXTOOLS3_OT_...` or `MESH_OT_...` and set `bl_idname` accordingly (lowercase `module.action`).
- `panels/`: UI panels live here (e.g., `panels/common_tools.py`). Panels should use `bl_category = "RexTools3"` and target `VIEW_3D`, `UI` region.

## Coding Conventions & Constraints

| Area | Rule |
|---|---|
| Undo | `bl_options = {'REGISTER', 'UNDO'}` on data-modifying operators |
| Polling | Always use `poll(cls, context)` to gate operator/panel availability |
| Cross-platform | `sys.platform` branching for file paths (see `open_folder.py`) |
| UI overlay | Custom GPU overlay system in `ui/` — use `core/notify.py` (not `self.report()`) |
| Panel style | Use `ui/utils.py` helpers: `draw_section()`, `draw_input_group()`, `draw_call_to_action()` |
| Theme | Single source in `core/theme.py` — never hardcode colors |
| Monkey-patching | `fbx_utils.py` patches Blender's FBX exporter; always restores originals |
| Blender API | Contains version-gated logic (see `auto_load.get_dependency_from_annotation`). Prefer existing compatibility approaches. |

## Implementation Examples (Copy-Paste Friendly)

### Adding an Operator
Create `operators/my_op.py` with:
```python
import bpy

class REXTOOLS3_OT_my_operator(bpy.types.Operator):
    bl_idname = "rextools3.my_operator"
    bl_label = "My Operator"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        # Operator logic here
        return {'FINISHED'}
```

### Adding Properties
Add `PropertyGroup` subclass in `properties.py` and register/unregister a `PointerProperty`:
```python
# In properties.py
class Rextools3MyProps(bpy.types.PropertyGroup):
    my_bool: bpy.props.BoolProperty(name="My Property")

def register_properties():
    bpy.types.Scene.rextools3_my_props = bpy.props.PointerProperty(type=Rextools3MyProps)
    # Register others...

def unregister_properties():
    del bpy.types.Scene.rextools3_my_props
    # Unregister others...
```

## Build / Lint / Verify

- There are no automated tests in the repo. Manual runtime verification steps:
  - Install the add-on in Blender (use `Edit → Preferences → Add-ons → Install...` pointing to this folder or zip).
  - Enable the add-on and open `3D Viewport → Sidebar → RexTools3` to exercise panels and operators.
  - Save a `.blend` file when testing file-system operators (e.g., `rextools3.open_folder`).
- Useful local commands (PowerShell):
```powershell
# Package (run from repo root)
Compress-Archive -Path . -DestinationPath ..\rextools3.zip

# Lint (if pyflakes available in host Python)
python -m pyflakes .
```

## Gotchas & Guidelines

- **Post-Feature Updates**: After completing a feature, ask the user if they want to update the README and CHANGELOG (using the workflows `/update-readme` and `/update-changelog`).
- **Small, focused diffs only**: Avoid changing registration mechanics or the `auto_load` algorithm unless fixing a real bug and include tests or manual verification steps.
- **Third-party dependencies**: If adding dependencies, list them in `blender_manifest.toml` `wheels` section and explain why they are required for offline packaging.
- **No registration hacks**: When a class depends on another (e.g., a Panel's `bl_parent_id` or property annotations), rely on `auto_load`'s dependency discovery instead of explicit registration order hacks.
- **Clarification**: For design intent (why a particular operator exists or UX expectations), check `Plan.md` for feature notes and iterate with the repo owner.
- **If you modify this file**: Keep it short and example-driven; avoid generic, project-agnostic advice.

