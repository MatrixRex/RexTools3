import bpy
import blf
from bpy.app.handlers import persistent

# ---------------------------------------------------------------------------
# Normals access (the API differs across Blender versions)
#   < 4.1 : mesh.calc_normals_split() then loop.normal
#   >= 4.1: mesh.corner_normals[i].vector  (auto-computed, read-only)
# ---------------------------------------------------------------------------
def get_corner_normals(mesh):
    if bpy.app.version < (4, 1, 0):
        mesh.calc_normals_split()
        return [tuple(l.normal) for l in mesh.loops]
    else:
        # Accessing corner_normals computes/refreshes the cache automatically.
        return [tuple(cn.vector) for cn in mesh.corner_normals]


def compute_engine_verts(obj, depsgraph, nrm_prec, uv_prec, col_prec,
                         use_uv, use_color):
    """Return (blender_verts, engine_verts, triangles) for one object.

    engine_verts = number of UNIQUE (position, normal, UVs, color) tuples per
    face-corner. This is what ends up in the GPU vertex buffer in Unity.
    """
    if obj.mode == 'EDIT':
        obj.update_from_editmesh()

    eval_obj = obj.evaluated_get(depsgraph)      # modifiers applied
    mesh = eval_obj.data                          # evaluated mesh data (no to_mesh/to_mesh_clear needed on eval data)
    
    mesh.calc_loop_triangles()
    tris = len(mesh.loop_triangles)

    normals = get_corner_normals(mesh)

    uv_layers = [uvl.data for uvl in mesh.uv_layers] if use_uv else []

    color_layers = []
    if use_color and hasattr(mesh, "color_attributes"):
        for ca in mesh.color_attributes:
            # domain is 'POINT' (per-vertex) or 'CORNER' (per-loop)
            color_layers.append((ca.domain, ca.data))

    nq = 10 ** nrm_prec   # quantization factors to kill float noise
    uq = 10 ** uv_prec
    cq = 10 ** col_prec

    keys = set()
    for li, loop in enumerate(mesh.loops):
        vidx = loop.vertex_index
        n = normals[li]
        key = [vidx,
               round(n[0] * nq), round(n[1] * nq), round(n[2] * nq)]

        for uvdata in uv_layers:
            uv = uvdata[li].uv
            key.append(round(uv[0] * uq))
            key.append(round(uv[1] * uq))

        for domain, cdata in color_layers:
            idx = li if domain == 'CORNER' else vidx
            c = cdata[idx].color
            key.append(round(c[0] * cq))
            key.append(round(c[1] * cq))
            key.append(round(c[2] * cq))
            key.append(round(c[3] * cq))

        keys.add(tuple(key))

    return len(mesh.vertices), len(keys), tris


# ---------------------------------------------------------------------------
# Operator
# ---------------------------------------------------------------------------
class REXTOOLS3_OT_calculate_engine_stats(bpy.types.Operator):
    bl_idname = "rextools3.calculate_engine_stats"
    bl_label = "Calculate Engine Stats"
    bl_description = "Compute Unity-accurate render vertex count for selected meshes"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        deps = context.evaluated_depsgraph_get()
        s = context.scene
        props = s.rex_engine_vertex_stats

        addon_name = ".".join(__package__.split(".")[:3]) if __package__ and __package__.startswith("bl_ext.") else (__package__.partition('.')[0] if __package__ else "RexTools3")
        prefs = context.preferences.addons[addon_name].preferences

        active_obj = context.active_object
        selected_objs = context.selected_objects
        
        is_mesh_selected = (active_obj and active_obj.type == 'MESH' and active_obj in selected_objs)

        if is_mesh_selected:
            bv, ev, tr = compute_engine_verts(
                active_obj, deps,
                prefs.evstat_nrm_prec, prefs.evstat_uv_prec, prefs.evstat_col_prec,
                prefs.evstat_use_uv, prefs.evstat_use_color,
            )
            props.blender_verts = bv
            props.engine_verts = ev
            props.tris = tr
            props.count = 1
            self.report({'INFO'}, f"{active_obj.name}: {ev} verts / {tr} tris")
        else:
            props.blender_verts = 0
            props.engine_verts = 0
            props.tris = 0
            props.count = 0
            self.report({'WARNING'}, "No active mesh selected")
            return {'CANCELLED'}

        return {'FINISHED'}


# ---------------------------------------------------------------------------
# Auto Recalculate Handler
# ---------------------------------------------------------------------------
last_selection_hash = None
_in_handler = False

