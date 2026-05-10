from __future__ import annotations
import glob
import json
import os
from typing import List

from fastapi import APIRouter, HTTPException
from models.schemas import VehicleSummary, VehicleFull, VehicleArmorResponse

router = APIRouter(prefix="/api/vehicles", tags=["vehicles"])


def _data_dir() -> str:
    return os.environ.get("DATA_DIR", "/app/data")


def _load_vehicle(vehicle_id: str) -> dict:
    path = os.path.join(_data_dir(), "vehicles", f"{vehicle_id}.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Vehicle '{vehicle_id}' not found")
    with open(path) as f:
        return json.load(f)


@router.get("", response_model=List[VehicleSummary])
def list_vehicles():
    pattern = os.path.join(_data_dir(), "vehicles", "*.json")
    results = []
    for path in sorted(glob.glob(pattern)):
        with open(path) as f:
            v = json.load(f)
        results.append(VehicleSummary(
            vehicleId=v["vehicleId"],
            displayName=v["displayName"],
            nation=v["nation"],
            type=v["type"],
            battleRating=v["battleRating"],
            rank=v["rank"],
            branch=v["branch"],
        ))
    return results


@router.get("/{vehicleId}", response_model=VehicleFull)
def get_vehicle(vehicleId: str):
    return _load_vehicle(vehicleId)


@router.get("/{vehicleId}/armor", response_model=VehicleArmorResponse)
def get_vehicle_armor(vehicleId: str):
    v = _load_vehicle(vehicleId)
    return VehicleArmorResponse(
        vehicleId=v["vehicleId"],
        damageParts=v["damageParts"],
        xrayViewerData=v.get("xrayViewerData"),
    )
