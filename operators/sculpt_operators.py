import bpy
import os
from bpy.props import StringProperty
from bpy.types import Operator


# Maps context.mode strings to bpy.ops.object.mode_set(mode=...) strings
_MODE_SET_MAP = {
    'OBJECT':         'OBJECT',
    'EDIT_MESH':      'EDIT',
    'SCULPT':         'SCULPT',
    'PAINT_VERTEX':   'VERTEX_PAINT',
    'PAINT_WEIGHT':   'WEIGHT_PAINT',
    'PAINT_TEXTURE':  'TEXTURE_PAINT',
    'POSE':           'POSE',
}


class REXTOOLS3_OT_batch_assign_sculpt_previews(Operator):
    """Batch assign preview images to sculpt brush assets from a selected folder."""
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

        matches = self._find_matches(context, image_files)

        if not matches:
            self.report({'WARNING'}, "No matching brush assets found in any asset library")
            return {'CANCELLED'}

        # ── Find a 3D Viewport area + WINDOW region ───────────────────────────
        view_area = None
        view_region = None
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                for region in area.regions:
                    if region.type == 'WINDOW':
                        view_area = area
                        view_region = region
                        break
            if view_area:
                break

        if view_area is None:
            self.report({'ERROR'}, "No 3D Viewport found — please open a 3D Viewport")
            return {'CANCELLED'}

        # ── Ensure we are in Sculpt Mode (brush operators require it) ─────────
        original_mode = context.mode          # e.g. 'OBJECT', 'SCULPT', 'EDIT_MESH'
        switched_mode = False

        if original_mode != 'SCULPT':
            obj = context.active_object
            if obj is None or obj.type != 'MESH':
                self.report({'ERROR'},
                    "An active mesh object is required to enter Sculpt Mode for brush ops")
                return {'CANCELLED'}
            with context.temp_override(area=view_area, region=view_region):
                bpy.ops.object.mode_set(mode='SCULPT')
            switched_mode = True

        count = 0
        skipped = 0

        try:
            for lib_name, identifier, brush_name, img_path in matches:
                try:
                    with context.temp_override(area=view_area, region=view_region):
                        # 1. Activate the brush asset — sets the asset context.
                        bpy.ops.brush.asset_activate(
                            asset_library_type='CUSTOM',
                            asset_library_identifier=lib_name,
                            relative_asset_identifier=identifier,
                        )

                    # 2. Flush a redraw so the async asset load has a chance to
                    #    complete before asset_load_preview runs its poll check.
                    bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

                    with context.temp_override(area=view_area, region=view_region):
                        # 3. Load the preview — writes directly into the source
                        #    .asset.blend on disk. No separate save needed.
                        result = bpy.ops.brush.asset_load_preview(
                            'EXEC_DEFAULT', filepath=img_path
                        )

                    if 'FINISHED' in result:
                        count += 1
                        print(f"[RexTools3] Preview assigned: {brush_name} <- {os.path.basename(img_path)}")
                    else:
                        skipped += 1
                        self.report({'WARNING'}, f"asset_load_preview failed for '{brush_name}': {result}")

                except Exception as e:
                    skipped += 1
                    self.report({'WARNING'}, f"Failed '{brush_name}': {e}")

        finally:
            # ── Restore original interaction mode ─────────────────────────────
            if switched_mode:
                restore = _MODE_SET_MAP.get(original_mode, 'OBJECT')
                try:
                    with context.temp_override(area=view_area, region=view_region):
                        bpy.ops.object.mode_set(mode=restore)
                except Exception:
                    pass

        # ── Refresh any open Asset Browser ────────────────────────────────────
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

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _find_matches(self, context, image_files):
        """
        Walk every custom asset library and find .asset.blend files whose
        base-name matches an image in image_files.

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
                    rel = os.path.relpath(abs_file, lib_root).replace('/', '\\')
                    identifier = f"{rel}\\Brush\\{brush_name}"
                    img_path = image_files[brush_name.lower()]

                    results.append((lib.name, identifier, brush_name, img_path))
                    print(f"[RexTools3] Found asset: lib='{lib.name}' id='{identifier}'")

        return results
