def create_bbox(start, end, buffer=0.02):
    min_lat = min(start["lat"], end["lat"]) - buffer
    max_lat = max(start["lat"], end["lat"]) + buffer
    min_lon = min(start["lon"], end["lon"]) - buffer
    max_lon = max(start["lon"], end["lon"]) + buffer

    return {
        "west": min_lon,
        "south": min_lat,
        "east": max_lon,
        "north": max_lat
    }
