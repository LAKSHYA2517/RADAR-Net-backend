import requests
import os
from dotenv import load_dotenv

load_dotenv()

PRITHVI_API_URL=os.getenv("PRITHVI_API_URL")

def send_to_prithvi(start_coords, dest_coords):
    
    payload = {
        "start": start_coords,
        "destination": dest_coords
    }

    response = requests.post(PRITHVI_API_URL, json=payload)

    return response.json()
