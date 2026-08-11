"""ChargeMesh — API v1 Router"""

from fastapi import APIRouter

from app.api.v1 import (
    admin,
    analytics,
    auth,
    batteries,
    dispatch,
    driver_app,
    drivers,
    fleet,
    ledger,
    networks,
    oems,
    orgs,
    sessions,
    settlements,
    stations,
    swaps,
    telemetry,
    thermal,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(orgs.router, prefix="/orgs", tags=["organizations"])
api_router.include_router(fleet.router, prefix="/fleet", tags=["fleet"])
api_router.include_router(drivers.router, prefix="/drivers", tags=["drivers"])
api_router.include_router(stations.router, prefix="/stations", tags=["stations"])
api_router.include_router(networks.router, prefix="/networks", tags=["networks"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(telemetry.router, prefix="/telemetry", tags=["telemetry"])
api_router.include_router(batteries.router, prefix="/batteries", tags=["batteries"])
api_router.include_router(swaps.router, prefix="/swaps", tags=["swaps"])
api_router.include_router(ledger.router, prefix="/ledger", tags=["ledger"])
api_router.include_router(settlements.router, prefix="/ledger/settlements", tags=["settlements"])
api_router.include_router(dispatch.router, prefix="/dispatch", tags=["dispatch"])
api_router.include_router(thermal.router, prefix="/thermal", tags=["thermal"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(driver_app.router, prefix="/driver", tags=["driver-app"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(oems.router, prefix="/oems", tags=["oems"])
