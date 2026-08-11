"""ChargeMesh — Drivers API Routes"""

import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentOrg, DB
from app.models.vehicle import Driver
from app.schemas.driver import DriverCreate, DriverOut, DriverUpdate

router = APIRouter()


@router.get("", response_model=list[DriverOut])
async def list_drivers(current_org: CurrentOrg, db: DB):
    result = await db.execute(
        select(Driver).where(Driver.org_id == current_org.id, Driver.is_active == True)
    )
    return result.scalars().all()


@router.post("", response_model=DriverOut, status_code=status.HTTP_201_CREATED)
async def create_driver(payload: DriverCreate, current_org: CurrentOrg, db: DB):
    existing = await db.execute(select(Driver).where(Driver.phone == payload.phone))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Phone number already registered")

    driver = Driver(org_id=current_org.id, **payload.model_dump(exclude_none=True))
    db.add(driver)
    await db.flush()
    return driver


@router.get("/{driver_id}", response_model=DriverOut)
async def get_driver(driver_id: uuid.UUID, current_org: CurrentOrg, db: DB):
    result = await db.execute(
        select(Driver).where(Driver.id == driver_id, Driver.org_id == current_org.id)
    )
    driver = result.scalar_one_or_none()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver


@router.put("/{driver_id}", response_model=DriverOut)
async def update_driver(driver_id: uuid.UUID, payload: DriverUpdate, current_org: CurrentOrg, db: DB):
    result = await db.execute(
        select(Driver).where(Driver.id == driver_id, Driver.org_id == current_org.id)
    )
    driver = result.scalar_one_or_none()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(driver, field, value)
    db.add(driver)
    return driver


@router.delete("/{driver_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deregister_driver(driver_id: uuid.UUID, current_org: CurrentOrg, db: DB):
    result = await db.execute(
        select(Driver).where(Driver.id == driver_id, Driver.org_id == current_org.id)
    )
    driver = result.scalar_one_or_none()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    driver.is_active = False
    db.add(driver)
