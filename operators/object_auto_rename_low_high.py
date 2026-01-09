import bpy

class MESH_OT_auto_rename_high_low(bpy.types.Operator):
    bl_idname = "mesh.auto_rename_high_low"
    bl_label = "Auto Rename High/Low"
    bl_description = "Rename selected meshes based on collection/vertex count and match origins"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        props = context.scene.highlow_renamer_props

        if len(selected_objects) != 2:
            self.report({'ERROR'}, "Need two meshes only")
            return {'CANCELLED'}

    @staticmethod
    def detect_low_high(selected_objects, context):
        if len(selected_objects) != 2:
            return None, None
            
        obj1, obj2 = selected_objects
        
        # Suffixes to check
        low_suffixes = ["_low", "_lp", "_lowpoly", "low", "lp", "lowpoly", ".low", " low", "-low"]
        high_suffixes = ["_high", "_hp", "_highpoly", "high", "hp", "highpoly", ".high", " high", "-high"]
        
        def get_type_rating(obj):
            # Check collections
            for col in obj.users_collection:
                n = col.name.lower()
                if any(n.endswith(s) for s in low_suffixes):
                    return -2 # Strongly low
                if any(n.endswith(s) for s in high_suffixes):
                    return 2 # Strongly high
            
            # Check names
            n = obj.name.lower()
            if any(n.endswith(s) for s in low_suffixes):
                return -1 # Likely low
            if any(n.endswith(s) for s in high_suffixes):
                return 1 # Likely high
            return 0

        r1 = get_type_rating(obj1)
        r2 = get_type_rating(obj2)
        
        if r1 < r2:
            return obj1, obj2
        elif r2 < r1:
            return obj2, obj1
        else:
            # Vertex count fallback
            depsgraph = context.evaluated_depsgraph_get()
            v1 = len(obj1.evaluated_get(depsgraph).data.vertices)
            v2 = len(obj2.evaluated_get(depsgraph).data.vertices)
            if v1 > v2:
                return obj2, obj1
            else:
                return obj1, obj2

    @staticmethod
    def clean_base_name(name):
        import re
        # Remove trailing .001, .002 etc
        name = re.sub(r'\.\d{3,}$', '', name)
        
        low_suffixes = ["_low", "_lp", "_lowpoly", "low", "lp", "lowpoly", ".low", " low", "-low"]
        high_suffixes = ["_high", "_hp", "_highpoly", "high", "hp", "highpoly", ".high", " high", "-high"]
        
        # Strip common suffixes (case insensitive endswith)
        for s in low_suffixes + high_suffixes:
            if name.lower().endswith(s):
                name = name[:-len(s)]
                # Recursively check in case of multiple suffixes like Name_low.001
                return MESH_OT_auto_rename_high_low.clean_base_name(name)
        return name

    def execute(self, context):
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        props = context.scene.highlow_renamer_props

        if len(selected_objects) != 2:
            self.report({'ERROR'}, "Need two meshes only")
            return {'CANCELLED'}

        low_poly, high_poly = self.detect_low_high(selected_objects, context)
        
        # 3. Auto-fill the object name if it's currently empty
        if not props.obj_name:
            detected_name = self.clean_base_name(low_poly.name)
            if detected_name:
                props.obj_name = detected_name

        # If it's still empty and no name detected, use a fallback
        if not props.obj_name:
            props.obj_name = "Asset"

        # 4. Rename with conflict handling
        target_low = props.obj_name + props.low_prefix
        target_high = props.obj_name + props.high_prefix

        def safe_rename(obj, target):
            if obj.name == target:
                return
            
            # If target name is taken by ANY other object
            existing = bpy.data.objects.get(target)
            if existing and existing != obj:
                # Rename the conflicting object to free up the name
                # We append .old and potentially another number if .old is taken
                existing.name += ".old"
            
            obj.name = target

        # Use temporary names first to avoid swapping conflicts within selection
        low_poly.name = "__rextools_tmp_low__"
        high_poly.name = "__rextools_tmp_high__"
        
        safe_rename(low_poly, target_low)
        safe_rename(high_poly, target_high)
        
        # 5. Match Origins
        old_high_mat = high_poly.matrix_world.copy()
        target_mat = low_poly.matrix_world.copy()
        
        high_poly.matrix_world = target_mat
        high_poly.data.transform(target_mat.inverted() @ old_high_mat)
        
        context.view_layer.update()

        self.report({'INFO'}, f"Renamed & Matched Origins: {low_poly.name}, {high_poly.name}")
        return {'FINISHED'}



class MESH_OT_auto_rename_high_low_detect(bpy.types.Operator):
    bl_idname = "mesh.auto_rename_high_low_detect"
    bl_label = "Detect Name"
    bl_description = "Detect suggested base name from selection"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        low_poly, _ = MESH_OT_auto_rename_high_low.detect_low_high(selected_objects, context)
        if low_poly:
            name = MESH_OT_auto_rename_high_low.clean_base_name(low_poly.name)
            if name:
                context.scene.highlow_renamer_props.obj_name = name
        return {'FINISHED'}

