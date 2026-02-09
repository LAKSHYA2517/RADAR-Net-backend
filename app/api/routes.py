from app.utils.a_star import get_a_star_geojson
from app.utils.osm import get_nearest_node, get_reachable_roads
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from ..models.request_models import RouteRequest
from ..services.geocoding_service import geocode_location
from ..services.prithvi_client import send_to_prithvi

import numpy as np

router = APIRouter()

@router.post("/process")
def process_route(data: RouteRequest):
    # Step 1: Convert destination string → coordinates
    dest_coords = geocode_location(data.destination)

    if dest_coords is None:
        raise HTTPException(status_code=404, detail="Location not found")

    start_coords = {
        "lat": data.start_lat,
        "lon": data.start_lon
    }

    # Step 2: Send to Prithvi model backend
    # result = send_to_prithvi(start_coords, dest_coords)

    
    north = 12.98
    south = 12.95
    east = 77.62
    west = 77.58

    grid_shape = (20, 20)
    flood_grid = np.random.choice([0, 1], size=grid_shape, p=[0.85, 0.15])
    
    start_lat = 12.970
    start_lon = 77.585
    
    end_lat = 12.955
    end_lon = 77.610
    
    try:
        G_reachable = get_reachable_roads(north=north, south=south, east=east, west=west,flood_grid=flood_grid,network_type='drive',edge_sample_points=15)
        
        print(f"\nReachable nodes: {len(G_reachable.nodes)}")
        print(f"Reachable edges: {len(G_reachable.edges)}")

        route_geojson = None
        
        if len(G_reachable.nodes) >= 2:
            print(f"\n--- Finding A* Route ---")
            print(f"Start coordinates: ({start_lat}, {start_lon})")
            print(f"End coordinates: ({end_lat}, {end_lon})")
            
            # Find nearest nodes to the user's coordinates
            start_node = get_nearest_node(G_reachable, start_lat, start_lon)
            end_node = get_nearest_node(G_reachable, end_lat, end_lon)
            
            # Calculate route using A*
            route_geojson = get_a_star_geojson(G_reachable, start_node, end_node)
            
            if route_geojson is None:
                return JSONResponse(status_code=404, content={"message": "No route found. Possible reasons: start and end are in different disconnected components, or flood has isolated one or both locations."})
        else:
            return JSONResponse(status_code=401, content={"message": "Need atleast 2 nodes to compute path"})
        
        return route_geojson
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": "Error in OSM section"})
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()