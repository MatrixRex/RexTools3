import bpy

class MESH_OT_auto_rename_high_low(bpy.types.Operator):
    bl_idname = "mesh.auto_rename_high_low"
    bl_label = "Auto Rename High/Low"
    bl_description = "Rename selected meshes based on collection/vertex count and match origins"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        return len(selected_objects) >= 2

    @staticmethod
    def classify_low_high(selected_objects, context):
        low_suffixes = ["_low", "_lp", "_lowpoly", "low", "lp", "lowpoly", ".low", " low", "-low"]
        high_suffixes = ["_high", "_hp", "_highpoly", "high", "hp", "highpoly", ".high", " high", "-high"]
        
        # If exactly 2 objects, fall back to the existing logic for perfect backward compatibility
        if len(selected_objects) == 2:
            low, high = MESH_OT_auto_rename_high_low.detect_low_high(selected_objects, context)
            if low and high:
                return [low], [high]
            return [], []

        import re
        # Pattern to match the suffix, allowing word boundaries, numbers, underscores, or dots after it (variations/numbers)
        low_pat = re.compile(r'(_low|_lp|_lowpoly|low|lp|lowpoly)(\b|_|\.|\d)', re.IGNORECASE)
        high_pat = re.compile(r'(_high|_hp|_highpoly|high|hp|highpoly)(\b|_|\.|\d)', re.IGNORECASE)

        low_objs = []
        high_objs = []
        unclassified = []

        for obj in selected_objects:
            if obj.type != 'MESH':
                continue
                
            # 1. Check collections
            is_low = False
            is_high = False
            for col in obj.users_collection:
                n = col.name.lower()
                if any(s in n for s in ["low", "lp", "lowpoly"]):
                    is_low = True
                    break
                if any(s in n for s in ["high", "hp", "highpoly"]):
                    is_high = True
                    break
                    
            if is_low:
                low_objs.append(obj)
                continue
            if is_high:
                high_objs.append(obj)
                continue

            # 2. Check name
            n = obj.name.lower()
            if low_pat.search(n):
                low_objs.append(obj)
            elif high_pat.search(n):
                high_objs.append(obj)
            else:
                unclassified.append(obj)
                
        # 3. For unclassified objects, if we can guess from vertex count comparison to already classified objects:
        if unclassified and (low_objs or high_objs):
            # Calculate average vertex counts
            depsgraph = context.evaluated_depsgraph_get()
            def get_verts(o):
                return len(o.evaluated_get(depsgraph).data.vertices)
                
            low_verts = [get_verts(o) for o in low_objs]
            high_verts = [get_verts(o) for o in high_objs]
            
            avg_low = sum(low_verts) / len(low_verts) if low_verts else 0
            avg_high = sum(high_verts) / len(high_verts) if high_verts else 0
            
            for obj in unclassified:
                v = get_verts(obj)
                if avg_low > 0 and avg_high > 0:
                    # If we have both, classify by proximity to averages
                    if abs(v - avg_low) < abs(v - avg_high):
                        low_objs.append(obj)
                    else:
                        high_objs.append(obj)
                elif avg_low > 0:
                    # If we only have low, classify as high if it has significantly more vertices
                    if v > avg_low * 1.5:
                        high_objs.append(obj)
                    else:
                        low_objs.append(obj)
                elif avg_high > 0:
                    # If we only have high, classify as low if it has significantly fewer vertices
                    if v < avg_high * 0.7:
                        low_objs.append(obj)
                    else:
                        high_objs.append(obj)
        elif unclassified:
            # If all are unclassified and >= 2, sort by vertex count and split
            # The top half (fewer vertices) is low, bottom half is high
            depsgraph = context.evaluated_depsgraph_get()
            sorted_objs = sorted(unclassified, key=lambda o: len(o.evaluated_get(depsgraph).data.vertices))
            mid = len(sorted_objs) // 2
            low_objs = sorted_objs[:mid]
            high_objs = sorted_objs[mid:]
            
        return low_objs, high_objs

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

        if len(selected_objects) < 2:
            self.report({'ERROR'}, "Select at least 2 meshes")
            return {'CANCELLED'}

        low_objs, high_objs = self.classify_low_high(selected_objects, context)
        if not low_objs or not high_objs:
            self.report({'ERROR'}, "Could not differentiate Low and High poly objects")
            return {'CANCELLED'}

        # 3. Auto-fill the object name if it's currently empty
        if not props.obj_name:
            detected_name = self.clean_base_name(low_objs[0].name)
            if detected_name:
                props.obj_name = detected_name

        # If it's still empty and no name detected, use a fallback
        if not props.obj_name:
            props.obj_name = "Asset"

        # Pair objects by clean base name before renaming to match origins later
        low_by_base = {self.clean_base_name(o.name).lower(): o for o in low_objs}
        pairs = [] # list of (low_obj, high_obj)
        for high_obj in high_objs:
            base = self.clean_base_name(high_obj.name).lower()
            low_obj = low_by_base.get(base)
            if not low_obj and len(low_objs) == 1:
                low_obj = low_objs[0]
            if low_obj:
                pairs.append((low_obj, high_obj))

        # 4. Rename with conflict handling
        # Precompute target names before any renaming so we don't lose the original names
        low_targets = []
        used_low_names = set()
        for idx, low_obj in enumerate(low_objs):
            base = self.clean_base_name(low_obj.name)
            if not base or base.lower() == props.obj_name.lower():
                variation = f"{idx + 1}"
            else:
                variation = base
                
            if len(low_objs) == 1:
                target_name = props.obj_name + props.low_prefix
            else:
                target_name = f"{props.obj_name}{props.low_prefix}_{variation}"
                
            counter = 1
            temp_name = target_name
            while temp_name in used_low_names:
                temp_name = f"{target_name}_{counter}"
                counter += 1
            target_name = temp_name
            used_low_names.add(target_name)
            low_targets.append(target_name)

        high_targets = []
        used_high_names = set()
        for idx, high_obj in enumerate(high_objs):
            base = self.clean_base_name(high_obj.name)
            if not base or base.lower() == props.obj_name.lower():
                variation = f"{idx + 1}"
            else:
                variation = base
                
            if len(high_objs) == 1:
                target_name = props.obj_name + props.high_prefix
            else:
                target_name = f"{props.obj_name}{props.high_prefix}_{variation}"
                
            counter = 1
            temp_name = target_name
            while temp_name in used_high_names:
                temp_name = f"{target_name}_{counter}"
                counter += 1
            target_name = temp_name
            used_high_names.add(target_name)
            high_targets.append(target_name)

        def safe_rename(obj, target):
            if obj.name == target:
                return
            existing = bpy.data.objects.get(target)
            if existing and existing != obj:
                existing.name += ".old"
            obj.name = target

        # Use temporary names first to avoid swapping conflicts within selection
        for idx, obj in enumerate(low_objs):
            obj.name = f"__rextools_tmp_low_{idx}__"
        for idx, obj in enumerate(high_objs):
            obj.name = f"__rextools_tmp_high_{idx}__"

        # Apply target names
        for obj, target in zip(low_objs, low_targets):
            safe_rename(obj, target)
        for obj, target in zip(high_objs, high_targets):
            safe_rename(obj, target)
        
        # 5. Match Origins for paired objects
        for low_obj, high_obj in pairs:
            old_high_mat = high_obj.matrix_world.copy()
            target_mat = low_obj.matrix_world.copy()
            
            high_obj.matrix_world = target_mat
            high_obj.data.transform(target_mat.inverted() @ old_high_mat)
        
        context.view_layer.update()

        self.report({'INFO'}, f"Renamed & Matched Origins for {len(low_objs)} Low and {len(high_objs)} High meshes")
        return {'FINISHED'}