@persistent
def evstat_auto_recalc_handler(scene, depsgraph=None):
    global last_selection_hash, _in_handler
    if _in_handler:
        return

    addon_name = ".".join(__package__.split(".")[:3]) if __package__ and __package__.startswith("bl_ext.") else (__package__.partition('.')[0] if __package__ else "RexTools3")
    try:
        prefs = bpy.context.preferences.addons[addon_name].preferences
    except Exception:
        return

    context = bpy.context
    selected_objs = context.selected_objects
    active_obj = context.active_object
    
    # Hash of names and mode of selected/active objects to only trigger on selection or mode change
    current_hash = hash(tuple(sorted([o.name for o in selected_objs])) + (active_obj.name if active_obj else "", active_obj.mode if active_obj else ""))
    
    if current_hash != last_selection_hash:
        last_selection_hash = current_hash
        _in_handler = True
        try:
            is_mesh_selected = (active_obj and active_obj.type == 'MESH' and active_obj in selected_objs)
            props = scene.rex_engine_vertex_stats
            
            if is_mesh_selected:
                if getattr(prefs, "evstat_auto_recalculate", False):
                    if not depsgraph:
                        depsgraph = context.evaluated_depsgraph_get()
                    bv, ev, tr = compute_engine_verts(
                        active_obj, depsgraph,
                        prefs.evstat_nrm_prec, prefs.evstat_uv_prec, prefs.evstat_col_prec,
                        prefs.evstat_use_uv, prefs.evstat_use_color,
                    )
                    props.blender_verts = bv
                    props.engine_verts = ev
                    props.tris = tr
                    props.count = 1
                else:
                    # Selection changed/active object changed but auto recalculate is off.
                    # Reset properties to 0 since the old calculated stats are stale.
                    props.blender_verts = 0
                    props.engine_verts = 0
                    props.tris = 0
                    props.count = 0
            else:
                props.blender_verts = 0
                props.engine_verts = 0
                props.tris = 0
                props.count = 0
        except Exception as e:
            # Silence errors in handlers to avoid disrupting Blender interaction
            print(f"[EngineVertexStats] Auto-recalculate error: {e}")
        finally:
            _in_handler = False


# ---------------------------------------------------------------------------
# Viewport Overlay Drawing
# ---------------------------------------------------------------------------
def draw_viewport_callback():
    context = bpy.context
    if not context or not context.area or context.area.type != 'VIEW_3D':
        return
        
    addon_name = ".".join(__package__.split(".")[:3]) if __package__ and __package__.startswith("bl_ext.") else (__package__.partition('.')[0] if __package__ else "RexTools3")
    try:
        prefs = context.preferences.addons[addon_name].preferences
    except Exception:
        return
        
    if not getattr(prefs, "enable_engine_vertex_stats", False) or not getattr(prefs, "evstat_show_overlay", False):
        return

    # Only draw in Object Mode
    if context.mode != 'OBJECT':
        return

    props = context.scene.rex_engine_vertex_stats
    region = context.region
    
    # Calculate top offset dynamically based on native statistics visibility
    top_offset = 265

    if getattr(context.space_data.overlay, "show_stats", False):
        if context.mode == 'EDIT_MESH':
            top_offset += 0
        else:
            top_offset += 0
            
    x = 130
    y = region.height - top_offset
    
    active_obj = context.active_object
    selected_objs = context.selected_objects
    is_mesh_selected = (active_obj and active_obj.type == 'MESH' and active_obj in selected_objs)
    
    engine_verts = props.engine_verts if is_mesh_selected else 0
    text = f"Game Verts: {engine_verts:,}"
    
    font_id = 0
    blf.size(font_id, 14)
    # Match standard Blender stats text color and styling
    blf.color(font_id, 1, 1, 1, 1)
    blf.position(font_id, x, y, 0)
    blf.draw(font_id, text)


_draw_handler = None

def register():
    global _draw_handler
    if evstat_auto_recalc_handler not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(evstat_auto_recalc_handler)
        
    if _draw_handler is None:
        _draw_handler = bpy.types.SpaceView3D.draw_handler_add(draw_viewport_callback, (), 'WINDOW', 'POST_PIXEL')


def unregister():
    global _draw_handler
    if evstat_auto_recalc_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(evstat_auto_recalc_handler)
        
    if _draw_handler is not None:
        bpy.types.SpaceView3D.draw_handler_remove(_draw_handler, 'WINDOW')
        _draw_handler = None
