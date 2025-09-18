<!-- .github/copilot-instructions.md -->
Purpose: help AI coding agents become productive in the RexTools3 Blender addon.

Quick orientation
- Project type: Blender add-on (Python) packaged as `rextools3` (see `blender_manifest.toml` and `__init__.py`).
- Entry points: `__init__.py` calls `auto_load.init()` and exposes `register()` / `unregister()` used by Blender.
- Auto-registration: `auto_load.py` dynamically imports `operators/` and `panels/` modules and computes a safe registration order.

Important files and patterns
- `auto_load.py`: central to registration. Prefer adding new `Operator`, `Panel`, or `PropertyGroup` classes to `operators/` or `panels/` and rely on `auto_load` to discover them.
- `properties.py`: defines `PropertyGroup` types and registers global properties on `bpy.types` (e.g., `Scene.bone_rename_props`, `Material.pbr_settings`). Use the same pattern when adding new properties and put update callbacks here.
- `operators/`: place command logic in individual modules. Example: `operators/checker_dissolve.py` defines `MESH_OT_checker_dissolve` and a small `Panel` in the same file. Follow existing naming: `REXTOOLS3_OT_...` or `MESH_OT_...` and set `bl_idname` accordingly.
- `panels/`: UI panels live here (e.g., `panels/common_tools.py`). Panels should use `bl_category = "RexTools3"` and target `VIEW_3D`, `UI` region.

Coding conventions & constraints
- Registration: Do not call `bpy.utils.register_class` directly at module import time. Add classes and rely on `auto_load` which computes dependencies and registers in order.
- Properties: attach PointerProperty instances to `bpy.types` (WindowManager, Scene, Material) inside `register_properties()` and remove in `unregister_properties()`.
- Operators/Panel Polling: use `poll(cls, context)` consistently to gate UI availability (see `checker_dissolve.py` and `common_tools.py`).
- IO & platform differences: use `sys.platform` checks as in `operators/open_folder.py` for cross-OS behavior.
- Blender API versions: the code contains version-gated logic (see `auto_load.get_dependency_from_annotation`). When adding features, prefer the existing compatibility approach.

Tests, build, and runtime
- There are no automated tests in the repo. Manual runtime verification steps:
  - Install the add-on in Blender (use `Edit → Preferences → Add-ons → Install...` pointing to this folder or zip).
  - Enable the add-on and open `3D Viewport → Sidebar → RexTools3` to exercise panels and operators.
  - Save a `.blend` file when testing file-system operators (e.g., `rextools3.open_folder`).
- Useful local commands (PowerShell):
  - Zip for install: `Compress-Archive -Path . -DestinationPath ..\rextools3.zip` (run from repo root)
  - Quick lint: `python -m pyflakes .` (if pyflakes is installed in the environment used outside Blender)

Common patterns to follow in changes
- Single-responsibility modules: keep one or two closely related classes per file (many operator files define both an `Operator` and a small panel; replicate that style).
- Use Blender-friendly undo: set `bl_options = {'REGISTER', 'UNDO'}` on operators that modify data.
- Preserve naming conventions for `bl_idname` (lowercase `module.action`) and class name prefixes (`REXTOOLS3_OT_`, `MESH_OT_`, `VIEW3D_PT_`).
- When a class depends on another (e.g., a Panel's `bl_parent_id` or property annotations), rely on `auto_load`'s dependency discovery instead of explicit registration order hacks.

Implementation examples (copy-paste friendly)
- Add an operator: create `operators/my_op.py` with
  - class `REXTOOLS3_OT_my_operator(bpy.types.Operator)`
  - `bl_idname = "rextools3.my_operator"`, `bl_label` and `bl_options`
  - `poll`, `execute`, and optional `invoke` methods
- Add properties: add `PropertyGroup` subclass in `properties.py` and register a `PointerProperty` in `register_properties()`.

Notes for AI code changes
- Small, focused diffs only. Avoid changing registration mechanics or the `auto_load` algorithm unless fixing a real bug and include tests or manual verification steps.
- If adding dependencies (third-party packages), list them in `blender_manifest.toml` `wheels` section and explain why they are required for offline packaging.
- When altering `properties.py` update both `register_properties()` and `unregister_properties()` to keep Blender stable when reloading the add-on.

Where to ask for clarification
- For design intent (why a particular operator exists or UX expectations), check `Plan.md` for feature notes and iterate with the repo owner.

If you modify this file: keep it short and example-driven; avoid generic, project-agnostic advice.
