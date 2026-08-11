"""ChargeMesh — Charging Network Integrations API"""

import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentOrg, DB
from app.models.network import ChargingNetwork
from app.schemas.station import ChargingNetworkCreate, ChargingNetworkOut

router = APIRouter()


@router.get("", response_model=list[ChargingNetworkOut])
async def list_networks(current_org: CurrentOrg, db: DB):
    result = await db.execute(
        select(ChargingNetwork).where(ChargingNetwork.org_id == current_org.id)
    )
    return result.scalars().all()


@router.post("", response_model=ChargingNetworkOut, status_code=status.HTTP_201_CREATED)
async def add_network(payload: ChargingNetworkCreate, current_org: CurrentOrg, db: DB):
    network = ChargingNetwork(org_id=current_org.id, **payload.model_dump(exclude_none=True))
    db.add(network)
    await db.flush()
    return network


@router.get("/{network_id}", response_model=ChargingNetworkOut)
async def get_network(network_id: uuid.UUID, current_org: CurrentOrg, db: DB):
    result = await db.execute(
        select(ChargingNetwork).where(
            ChargingNetwork.id == network_id, ChargingNetwork.org_id == current_org.id
        )
    )
    network = result.scalar_one_or_none()
    if not network:
        raise HTTPException(status_code=404, detail="Network not found")
    return network


@router.put("/{network_id}", response_model=ChargingNetworkOut)
async def update_network(network_id: uuid.UUID, payload: ChargingNetworkCreate, current_org: CurrentOrg, db: DB):
    result = await db.execute(
        select(ChargingNetwork).where(
            ChargingNetwork.id == network_id, ChargingNetwork.org_id == current_org.id
        )
    )
    network = result.scalar_one_or_none()
    if not network:
        raise HTTPException(status_code=404, detail="Network not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(network, field, value)
    db.add(network)
    return network


@router.delete("/{network_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_network(network_id: uuid.UUID, current_org: CurrentOrg, db: DB):
    result = await db.execute(
        select(ChargingNetwork).where(
            ChargingNetwork.id == network_id, ChargingNetwork.org_id == current_org.id
        )
    )
    network = result.scalar_one_or_none()
    if not network:
        raise HTTPException(status_code=404, detail="Network not found")
    network.is_active = False
    db.add(network)


@router.get("/{network_id}/status")
async def network_status(network_id: uuid.UUID, current_org: CurrentOrg, db: DB):
    result = await db.execute(
        select(ChargingNetwork).where(
            ChargingNetwork.id == network_id, ChargingNetwork.org_id == current_org.id
        )
    )
    network = result.scalar_one_or_none()
    if not network:
        raise HTTPException(status_code=404, detail="Network not found")
    return {
        "network_id": network_id,
        "name": network.name,
        "connection_status": network.connection_status,
        "last_heartbeat_at": network.last_heartbeat_at,
        "station_count": network.station_count,
    }
