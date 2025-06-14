from math import radians, cos, sin, asin, sqrt


def get_bounding_box(lat: float, long: float, distance: float | int = 700) -> dict:
    # 364000 approx feet in a degree
    lat_offset = float(distance) / 364000
    long_offset = float(distance) / (364000 * cos(radians(lat)))

    return {
        "sw": lat - lat_offset,
        "swLng": long - long_offset,
        "neLat": lat + lat_offset,
        "neLng": long + long_offset,
    }


def haversine(lat1, lon1, lat2, lon2):
    R = 3959.87433  # this is in miles.  For Earth radius in kilometers use 6372.8 km

    dLat = radians(lat2 - lat1)
    dLon = radians(lon2 - lon1)
    lat1 = radians(lat1)
    lat2 = radians(lat2)

    a = sin(dLat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dLon / 2) ** 2
    c = 2 * asin(sqrt(a))

    return R * c


def is_within_feet(
    lat1: float, long1: float, lat2: float, long2: float, feet: float
) -> bool:
    return haversine(lat1, long1, lat2, long2) <= (feet / 5820.0)
