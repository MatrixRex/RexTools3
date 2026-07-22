import bpy
from ..core import notify

addon_keymaps = []

def get_sculpt_brush(context):
    """Robust sculpt brush lookup across Blender 3.x, 4.x, 4.5+ and 5.x."""
    # 1. Check sculpt_object.sculpt_session
    sculpt_obj = getattr(context, "sculpt_object", None) or getattr(context, "active_object", None)
    if sculpt_obj:
        ss = getattr(sculpt_obj, "sculpt_session", None)
        if ss:
            b = getattr(ss, "active_brush", None) or getattr(ss, "brush", None)
            if b:
                return b

    # 2. Check context.tool_settings.sculpt
    ts = getattr(context, "tool_settings", None)
    if ts:
        sculpt = getattr(ts, "sculpt", None)
        if sculpt:
            b = getattr(sculpt, "brush", None)
            if b:
                return b

    # 3. Direct context brush
    try:
        b = getattr(context, "brush", None)
        if b:
            return b
    except Exception:
        pass

    return None


def get_active_brush(context, paint_type=None):
    """Retrieve active brush compatible with Blender 3.x, 4.x, 4.5+ and 5.x."""
    if paint_type == 'SCULPT':
        return get_sculpt_brush(context)

    # Direct context access
    try:
        brush = getattr(context, "brush", None)
        if brush:
            return brush
    except Exception:
        pass

    tool_settings = getattr(context, "tool_settings", None)
    if not tool_settings:
        return None

    # Fallback to mode tool_settings
    if paint_type == 'WEIGHT':
        wp = getattr(tool_settings, "weight_paint", None)
        if wp and getattr(wp, "brush", None):
            return wp.brush
    elif paint_type == 'VERTEX':
        vp = getattr(tool_settings, "vertex_paint", None)
        if vp and getattr(vp, "brush", None):
            return vp.brush
    elif paint_type == 'IMAGE':
        ip = getattr(tool_settings, "image_paint", None)
        if ip and getattr(ip, "brush", None):
            return ip.brush

    for attr in ("sculpt", "weight_paint", "vertex_paint", "image_paint"):
        st = getattr(tool_settings, attr, None)
        b = getattr(st, "brush", None) if st else None
        if b:
            return b

    return None


def redraw_all_areas(context):
    """Force UI redraw across screen areas for instant feedback."""
    try:
        if context.window_manager:
            for window in context.window_manager.windows:
                if window.screen:
                    for area in window.screen.areas:
                        area.tag_redraw()
    except Exception:
        if context.area:
            context.area.tag_redraw()


