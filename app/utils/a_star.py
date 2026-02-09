from math import radians, cos, sin, asin, sqrt
import networkx as nx

def haversine_distance(u, v, G):
    """Heuristic function: straight-line distance in meters."""
    node_u = G.nodes[u]
    node_v = G.nodes[v]
    
    # OSMnx uses 'y' for lat, 'x' for lon
    lat1, lon1 = radians(node_u['y']), radians(node_u['x'])
    lat2, lon2 = radians(node_v['y']), radians(node_v['x'])
    
    dlon, dlat = lon2 - lon1, lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    return 2 * asin(sqrt(a)) * 6371000

def get_a_star_geojson(G, start_node, end_node):
    """
    Find shortest path using A* and return as GeoJSON.
    
    Parameters:
    -----------
    G : nx.MultiDiGraph
        Graph with reachable roads
    start_node : int
        Starting node ID
    end_node : int
        Destination node ID
    
    Returns:
    --------
    dict or None
        GeoJSON FeatureCollection with the route, or None if no path exists
    """
    try:
        # Run A* with haversine heuristic
        path = nx.astar_path(
            G, 
            start_node, 
            end_node, 
            heuristic=lambda u, v: haversine_distance(u, v, G), 
            weight='length'
        )
        
        # Calculate total distance from edge attributes
        total_dist = 0
        for u, v in zip(path[:-1], path[1:]):
            # For MultiDiGraph, get the edge with minimum length
            edge_data = min(G[u][v].values(), key=lambda x: x.get('length', 0))
            total_dist += edge_data.get('length', 0)
        
        # Build GeoJSON coordinates [longitude, latitude]
        line_coords = [[G.nodes[n]['x'], G.nodes[n]['y']] for n in path]
        
        geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "type": "route",
                        "distance_meters": round(total_dist, 2),
                        "distance_km": round(total_dist / 1000, 2),
                        "num_nodes": len(path),
                        "status": "dry"
                    },
                    "geometry": {
                        "type": "LineString",
                        "coordinates": line_coords
                    }
                }
            ]
        }
        
        print(f"\n✓ Route found: {len(path)} nodes, {total_dist/1000:.2f} km")
        return geojson
        
    except nx.NetworkXNoPath:
        print(f"\n✗ No path exists between nodes {start_node} and {end_node}")
        return None
    except Exception as e:
        print(f"\n✗ Error finding path: {e}")
        return None

