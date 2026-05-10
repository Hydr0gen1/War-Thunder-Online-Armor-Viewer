from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class BattleRating(BaseModel):
    arcade: float
    realistic: float
    simulator: float


class ShopArmor(BaseModel):
    hull: List[int]
    turret: List[int]


class VehicleSummary(BaseModel):
    vehicleId: str
    displayName: str
    nation: str
    type: str
    battleRating: BattleRating
    rank: int
    branch: str


class VehicleFull(BaseModel):
    vehicleId: str
    displayName: str
    nation: str
    operatorCountry: Optional[str] = None
    type: str
    branch: str
    rank: int
    battleRating: BattleRating
    shopArmor: Optional[ShopArmor] = None
    modelId: Optional[str] = None
    damageParts: Dict[str, Any]
    xrayViewerData: Optional[Dict[str, Any]] = None
    shells: List[str]


class VehicleArmorResponse(BaseModel):
    vehicleId: str
    damageParts: Dict[str, Any]
    xrayViewerData: Optional[Dict[str, Any]] = None


class PenCurvePoint(BaseModel):
    range_m: float
    pen_mm: float


class Round(BaseModel):
    bulletName: str
    bulletType: str
    displayName: str
    mass_kg: Optional[float] = None
    explosiveMass_kg: Optional[float] = None
    penetration_flat_mm: Optional[float] = None
    penCurve: Optional[List[PenCurvePoint]] = None
    demarreK: Optional[float] = None
    demarreSpeedPow: Optional[float] = None
    demarreMassPow: Optional[float] = None


class ShellResponse(BaseModel):
    cannonId: str
    caliber_mm: float
    rounds: List[Round]


class PenCheckRequest(BaseModel):
    vehicleId: str
    zoneName: str
    impactAngle_deg: float = 0.0
    shellBulletName: str
    range_m: float = 0.0
    shellType: str = "ke"


class LayerResult(BaseModel):
    part: str
    nominal: float
    effective: float
    armorClass: str


class PenCheckResponse(BaseModel):
    zoneName: str
    nominalThickness_mm: float
    effectiveThickness_mm: float
    shellPen_mm: float
    penetrated: bool
    marginMm: float
    layers: List[LayerResult]