class REXTOOLS3_OT_flip_paint_polarity(bpy.types.Operator):
    """Flip active brush weight, sculpt direction, or foreground/background colors in paint modes"""
    bl_idname = "rextools3.flip_paint_polarity"
    bl_label = "Flip Paint Polarity / Weight / Colors"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if not context.tool_settings:
            return False
        
        # Check standard 3D view paint modes
        paint_modes = {'SCULPT', 'PAINT_WEIGHT', 'PAINT_VERTEX', 'PAINT_TEXTURE', 'SCULPT_VERTEX'}
        if context.mode in paint_modes:
            return True

        # Check Image Editor image paint mode
        if context.area and context.area.type == 'IMAGE_EDITOR':
            space = context.space_data
            if hasattr(space, 'mode') and space.mode == 'PAINT':
                return True

        return False

    def execute(self, context):
        mode = context.mode
        tool_settings = context.tool_settings
        area_type = context.area.type if context.area else None
        space_mode = getattr(context.space_data, 'mode', None) if context.space_data else None

        # 1. Weight Paint Mode
        if mode == 'PAINT_WEIGHT':
            brush = get_active_brush(context, 'WEIGHT')
            wp = getattr(tool_settings, "weight_paint", None)
            wp_ups = getattr(wp, "unified_paint_settings", None) if wp else None
            ups = getattr(tool_settings, "unified_paint_settings", None)

            current_w = None
            if wp_ups and getattr(wp_ups, 'use_unified_weight', False) and hasattr(wp_ups, 'weight'):
                current_w = wp_ups.weight
            elif ups and getattr(ups, 'use_unified_weight', False) and hasattr(ups, 'weight'):
                current_w = ups.weight
            elif brush and hasattr(brush, 'weight'):
                current_w = brush.weight
            elif wp_ups and hasattr(wp_ups, 'weight'):
                current_w = wp_ups.weight
            elif ups and hasattr(ups, 'weight'):
                current_w = ups.weight

            if current_w is not None:
                new_weight = round(1.0 - current_w, 4)

                if wp_ups and hasattr(wp_ups, 'weight'):
                    wp_ups.weight = new_weight
                if ups and hasattr(ups, 'weight'):
                    ups.weight = new_weight
                if brush and hasattr(brush, 'weight'):
                    brush.weight = new_weight

                redraw_all_areas(context)
                notify.info(f"Weight: {new_weight:g}")
                return {'FINISHED'}

        # 2. Sculpt Mode
        elif mode == 'SCULPT':
            brush = get_sculpt_brush(context)
            toggled = False
            new_dir_str = "Toggled"

            if brush and hasattr(brush, 'direction'):
                try:
                    current_dir = brush.direction
                    new_dir = 'SUBTRACT' if current_dir == 'ADD' else 'ADD'
                    brush.direction = new_dir
                    new_dir_str = new_dir.title()
                    toggled = True
                except Exception as e:
                    print(f"[RexTools3] Direct brush.direction edit failed: {e}")

            if not toggled:
                try:
                    res = bpy.ops.wm.context_toggle_enum(data_path="brush.direction", value_1="ADD", value_2="SUBTRACT")
                    if 'FINISHED' in res:
                        toggled = True
                        if brush and hasattr(brush, 'direction'):
                            new_dir_str = brush.direction.title()
                except Exception as e:
                    print(f"[RexTools3] context_toggle_enum failed: {e}")

            if toggled:
                redraw_all_areas(context)
                notify.info(f"Sculpt Polarity: {new_dir_str}")
                return {'FINISHED'}

        # 3. Vertex Color Paint Mode
        elif mode in {'PAINT_VERTEX', 'SCULPT_VERTEX'}:
            brush = get_active_brush(context, 'VERTEX')
            vp = getattr(tool_settings, "vertex_paint", None)
            vp_ups = getattr(vp, "unified_paint_settings", None) if vp else None
            ups = getattr(tool_settings, "unified_paint_settings", None)

            flipped = False
            for u in (vp_ups, ups):
                if u and hasattr(u, 'color') and hasattr(u, 'secondary_color'):
                    u.color, u.secondary_color = list(u.secondary_color), list(u.color)
                    flipped = True

            if brush and hasattr(brush, 'color') and hasattr(brush, 'secondary_color'):
                brush.color, brush.secondary_color = list(brush.secondary_color), list(brush.color)
                flipped = True

            if flipped:
                redraw_all_areas(context)
                notify.info("Colors Flipped")
                return {'FINISHED'}

        # 4. Image / Texture Paint Mode (3D View or Image Editor)
        elif mode == 'PAINT_TEXTURE' or (area_type == 'IMAGE_EDITOR' and space_mode == 'PAINT'):
            brush = get_active_brush(context, 'IMAGE')
            ip = getattr(tool_settings, "image_paint", None)
            ip_ups = getattr(ip, "unified_paint_settings", None) if ip else None
            ups = getattr(tool_settings, "unified_paint_settings", None)

            flipped = False
            for u in (ip_ups, ups):
                if u and hasattr(u, 'color') and hasattr(u, 'secondary_color'):
                    u.color, u.secondary_color = list(u.secondary_color), list(u.color)
                    flipped = True

            if brush and hasattr(brush, 'color') and hasattr(brush, 'secondary_color'):
                brush.color, brush.secondary_color = list(brush.secondary_color), list(brush.color)
                flipped = True

            if flipped:
                redraw_all_areas(context)
                notify.info("Colors Flipped")
                return {'FINISHED'}

        return {'CANCELLED'}


def register():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if not kc:
        return

    km_names = [
        'Sculpt', 
        'Sculpt Mode', 
        'Paint Sculpt', 
        'Weight Paint', 
        'Weight Paint Vertex Selection',
        'Vertex Paint', 
        'Image Paint', 
        'Image'
    ]
    for km_name in km_names:
        km = kc.keymaps.get(km_name)
        if not km:
            space_type = 'IMAGE_EDITOR' if km_name == 'Image' else 'VIEW_3D'
            km = kc.keymaps.new(name=km_name, space_type=space_type)
        kmi = km.keymap_items.new('rextools3.flip_paint_polarity', 'X', 'PRESS')
        try:
            addon_name = ".".join(__package__.split(".")[:3]) if __package__ and __package__.startswith("bl_ext.") else (__package__.partition('.')[0] if __package__ else "RexTools3")
            prefs = bpy.context.preferences.addons[addon_name].preferences
            kmi.active = getattr(prefs, 'enable_paint_flip', True)
        except Exception:
            pass
        addon_keymaps.append((km, kmi))


def unregister():
    for km, kmi in addon_keymaps:
        try:
            km.keymap_items.remove(kmi)
        except Exception:
            pass
    addon_keymaps.clear()
