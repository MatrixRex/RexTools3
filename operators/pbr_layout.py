# operators/pbr_layout.py
import bpy
from bpy.types import Operator
from mathutils import Vector

class PBR_OT_ArrangeNodes(Operator):
    bl_idname = "pbr.arrange_nodes"
    bl_label = "Arrange PBR Nodes"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        if not obj or not obj.active_material:
            return {'CANCELLED'}
            
        material = obj.active_material
        if not material.use_nodes:
            return {'CANCELLED'}
            
        self.arrange_pbr_nodes(material)
        return {'FINISHED'}
    
    @staticmethod
    def get_node_bounds(node):
        """Get the bounding box of a node in 2D space"""
        # Node dimensions vary by type, these are approximate Blender defaults
        node_dimensions = {
            'BSDF_PRINCIPLED': (240, 600),
            'OUTPUT_MATERIAL': (140, 80),
            'TEX_IMAGE': (240, 200),
            'MIX_RGB': (140, 180),
            'NORMAL_MAP': (140, 120),
            'MATH': (140, 120),
            'MAPPING': (140, 200),
            'TEX_COORD': (140, 120),
            'SEPRGB': (100, 100),
            'COMBRGB': (100, 100),
            'REROUTE': (16, 16),
        }
        
        # Get dimensions for this node type, fallback to generic size
        width, height = node_dimensions.get(node.type, (140, 120))
        
        # Calculate bounds based on node location (bottom-left is the pivot)
        x, y = node.location
        return {
            'min_x': x,
            'max_x': x + width,
            'min_y': y - height,  # Blender nodes grow upward from location
            'max_y': y,
            'width': width,
            'height': height,
            'center_x': x + width/2,
            'center_y': y - height/2
        }
    
    @staticmethod
    def nodes_overlap(node1, node2, padding=20):
        """Check if two nodes overlap with optional padding"""
        bounds1 = PBR_OT_ArrangeNodes.get_node_bounds(node1)
        bounds2 = PBR_OT_ArrangeNodes.get_node_bounds(node2)
        
        # Add padding to bounds
        return not (bounds1['max_x'] + padding < bounds2['min_x'] or
                   bounds2['max_x'] + padding < bounds1['min_x'] or
                   bounds1['max_y'] + padding < bounds2['min_y'] or
                   bounds2['max_y'] + padding < bounds1['min_y'])
    
    @staticmethod
    def find_non_overlapping_position(node, existing_nodes, preferred_y=None, padding=20):
        """Find a position for a node that doesn't overlap with existing nodes"""
        bounds = PBR_OT_ArrangeNodes.get_node_bounds(node)
        
        # If no preferred Y, use current position
        if preferred_y is None:
            preferred_y = node.location.y
            
        # Try the preferred Y position first
        test_y = preferred_y
        node.location = (node.location.x, test_y)
        
        max_attempts = 50
        attempt = 0
        direction = 1  # 1 for down, -1 for up
        step = bounds['height'] + padding
        
        while attempt < max_attempts:
            # Update node position for bounds calculation
            node.location = (node.location.x, test_y)
            
            # Check for overlaps
            has_overlap = False
            for other_node in existing_nodes:
                if other_node != node and PBR_OT_ArrangeNodes.nodes_overlap(node, other_node, padding):
                    has_overlap = True
                    break
            
            if not has_overlap:
                return test_y
            
            # Move to next position
            if direction == 1:
                test_y -= step
                if attempt % 2 == 1:  # Every other attempt, try going up instead
                    direction = -1
                    test_y = preferred_y + step
            else:
                test_y += step
                direction = 1
                test_y = preferred_y - step * (attempt // 2 + 2)
                
            attempt += 1
        
        # If we can't find a good position, just use the preferred Y
        return preferred_y
    
    @staticmethod
    def arrange_pbr_nodes(material):
        """Arrange nodes in a clean layout based on their connections to Principled BSDF"""
        nodes = material.node_tree.nodes
        links = material.node_tree.links
        
        # Find the Principled BSDF and Output nodes
        principled = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
        output = next((n for n in nodes if n.type == 'OUTPUT_MATERIAL'), None)
        
        if not principled:
            return
            
        # Position the main nodes first
        if output:
            output.location = (400, 0)
        principled.location = (0, 0)
        
        # Define preferred input socket positions
        socket_preferences = {
            'Base Color': 200,
            'Metallic': 100,
            'Roughness': 0,
            'Normal': -100,
            'Alpha': -200,
            'Specular': 50,
            'Transmission': -50,
            'Emission': 150,
        }
        
        # Track positioned nodes to avoid overlaps
        positioned_nodes = [principled]
        if output:
            positioned_nodes.append(output) 
        
        # Arrange nodes connected to each input
        chains_to_position = []
        
        # First pass: collect all chains
        for socket_name, preferred_y in socket_preferences.items():
            inp = principled.inputs.get(socket_name)
            if not inp or not inp.is_linked:
                continue
                
            # Get the connected node chain
            connected_node = inp.links[0].from_node
            chain = PBR_OT_ArrangeNodes.get_node_chain(connected_node)
            chains_to_position.append((chain, preferred_y, socket_name))
        
        # Sort chains by preferred Y position (top to bottom)
        chains_to_position.sort(key=lambda x: x[1], reverse=True)
        
        # Second pass: position chains avoiding overlaps
        for chain, preferred_y, socket_name in chains_to_position:
            PBR_OT_ArrangeNodes.position_node_chain(chain, preferred_y, positioned_nodes)
            positioned_nodes.extend(chain)
    
    @staticmethod
    def get_node_chain(start_node):
        """Get all nodes in a chain leading to the start node"""
        chain = []
        visited = set()  # Prevent infinite loops
        current = start_node
        
        while current and current not in visited:
            visited.add(current)
            chain.append(current)
            
            # Find the next node in the chain (prioritize Color/Value inputs for textures)
            next_node = None
            
            # For image texture nodes, look for mapping or coordinate nodes
            if current.type == 'TEX_IMAGE':
                vector_input = current.inputs.get('Vector')
                if vector_input and vector_input.is_linked:
                    next_node = vector_input.links[0].from_node
            else:
                # For other nodes, find the first connected input
                for inp in current.inputs:
                    if inp.is_linked and inp.name in ['Color', 'Color1', 'Value', 'Vector']:
                        next_node = inp.links[0].from_node
                        break
                        
                # If no primary input found, take any connected input
                if not next_node:
                    for inp in current.inputs:
                        if inp.is_linked:
                            next_node = inp.links[0].from_node
                            break
                            
            current = next_node
            
        return chain  # Don't reverse - keep the natural order from Principled BSDF outward
    
    @staticmethod
    def position_node_chain(chain, preferred_y, existing_nodes, padding=30):
        """Position a chain of nodes horizontally, avoiding overlaps"""
        if not chain:
            return
            
        x_spacing = 280  # Space between nodes in chain
        start_x = -280  # Start closer to the Principled BSDF
        
        # Position each node in the chain from right to left
        # chain[0] is the node directly connected to Principled BSDF
        # chain[-1] is the furthest upstream node (like texture)
        for i, node in enumerate(chain):
            x_pos = start_x - (i * x_spacing)  # Each subsequent node goes further left
            
            # Set initial position
            node.location = (x_pos, preferred_y)
            
            # Find non-overlapping Y position
            final_y = PBR_OT_ArrangeNodes.find_non_overlapping_position(
                node, existing_nodes, preferred_y, padding
            )
            
            node.location = (x_pos, final_y)
            
            # For chains, subsequent nodes should try to stay aligned
            if i > 0:
                preferred_y = final_y


class PBR_OT_AutoArrangeNodes(Operator):
    bl_idname = "pbr.auto_arrange_nodes" 
    bl_label = "Auto Arrange Nodes"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # This operator can be called automatically after texture assignment
        return PBR_OT_ArrangeNodes.execute(self, context)