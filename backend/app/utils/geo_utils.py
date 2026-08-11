"""
ChargeMesh — Geographic Utilities
Haversine distance calculation and earthdistance query helpers.
"""

import math
from typing import Optional


EARTH_RADIUS_KM = 6371.0


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on Earth using Haversine formula.

    Args:
        lat1, lon1: First point (decimal degrees)
        lat2, lon2: Second point (decimal degrees)

    Returns:
        Distance in kilometers
    """
    lat1_r = math.radians(lat1)
    lat2_r = math.radians(lat2)
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)

    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(d_lon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))
    return EARTH_RADIUS_KM * c


def earthdistance_sql_filter(
    latitude: float,
    longitude: float,
    radius_km: float,
    lat_column: str = "latitude",
    lon_column: str = "longitude",
) -> str:
    """
    Generate SQL WHERE clause for proximity filtering using PostgreSQL earthdistance extension.
    Requires: CREATE EXTENSION cube; CREATE EXTENSION earthdistance;

    Usage:
        WHERE earth_box(ll_to_earth(:lat, :lon), :radius_m) @> ll_to_earth(latitude, longitude)
        AND earth_distance(ll_to_earth(:lat, :lon), ll_to_earth(latitude, longitude)) <= :radius_m

    Args:
        latitude, longitude: Center point
        radius_km: Search radius in kilometers
        lat_column, lon_column: Column names in the target table

    Returns:
        SQL fragment (use with parameterized query — add :lat, :lon, :radius_m params)
    """
    return (
        f"earth_box(ll_to_earth(:lat, :lon), :radius_m) @> ll_to_earth({lat_column}, {lon_column}) "
        f"AND earth_distance(ll_to_earth(:lat, :lon), ll_to_earth({lat_column}, {lon_column})) <= :radius_m"
    )


def bounding_box(
    latitude: float,
    longitude: float,
    radius_km: float,
) -> tuple[float, float, float, float]:
    """
    Calculate a bounding box for initial filtering before precise distance calculation.
    Returns (min_lat, min_lon, max_lat, max_lon).
    Useful for pre-filtering rows before the more expensive Haversine calculation.
    """
    # 1 degree of latitude ≈ 111 km
    lat_delta = radius_km / 111.0
    # 1 degree of longitude varies with latitude
    lon_delta = radius_km / (111.0 * math.cos(math.radians(latitude)))

    return (
        latitude - lat_delta,
        longitude - lon_delta,
        latitude + lat_delta,
        longitude + lon_delta,
    )
