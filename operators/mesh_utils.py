import bmesh
import math

def find_next_edge(curr_edge, curr_vert, ref_angle, visited_edges, angle_tol, straight_tol, stop_at_seam):
    # 1. Check if we should stop here because of existing seams at this vertex
    if stop_at_seam:
        for edge in curr_vert.link_edges:
            if edge == curr_edge:
                continue
            # If there's an existing seam that isn't part of our current crawl/selection, stop.
            if edge.seam and (edge not in visited_edges):
                return None

    # Direction of entry into curr_vert
    v_prev = curr_edge.other_vert(curr_vert).co
    v_curr = curr_vert.co
    dir_in = (v_curr - v_prev).normalized()

    best_edge = None
    best_score = -2.0 # Higher is better (dot product)

    for edge in curr_vert.link_edges:
        if edge == curr_edge:
            continue
        if edge in visited_edges:
            continue
        
        # Geometric direction
        v_next = edge.other_vert(curr_vert).co
        dir_out = (v_next - v_curr).normalized()
        
        dot = dir_in.dot(dir_out)
        # angle_between_edges is the "turn" angle. 0 is straight, PI is U-turn.
        angle_between_edges = math.acos(max(-1.0, min(1.0, dot))) 
        
        if angle_between_edges > straight_tol:
            continue
            
        # Dihedral angle check
        try:
            phi = edge.calc_face_angle()
        except ValueError:
            phi = 0.0
            
        # Check if the face angle is close to our reference
        if abs(phi - ref_angle) > angle_tol:
            continue
            
        # Score is based on straightness (best alignment)
        if dot > best_score:
            best_score = dot
            best_edge = edge
    
    return best_edge

def crawl(start_edge, start_vert, ref_angle, visited_edges, angle_tol, straight_tol, stop_at_seam, max_steps=1000):
    curr_edge = start_edge
    curr_vert = start_vert
    
    for _ in range(max_steps):
        next_edge = find_next_edge(curr_edge, curr_vert, ref_angle, visited_edges, angle_tol, straight_tol, stop_at_seam)
        if not next_edge:
            break
        
        visited_edges.add(next_edge)
        # update curr_vert to the other end of next_edge
        curr_vert = next_edge.other_vert(curr_vert)
        curr_edge = next_edge
