# operators/pbr_layout.py
import bpy
from bpy.types import Operator
from mathutils import Vector
from collections import deque

class PBR_OT_ArrangeNodes(Operator):
    bl_idname = "pbr.arrange_nodes"
    bl_label = "Arrange PBR Nodes"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        if not obj or not obj.active_material:
            self.report({'WARNING'}, "No active material")
            return {'CANCELLED'}
            
        mat = obj.active_material
        if not mat.use_nodes:
            self.report({'WARNING'}, "Material does not use nodes")
            return {'CANCELLED'}
            
        self.arrange_pbr_tree(mat)
        return {'FINISHED'}
    
    def get_node_height(self, node):
        # Approximate heights of Blender 4.x nodes (used for stacking offsets)
        h_map = {
            'BSDF_PRINCIPLED': 650,
            'OUTPUT_MATERIAL': 120,
            'TEX_IMAGE': 260,
            'MIX': 220,
            'MIX_RGB': 220,
            'MATH': 140,
            'NORMAL_MAP': 160,
            'SEPARATE_RGB': 160,
            'MAPPING': 240,
            'TEX_COORD': 160,
            'ATTRIBUTE': 160,
            'RGB': 150,
            'VALTORGB': 200, # Color Ramp
        }
        return h_map.get(node.type, 180)

    def arrange_pbr_tree(self, mat):
        nodes = mat.node_tree.nodes
        # Find the main BSDF
        principled = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if not principled:
            return

        # 1. Output/Principled baseline
        output = next((n for n in nodes if n.type == 'OUTPUT_MATERIAL'), None)
        if output:
            output.location = (400, 0)
        principled.location = (0, 0)

        # 2. Priority mapping for vertical alignment
        # Higher numbers will be positioned higher in the Y axis
        prio_map = {
            'Base Color': 1000,
            'Subsurface Weight': 950,
            'Metallic': 900,
            'Specular IOR Level': 850,
            'Roughness': 800,
            'Transmission Weight': 700,
            'Alpha': 600,
            'Normal': 500,
            'Emission Color': 400,
            'Displacement': 200,
        }

        # 3. BFS to calculate Distances (X Level) and Priorities (Y Order)
        # Using deque for efficient pops
        node_levels = {principled: 0}
        node_prios = {principled: 2000} # Internal priority for the root
        
        queue = deque()
        # Initialize queue from BSDF inputs
        for inp in principled.inputs:
            if inp.is_linked:
                # Get slot priority
                p = prio_map.get(inp.name, 0)
                if not p:
                    # Fallback heuristics for custom or unnamed sockets
                    if 'Color' in inp.name: p = 850
                    elif 'Normal' in inp.name: p = 500
                    else: p = 100
                
                for link in inp.links:
                    queue.append((link.from_node, 1, p))

        # BFS Traversal
        while queue:
            node, level, prio = queue.popleft()
            
            # Rule: Always record the LONGEST chain distance for a node (e.g. if shared between Alpha and Base Color)
            if node not in node_levels or level > node_levels[node]:
                node_levels[node] = level
            
            # Rule: Always record the HIGHEST priority (e.g. if node feeds both Base Color and Roughness)
            if node not in node_prios or prio > node_prios[node]:
                node_prios[node] = prio
                
            # Traverse backwards into inputs of current node
            for inp_socket in node.inputs:
                if inp_socket.is_linked:
                    for link in inp_socket.links:
                        queue.append((link.from_node, level + 1, prio))

        # 4. Group by Level for column layout
        columns = {}
        for node, level in node_levels.items():
            if level == 0: continue
            if level not in columns: columns[level] = []
            columns[level].append(node)

        # 5. Position nodes per level
        X_STEP = 360  # Horizontal distance between levels
        Y_GAP = 60    # Vertical gap between stacked nodes

        for level_idx in sorted(columns.keys()):
            col_nodes = columns[level_idx]
            # Sort: Priority (Major), Name (Minor - for stability)
            col_nodes.sort(key=lambda n: (node_prios.get(n, 0), n.name), reverse=True)
            
            # Calculate total vertical span of this column
            total_height = sum(self.get_node_height(n) for n in col_nodes) + (len(col_nodes) - 1) * Y_GAP
            
            # Start from a centered offset
            current_y = total_height / 2
            x_pos = -level_idx * X_STEP
            
            for node in col_nodes:
                h = self.get_node_height(node)
                # Position node
                node.location = (x_pos, current_y)
                # Increment Y for the next node below
                current_y -= (h + Y_GAP)

class PBR_OT_AutoArrangeNodes(Operator):
    bl_idname = "pbr.auto_arrange_nodes" 
    bl_label = "Auto Arrange Nodes"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        return bpy.ops.pbr.arrange_nodes()

def menu_func(self, context):
    self.layout.separator()
    self.layout.operator(PBR_OT_ArrangeNodes.bl_idname, text="Arrange All Nodes", icon='NODETREE')

def register():
    bpy.types.NODE_MT_context_menu.append(menu_func)

def unregister():
    bpy.types.NODE_MT_context_menu.remove(menu_func)
