from __future__ import annotations
import json
import os

from fastapi import APIRouter, HTTPException
from models.schemas import ShellResponse

router = APIRouter(prefix="/api/shells", tags=["shells"])


def _data_dir() -> str:
    return os.environ.get("DATA_DIR", "/app/data")


@router.get("/{cannonId}", response_model=ShellResponse)
def get_shells(cannonId: str):
    path = os.path.join(_data_dir(), "shells", f"{cannonId}.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Cannon '{cannonId}' not found")
    with open(path) as f:
        return json.load(f)
