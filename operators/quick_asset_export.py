import bpy
import os
import uuid
from ..core import notify

def _target_dir(prefs, context):
    """Resolve the absolute folder to write the asset .blend into."""
    if prefs.library == "__CUSTOM__":
        path = prefs.custom_path
    else:
        path = ""
        for lib in context.preferences.filepaths.asset_libraries:
            if lib.name == prefs.library:
                path = lib.path
                break
    return bpy.path.abspath(path) if path else ""


def _ensure_catalog(library_dir, catalog_path):
    """Make sure a catalog exists in the library's blender_assets.cats.txt.

    Returns the catalog UUID (string) or None. Creating the catalog here means
    the asset lands in the right folder of the Asset Browser automatically.
    """
    catalog_path = (catalog_path or "").strip().strip("/")
    if not catalog_path:
        return None

    cats_file = os.path.join(library_dir, "blender_assets.cats.txt")
    simple_name = catalog_path.split("/")[-1]
    lines = []

    if os.path.exists(cats_file):
        with open(cats_file, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
        for line in lines:
            s = line.strip()
            if not s or s.startswith("#") or s.startswith("VERSION"):
                continue
            parts = s.split(":")
            if len(parts) >= 2 and parts[1] == catalog_path:
                return parts[0]  # catalog already exists -> reuse its UUID

    new_uuid = str(uuid.uuid4())
    if not lines:
        lines = [
            "# This is an Asset Catalog Definition file for Blender.",
            "",
            "VERSION 1",
            "",
        ]
    lines.append("{0}:{1}:{2}".format(new_uuid, catalog_path, simple_name))
    with open(cats_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return new_uuid


class REXTOOLS3_OT_QuickAssetExport(bpy.types.Operator):
    bl_idname = "rextools3.quick_asset_export"
    bl_label = "Save Selected as Asset"
    bl_description = "Mark selected objects as assets and write them to your asset library"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return bool(context.selected_objects)

    def execute(self, context):
        prefs = context.scene.rex_asset_export_settings
        addon_name = ".".join(__package__.split(".")[:3]) if __package__ and __package__.startswith("bl_ext.") else (__package__.partition('.')[0] if __package__ else "RexTools3")
        addon_prefs = context.preferences.addons[addon_name].preferences
        target = _target_dir(prefs, context)

        if not target or not os.path.isdir(target):
            notify.error("Asset library folder is not set or does not exist.")
            return {'CANCELLED'}

        objects = list(context.selected_objects)
        if not objects:
            notify.error("No objects selected.")
            return {'CANCELLED'}

        catalog_path = prefs.catalog if prefs.catalog_selection == "__CUSTOM__" else prefs.catalog_selection
        try:
            catalog_id = _ensure_catalog(target, catalog_path)
        except Exception as e:
            notify.error(f"Could not write catalog file: {e}")
            return {'CANCELLED'}

        # Mark + queue preview generation now. Previews render on a background
        # thread, so the actual file write is deferred below.
        marked = []
        for obj in objects:
            if not obj.asset_data:
                obj.asset_mark()
            obj.asset_generate_preview()
            if catalog_id:
                obj.asset_data.catalog_id = catalog_id
            marked.append(obj)

        names = [o.name for o in marked]
        separate = prefs.separate_files
        clear_after = addon_prefs.quick_asset_clear_after
        base = bpy.path.clean_name(
            os.path.splitext(os.path.basename(bpy.data.filepath))[0]
        ) or "assets"

        def _do_write():
            objs = [bpy.data.objects.get(n) for n in names]
            objs = [o for o in objs if o is not None and o.asset_data]
            written = 0
            try:
                if separate:
                    for o in objs:
                        fp = os.path.join(target, bpy.path.clean_name(o.name) + ".blend")
                        bpy.data.libraries.write(fp, {o}, fake_user=True, compress=True)
                        written += 1
                elif objs:
                    fp = os.path.join(target, base + ".blend")
                    bpy.data.libraries.write(fp, set(objs), fake_user=True, compress=True)
                    written = len(objs)
            except Exception as e:
                print("[Quick Blender Assets] Write failed:", e)
                notify.error(f"Asset export write failed: {e}")
                return None

            if clear_after:
                for o in objs:
                    if o.asset_data:
                        o.asset_clear()

            try:
                bpy.ops.asset.library_refresh()
            except Exception:
                pass  # no Asset Browser open / wrong context -> ignore

            notify.success(f"Wrote {written} asset(s) to {target}")
            return None  # one-shot timer

        bpy.app.timers.register(_do_write, first_interval=addon_prefs.quick_asset_preview_wait)

        notify.info(f"Exporting {len(marked)} object(s) (rendering thumbnails)...")
        return {'FINISHED'}


def _menu_func(self, context):
    self.layout.operator(REXTOOLS3_OT_QuickAssetExport.bl_idname, icon='EXPORT')


def register():
    bpy.types.VIEW3D_MT_object.append(_menu_func)
    bpy.types.VIEW3D_MT_object_context_menu.append(_menu_func)


def unregister():
    bpy.types.VIEW3D_MT_object_context_menu.remove(_menu_func)
    bpy.types.VIEW3D_MT_object.remove(_menu_func)
