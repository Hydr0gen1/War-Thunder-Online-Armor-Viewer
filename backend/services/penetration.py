from __future__ import annotations
import math
from typing import Any, Dict, List, Tuple

from services.armor_class import get_multiplier
from models.schemas import LayerResult, PenCheckResponse


# --- Shell pen interpolation ------------------------------------------------

def _interp_pen(pen_curve: List[Dict], range_m: float) -> float:
    """Piecewise linear interpolation over a pen curve."""
    if not pen_curve:
        return 0.0
    if range_m <= pen_curve[0]["range_m"]:
        return float(pen_curve[0]["pen_mm"])
    if range_m >= pen_curve[-1]["range_m"]:
        return float(pen_curve[-1]["pen_mm"])
    for i in range(len(pen_curve) - 1):
        r0, p0 = pen_curve[i]["range_m"], pen_curve[i]["pen_mm"]
        r1, p1 = pen_curve[i + 1]["range_m"], pen_curve[i + 1]["pen_mm"]
        if r0 <= range_m <= r1:
            t = (range_m - r0) / (r1 - r0)
            return p0 + t * (p1 - p0)
    return float(pen_curve[-1]["pen_mm"])


def get_shell_pen(round_data: Dict[str, Any], range_m: float) -> float:
    pen_curve = round_data.get("penCurve")
    flat = round_data.get("penetration_flat_mm")
    if pen_curve:
        return _interp_pen(pen_curve, range_m)
    if flat is not None:
        return float(flat)
    return 0.0


# --- LOS multiplier ---------------------------------------------------------

_MAX_LOS = 2.0  # cap for variable-thickness zones


def _los_multiplier(angle_deg: float, variable_thickness: bool) -> float:
    """1 / cos(angle). Capped at MAX_LOS for variableThickness zones."""
    if angle_deg >= 90.0:
        return _MAX_LOS
    rad = math.radians(angle_deg)
    mult = 1.0 / math.cos(rad)
    if variable_thickness:
        return min(mult, _MAX_LOS)
    return mult


# --- Effective thickness per layer ------------------------------------------

def _effective_layer(
    thickness: float,
    armor_class: str,
    quality: float,
    variable: bool,
    angle_deg: float,
    shell_type: str,
) -> float:
    mult = get_multiplier(armor_class, shell_type)
    los = _los_multiplier(angle_deg, variable)
    return thickness * mult * quality * los


# --- Zone resolver ----------------------------------------------------------

def _collect_layers(
    zone: Dict[str, Any],
    zone_name: str,
    angle_deg: float,
    shell_type: str,
) -> List[LayerResult]:
    """
    Recursively collect effective-thickness layers for a zone.
    Groups: iterate children sequentially.
    Leaf zones: single layer.
    """
    results: List[LayerResult] = []

    if zone.get("_isModule") or zone.get("_isCrew"):
        return results

    if zone.get("_isGroup"):
        children = zone.get("children", {})
        for child_name, child in children.items():
            results.extend(_collect_layers(child, child_name, angle_deg, shell_type))
        return results

    thickness = float(zone.get("armorThickness", 0.0))
    armor_class = zone.get("armorClass", "RHA_tank")
    quality = float(zone.get("genericArmorQuality", 1.0))
    variable = bool(zone.get("variableThickness", False))

    effective = _effective_layer(thickness, armor_class, quality, variable, angle_deg, shell_type)
    results.append(LayerResult(
        part=zone_name,
        nominal=thickness,
        effective=round(effective, 1),
        armorClass=armor_class,
    ))
    return results


# --- Main entry point -------------------------------------------------------

def calculate_penetration(
    vehicle_data: Dict[str, Any],
    zone_name: str,
    impact_angle_deg: float,
    round_data: Dict[str, Any],
    range_m: float,
    shell_type: str,
) -> PenCheckResponse:
    damage_parts = vehicle_data.get("damageParts", {})
    zone = damage_parts.get(zone_name)
    if zone is None:
        raise ValueError(f"Zone '{zone_name}' not found in vehicle damage parts")

    layers = _collect_layers(zone, zone_name, impact_angle_deg, shell_type)

    total_nominal = sum(l.nominal for l in layers)
    total_effective = sum(l.effective for l in layers)

    shell_pen = get_shell_pen(round_data, range_m)
    penetrated = shell_pen > total_effective
    margin = round(shell_pen - total_effective, 1)

    return PenCheckResponse(
        zoneName=zone_name,
        nominalThickness_mm=round(total_nominal, 1),
        effectiveThickness_mm=round(total_effective, 1),
        shellPen_mm=round(shell_pen, 1),
        penetrated=penetrated,
        marginMm=margin,
        layers=layers,
    )
