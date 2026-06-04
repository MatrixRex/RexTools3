import bpy
import bmesh
from bpy.types import Operator

addon_keymaps = []

class REXTOOLS3_OT_ContextAwareSelect(Operator):
    """Context-aware selection: Linked select for Vertices/Faces/Curves, Loop select for Edges, triggered on double-click"""
    bl_idname = "rextools3.context_aware_select"
    bl_label = "Context Aware Select"
    bl_description = "Double-click to select linked (vertices/faces/curves) or loops (edges)"
    bl_options = {'REGISTER', 'UNDO'}

    # Linked Selection properties (Vertex/Face Mode)
    delimit: bpy.props.EnumProperty(
        name="Delimit",
        description="Limit selection boundaries",
        options={'ENUM_FLAG'},
        items=(
            ('NORMAL', "Normal", "Delimit by face directions"),
            ('MATERIAL', "Material", "Delimit by face material"),
            ('SEAM', "Seam", "Delimit by edge seams"),
            ('SHARP', "Sharp", "Delimit by sharp edges"),
            ('UV', "UV", "Delimit by UV coordinates"),
        ),
        default=set(),
    )

    # Loop Selection properties (Edge Mode)
    ring: bpy.props.BoolProperty(
        name="Ring",
        description="Select an edge ring instead of a loop",
        default=False,
    )

    # Hidden toggle property to track shift modifier between invoke and execute
    toggle_loop: bpy.props.BoolProperty(
        name="Toggle Loop",
        options={'HIDDEN'},
        default=False,
    )

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        
        if obj and obj.type == 'MESH' and context.mode == 'EDIT_MESH':
            select_mode = context.tool_settings.mesh_select_mode
            if select_mode[0] or select_mode[2]:
                # Show delimit options in Vertex or Face selection mode
                layout.prop(self, "delimit")
            elif select_mode[1]:
                # Show ring select options in Edge selection mode
                layout.prop(self, "ring")

    def execute(self, context):
        obj = context.active_object
        if not obj:
            return {'CANCELLED'}

        if obj.type == 'MESH' and context.mode == 'EDIT_MESH':
            select_mode = context.tool_settings.mesh_select_mode

            if select_mode[0] or select_mode[2]:
                # Run linked selection
                bpy.ops.mesh.select_linked(delimit=self.delimit)
                return {'FINISHED'}

            elif select_mode[1]:
                # In execute (Redo adjustments), use loop_multi_select.
                # This works on the seed selection restored by Blender's undo stack,
                # converting the selection between loop/ring without needing mouse coordinates.
                bpy.ops.mesh.loop_multi_select(ring=self.ring)
                return {'FINISHED'}

        elif obj.type == 'CURVE' and context.mode == 'EDIT_CURVE':
            # Check if there is any selected control point/bezier point
            has_selection = False
            for spline in obj.data.splines:
                if any(p.select_control_point for p in spline.bezier_points) or any(p.select for p in spline.points):
                    has_selection = True
                    break

            if not has_selection:
                return {'CANCELLED'}

            # Run curve linked selection
            bpy.ops.curve.select_linked()
            return {'FINISHED'}

        return {'CANCELLED'}

    def invoke(self, context, event):
        # Pass through if any other modifier keys are held
        if event.ctrl or event.alt or event.oskey:
            return {'PASS_THROUGH'}

        # Ensure we are in Edit Mode on a mesh or curve object
        obj = context.active_object
        if not obj:
            return {'PASS_THROUGH'}

        if obj.type == 'MESH' and context.mode == 'EDIT_MESH':
            select_mode = context.tool_settings.mesh_select_mode
            bm = bmesh.from_edit_mesh(obj.data)

            # Check if there is any selection in the active selection mode
            has_selection = False
            if select_mode[0]:
                has_selection = any(v.select for v in bm.verts)
            elif select_mode[2]:
                has_selection = any(f.select for f in bm.faces)
            elif select_mode[1]:
                has_selection = any(e.select for e in bm.edges)

            # If no elements are selected, pass through
            if not has_selection:
                return {'PASS_THROUGH'}

            # Set initial toggle state based on shift modifier
            self.toggle_loop = event.shift

            # For initial selection in Edge mode, invoke the viewport-based loop_select
            # which utilizes mouse coordinates and correctly toggles/extends selection.
            if select_mode[1]:
                bpy.ops.mesh.loop_select(
                    'INVOKE_DEFAULT',
                    extend=False,
                    deselect=False,
                    toggle=self.toggle_loop,
                    ring=self.ring
                )
                return {'FINISHED'}

            # For Vertex/Face modes, execute directly
            return self.execute(context)

        elif obj.type == 'CURVE' and context.mode == 'EDIT_CURVE':
            # Check if there is any selected spline point
            has_selection = False
            for spline in obj.data.splines:
                if any(p.select_control_point for p in spline.bezier_points) or any(p.select for p in spline.points):
                    has_selection = True
                    break

            # If no elements are selected, pass through
            if not has_selection:
                return {'PASS_THROUGH'}

            return self.execute(context)

        return {'PASS_THROUGH'}


def register():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        # 1. Mesh Edit Mode Keymap
        km_mesh = kc.keymaps.get('Mesh')
        if not km_mesh:
            km_mesh = kc.keymaps.new(name='Mesh', space_type='EMPTY')

        kmi_mesh = km_mesh.keymap_items.new(
            REXTOOLS3_OT_ContextAwareSelect.bl_idname,
            type='LEFTMOUSE',
            value='DOUBLE_CLICK',
            any=True
        )
        addon_keymaps.append((km_mesh, kmi_mesh))

        # 2. Curve Edit Mode Keymap
        km_curve = kc.keymaps.get('Curve')
        if not km_curve:
            km_curve = kc.keymaps.new(name='Curve', space_type='EMPTY')

        kmi_curve = km_curve.keymap_items.new(
            REXTOOLS3_OT_ContextAwareSelect.bl_idname,
            type='LEFTMOUSE',
            value='DOUBLE_CLICK',
            any=True
        )
        addon_keymaps.append((km_curve, kmi_curve))


def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
