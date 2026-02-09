import osmnx as ox
from typing import Tuple, Optional
from shapely.geometry import Point, LineString
import numpy as np
import networkx as nx

def get_nearest_node(G, lat: float, lon: float):
    """
    Find the closest node in the graph to given coordinates.
    
    Parameters:
    -----------
    G : nx.MultiDiGraph
        Road network graph
    lat, lon : float
        Coordinates to find nearest node to
    
    Returns:
    --------
    int
        Node ID of nearest node
    """
    if len(G.nodes) == 0:
        raise ValueError("Graph has no nodes!")
    
    # OSMnx expects X=Longitude, Y=Latitude
    nearest_node_id = ox.distance.nearest_nodes(G, X=lon, Y=lat)
    
    # Get node coordinates for verification
    node_data = G.nodes[nearest_node_id]
    print(f"Nearest node to ({lat:.4f}, {lon:.4f}): "
          f"Node {nearest_node_id} at ({node_data['y']:.4f}, {node_data['x']:.4f})")
    
    return nearest_node_id

def get_road_network(north, south, east, west, network_type="drive"):
    G = ox.graph_from_bbox(
        bbox=(west, south, east, north),
        network_type=network_type,
        simplify=True
    )
    return G


def grid_coords_to_latlon(grid_row: int, grid_col: int, 
                          north: float, south: float, 
                          east: float, west: float,
                          grid_shape: Tuple[int, int]) -> Tuple[float, float]:
    """Convert grid coordinates to latitude/longitude."""
    rows, cols = grid_shape
    lat = north - (grid_row / rows) * (north - south)
    lon = west + (grid_col / cols) * (east - west)
    return lat, lon


def latlon_to_grid_coords(lat: float, lon: float,
                          north: float, south: float,
                          east: float, west: float,
                          grid_shape: Tuple[int, int]) -> Tuple[int, int]:
    """Convert latitude/longitude to grid coordinates."""
    rows, cols = grid_shape
    
    row = int((north - lat) / (north - south) * rows)
    col = int((lon - west) / (east - west) * cols)
    
    if 0 <= row < rows and 0 <= col < cols:
        return row, col
    return None


def is_node_flooded(node_lat: float, node_lon: float, 
                    flood_grid: np.ndarray,
                    north: float, south: float, 
                    east: float, west: float) -> bool:
    """Check if a node location is flooded based on the grid."""
    grid_coords = latlon_to_grid_coords(node_lat, node_lon, north, south, 
                                        east, west, flood_grid.shape)
    
    if grid_coords is None:
        return False
    
    row, col = grid_coords
    return flood_grid[row, col] == 1


def is_edge_flooded(edge_geometry: LineString,
                    flood_grid: np.ndarray,
                    north: float, south: float,
                    east: float, west: float,
                    sample_points: int = 10) -> bool:
    """
    Check if an edge passes through flooded areas by sampling points along it.
    
    Parameters:
    -----------
    edge_geometry : LineString
        The geometry of the road edge
    flood_grid : np.ndarray
        2D array where 1 = flooded, 0 = dry
    north, south, east, west : float
        Bounding box coordinates
    sample_points : int
        Number of points to sample along the edge (higher = more accurate)
    
    Returns:
    --------
    bool
        True if any point along the edge is in a flooded zone
    """
    # Sample points along the line
    distances = np.linspace(0, edge_geometry.length, sample_points)
    
    for distance in distances:
        point = edge_geometry.interpolate(distance)
        lon, lat = point.x, point.y
        
        if is_node_flooded(lat, lon, flood_grid, north, south, east, west):
            return True
    
    return False

def get_reachable_roads(north: float, south: float, east: float, west: float,
                        flood_grid: np.ndarray,
                        network_type: str = 'drive',
                        start_node: Optional[int] = None,
                        edge_sample_points: int = 10) -> nx.MultiDiGraph:
    """
    Get reachable roads during a flood by removing flooded intersections
    AND flooded edges, keeping only the largest connected component.
    
    Parameters:
    -----------
    north, south, east, west : float
        Bounding box coordinates in latitude/longitude
    flood_grid : np.ndarray
        2D array where 1 = flooded zone, 0 = dry ground
    network_type : str
        Type of street network ('drive', 'walk', 'bike', 'all')
    start_node : int, optional
        If provided, only keep the connected component containing this node
    edge_sample_points : int
        Number of points to sample along each edge to check for flooding
    
    Returns:
    --------
    nx.MultiDiGraph
        Graph containing only reachable (non-flooded) roads
    """
    # Download the road network
    print("Downloading road network...")
    G = get_road_network(north, south, east, west, network_type)
    print(f"Original network: {len(G.nodes)} nodes, {len(G.edges)} edges")
    
    # Identify flooded nodes
    print("Identifying flooded intersections...")
    flooded_nodes = []
    
    for node, data in G.nodes(data=True):
        lat = data['y']
        lon = data['x']
        
        if is_node_flooded(lat, lon, flood_grid, north, south, east, west):
            flooded_nodes.append(node)
    
    print(f"Found {len(flooded_nodes)} flooded intersections")
    
    # Remove flooded nodes and their connected edges
    G.remove_nodes_from(flooded_nodes)
    print(f"After removing flooded nodes: {len(G.nodes)} nodes, {len(G.edges)} edges")
    
    # Identify and remove flooded edges
    print("Identifying flooded road segments...")
    flooded_edges = []
    
    for u, v, key, data in G.edges(keys=True, data=True):
        # Get edge geometry
        if 'geometry' in data:
            edge_geom = data['geometry']
        else:
            # If no geometry, create a straight line between nodes
            u_data = G.nodes[u]
            v_data = G.nodes[v]
            edge_geom = LineString([(u_data['x'], u_data['y']), 
                                   (v_data['x'], v_data['y'])])
        
        # Check if edge passes through flooded area
        if is_edge_flooded(edge_geom, flood_grid, north, south, east, west, 
                          sample_points=edge_sample_points):
            flooded_edges.append((u, v, key))
    
    print(f"Found {len(flooded_edges)} flooded road segments")
    
    # Remove flooded edges
    G.remove_edges_from(flooded_edges)
    print(f"After removing flooded edges: {len(G.nodes)} nodes, {len(G.edges)} edges")
    
    # Convert to undirected to find connected components
    G_undirected = G.to_undirected()
    
    # Get the largest connected component (or component containing start_node)
    if start_node is not None and start_node in G:
        components = list(nx.connected_components(G_undirected))
        main_component = None
        for comp in components:
            if start_node in comp:
                main_component = comp
                break
        if main_component is None:
            print(f"Warning: start_node {start_node} not found in any component")
            main_component = max(nx.connected_components(G_undirected), key=len)
    else:
        main_component = max(nx.connected_components(G_undirected), key=len)
    
    # Filter the original directed graph to keep only nodes in main component
    G_reachable = G.subgraph(main_component).copy()
    
    print(f"Main connected component: {len(G_reachable.nodes)} nodes, {len(G_reachable.edges)} edges")
    
    return G_reachable
