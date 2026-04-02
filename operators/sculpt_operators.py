import bpy
import os
from bpy.props import StringProperty
from bpy.types import Operator


class REXTOOLS3_OT_batch_assign_sculpt_previews(Operator):
    """Batch assign preview images to sculpt brush assets from a selected folder.
    Run this from Sculpt Mode so brush.asset_activate can set the active brush."""
    bl_idname = "rextools3.batch_assign_sculpt_previews"
    bl_label = "Batch Assign Previews"
    bl_options = {'REGISTER'}

    directory: StringProperty(
        name="Folder Path",
        description="Select the folder containing preview images",
        subtype='DIR_PATH'
    )

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        folder_path = self.directory
        if not os.path.isdir(folder_path):
            folder_path = os.path.dirname(folder_path)

        if not folder_path or not os.path.exists(folder_path):
            self.report({'ERROR'}, "Selected folder does not exist")
            return {'CANCELLED'}

        valid_extensions = {".png", ".jpg", ".jpeg"}
        image_files = {}
        for f in os.listdir(folder_path):
            name, ext = os.path.splitext(f)
            if ext.lower() in valid_extensions:
                image_files[name.lower()] = os.path.join(folder_path, f)

        if not image_files:
            self.report({'WARNING'}, "No valid image files found in the directory")
            return {'CANCELLED'}

        # Scan all custom asset libraries for .asset.blend files whose names
        # match an image in the folder.
        matches = self._find_matches(context, image_files)

        if not matches:
            self.report({'WARNING'}, "No matching brush assets found in any asset library")
            return {'CANCELLED'}

        count = 0
        skipped = 0

        # Find any 3D Viewport + WINDOW region to use as context override for brush ops.
        # (The interaction mode is on context.object, not the Space — SpaceView3D has no .mode)
        sculpt_area = None
        sculpt_region = None
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                for region in area.regions:
                    if region.type == 'WINDOW':
                        sculpt_area = area
                        sculpt_region = region
                        break
            if sculpt_area:
                break

        if sculpt_area is None:
            self.report({'ERROR'}, "No 3D Viewport found — please open a 3D Viewport")
            return {'CANCELLED'}

        for lib_name, identifier, brush_name, img_path in matches:
            try:
                with context.temp_override(area=sculpt_area, region=sculpt_region):
                    # 1. Activate the brush asset so Blender knows which source
                    #    file to write. Requires a 3D View context.
                    bpy.ops.brush.asset_activate(
                        asset_library_type='CUSTOM',
                        asset_library_identifier=lib_name,
                        relative_asset_identifier=identifier,
                    )
                    # 2. Load the new preview — this writes it directly into the
                    #    source .asset.blend on disk. No separate save needed.
                    result = bpy.ops.brush.asset_load_preview('EXEC_DEFAULT', filepath=img_path)

                if 'FINISHED' in result:
                    count += 1
                    print(f"[RexTools3] Preview assigned: {brush_name} <- {os.path.basename(img_path)}")
                else:
                    skipped += 1
                    self.report({'WARNING'}, f"asset_load_preview failed for '{brush_name}': {result}")

            except Exception as e:
                skipped += 1
                self.report({'WARNING'}, f"Failed '{brush_name}': {e}")

        # Refresh any open Asset Browser so the new thumbnails appear immediately
        try:
            for area in context.screen.areas:
                if area.type == 'FILE_BROWSER' and area.ui_type == 'ASSETS':
                    with context.temp_override(area=area):
                        bpy.ops.asset.library_refresh()
                    break
        except Exception:
            pass

        if count == 0:
            self.report({'WARNING'}, "No previews were successfully assigned")
            return {'CANCELLED'}

        msg = f"Assigned previews to {count} brush asset(s)"
        if skipped:
            msg += f" ({skipped} failed — check System Console)"
        self.report({'INFO'}, msg)
        return {'FINISHED'}

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _find_matches(self, context, image_files):
        """
        Walk every custom asset library and find .asset.blend files whose
        base-name matches an image in image_files.

        .asset.blend convention: the file is named after the single asset it
        contains, e.g. 'Fold10.asset.blend' holds brush 'Fold10'.

        Returns: list of (lib_name, relative_asset_identifier, brush_name, img_path)
        """
        results = []

        for lib in context.preferences.filepaths.asset_libraries:
            lib_root = bpy.path.abspath(lib.path)
            if not os.path.isdir(lib_root):
                continue

            for dirpath, _dirs, files in os.walk(lib_root):
                for fname in files:
                    if not fname.endswith('.asset.blend'):
                        continue

                    brush_name = fname[: -len('.asset.blend')]
                    if brush_name.lower() not in image_files:
                        continue

                    abs_file = os.path.join(dirpath, fname)
                    # Build the relative_asset_identifier Blender expects:
                    #   <path relative to lib root>\Brush\<brush name>
                    # Use backslashes (Blender's asset system on all platforms).
                    rel = os.path.relpath(abs_file, lib_root).replace('/', '\\')
                    identifier = f"{rel}\\Brush\\{brush_name}"
                    img_path = image_files[brush_name.lower()]

                    results.append((lib.name, identifier, brush_name, img_path))
                    print(f"[RexTools3] Found asset: lib='{lib.name}' id='{identifier}'")

        return results