class MESH_OT_auto_rename_high_low_detect(bpy.types.Operator):
    bl_idname = "mesh.auto_rename_high_low_detect"
    bl_label = "Detect Name"
    bl_description = "Detect suggested base name from selection"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        return len(selected_objects) >= 2

    def execute(self, context):
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        low_objs, _ = MESH_OT_auto_rename_high_low.classify_low_high(selected_objects, context)
        if low_objs:
            name = MESH_OT_auto_rename_high_low.clean_base_name(low_objs[0].name)
            if name:
                context.scene.highlow_renamer_props.obj_name = name
        return {'FINISHED'}


class MESH_OT_auto_rename_high_low_pick_collection(bpy.types.Operator):
    bl_idname = "mesh.auto_rename_high_low_pick_collection"
    bl_label = "Pick Collection Name"
    bl_description = "Set base name from the collection name of the active/selected object"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        return len(selected_objects) >= 2

    def execute(self, context):
        col_name = None
        
        # 1. Try to get from active/selected object's collections
        obj = context.active_object
        if not obj or obj not in context.selected_objects:
            selected_meshes = [o for o in context.selected_objects if o.type == 'MESH']
            if selected_meshes:
                obj = selected_meshes[0]
                
        if obj and obj.users_collection:
            col_name = obj.users_collection[0].name
            
        # 2. Fallback to active collection of the context
        if not col_name and context.collection:
            col_name = context.collection.name
            
        if col_name:
            name = MESH_OT_auto_rename_high_low.clean_base_name(col_name)
            if name:
                context.scene.highlow_renamer_props.obj_name = name
                self.report({'INFO'}, f"Set name to collection: {name}")
                return {'FINISHED'}
                
        self.report({'WARNING'}, "No collection name could be resolved")
        return {'CANCELLED'}

