from fastapi import APIRouter, HTTPException
from ..models.request_models import RouteRequest  # Import from request_models.py
from ..services.geocoding_service import geocode_location
from ..services.prithvi_client import send_to_prithvi

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
    result = send_to_prithvi(start_coords, dest_coords)

    return {
        "start": start_coords,
        "destination": dest_coords,
        "prithvi_response": result
    }