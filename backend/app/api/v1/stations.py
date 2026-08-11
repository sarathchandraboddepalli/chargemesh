"""ChargeMesh — Charging Station API Routes"""

import uuid

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select, text

from app.api.deps import CurrentOrg, DB
from app.models.network import ChargingNetwork, ChargingStation
from app.schemas.station import ChargingStationOut, NearbyStationQuery
from app.utils.geo_utils import haversine_km

router = APIRouter()


@router.get("", response_model=list[ChargingStationOut])
async def list_stations(
    current_org: CurrentOrg,
    db: DB,
    city: str | None = Query(None),
    available_only: bool = Query(False),
):
    q = select(ChargingStation)
    if city:
        q = q.where(ChargingStation.city.ilike(f"%{city}%"))
    if available_only:
        q = q.where(ChargingStation.available_connectors > 0, ChargingStation.is_operational == True)

    result = await db.execute(q)
    stations = result.scalars().all()
    out = []
    for s in stations:
        item = ChargingStationOut.model_validate(s)
        # Fetch network name
        net_result = await db.execute(select(ChargingNetwork).where(ChargingNetwork.id == s.network_id))
        net = net_result.scalar_one_or_none()
        if net:
            item.network_name = net.name
        out.append(item)
    return out


@router.get("/nearby", response_model=list[ChargingStationOut])
async def nearby_stations(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(10.0, ge=0.1, le=100.0),
    available_only: bool = Query(True),
    db: DB = None,
):
    """Public endpoint — station coordinates are not sensitive.
    Returns stations within radius_km of the given coordinates.
    Uses Haversine distance since earthdistance extension is optional.
    """
    q = select(ChargingStation).where(
        ChargingStation.latitude.isnot(None),
        ChargingStation.longitude.isnot(None),
    )
    if available_only:
        q = q.where(ChargingStation.available_connectors > 0, ChargingStation.is_operational == True)

    result = await db.execute(q)
    stations = result.scalars().all()

    nearby = []
    for s in stations:
        dist = haversine_km(latitude, longitude, float(s.latitude), float(s.longitude))
        if dist <= radius_km:
            item = ChargingStationOut.model_validate(s)
            nearby.append((dist, item))

    nearby.sort(key=lambda x: x[0])
    return [item for _, item in nearby]


@router.get("/{station_id}", response_model=ChargingStationOut)
async def get_station(station_id: uuid.UUID, db: DB):
    result = await db.execute(select(ChargingStation).where(ChargingStation.id == station_id))
    station = result.scalar_one_or_none()
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")
    return station


@router.post("/networks/{network_id}/sync")
async def sync_network_stations(network_id: uuid.UUID, current_org: CurrentOrg, db: DB):
    """Trigger a resync of stations from a charging network."""
    from app.tasks.station_tasks import sync_network_stations as sync_task
    sync_task.delay(str(network_id))
    return {"detail": f"Station sync queued for network {network_id}"}


@router.get("/{station_id}/health")
async def station_health(station_id: uuid.UUID, db: DB):
    result = await db.execute(select(ChargingStation).where(ChargingStation.id == station_id))
    station = result.scalar_one_or_none()
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")
    return {
        "station_id": station_id,
        "is_operational": station.is_operational,
        "available_connectors": station.available_connectors,
        "total_connectors": station.total_connectors,
        "last_status_update": station.last_status_update,
    }
