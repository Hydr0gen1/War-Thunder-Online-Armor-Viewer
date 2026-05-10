from __future__ import annotations
import json
import os

from fastapi import APIRouter, HTTPException
from models.schemas import PenCheckRequest, PenCheckResponse
from services.penetration import calculate_penetration

router = APIRouter(prefix="/api/penetration", tags=["penetration"])


def _data_dir() -> str:
    return os.environ.get("DATA_DIR", "/app/data")


def _load_json(subpath: str) -> dict:
    path = os.path.join(_data_dir(), subpath)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"File not found: {subpath}")
    with open(path) as f:
        return json.load(f)


@router.post("/check", response_model=PenCheckResponse)
def penetration_check(req: PenCheckRequest):
    vehicle = _load_json(f"vehicles/{req.vehicleId}.json")

    shell_ids = vehicle.get("shells", [])
    round_data = None
    for cannon_id in shell_ids:
        cannon = _load_json(f"shells/{cannon_id}.json")
        for r in cannon.get("rounds", []):
            if r["bulletName"] == req.shellBulletName:
                round_data = r
                break
        if round_data:
            break

    if round_data is None:
        raise HTTPException(status_code=404, detail=f"Shell '{req.shellBulletName}' not found for vehicle '{req.vehicleId}'")

    try:
        return calculate_penetration(
            vehicle_data=vehicle,
            zone_name=req.zoneName,
            impact_angle_deg=req.impactAngle_deg,
            round_data=round_data,
            range_m=req.range_m,
            shell_type=req.shellType,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
