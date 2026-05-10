#!/usr/bin/env python3
"""
Assemble per-vehicle JSON and shells JSON from raw War Thunder game file extracts.

Usage:
    python build_vehicle_json.py \
        --blk      path/to/sw_t_72m1.blk \
        --wpcost   path/to/wpcost.blk \
        --shop     path/to/shop.blk \
        --units    path/to/units.csv \
        --unittags path/to/unittags.blk \
        --cannon   path/to/2a46m.blk \
        --out-vehicles ./backend/data/vehicles \
        --out-shells   ./backend/data/shells

Output files:
    backend/data/vehicles/<vehicleId>.json
    backend/data/shells/<cannonId>.json

BR formula: BR = 1.0 + economicRankHistorical / 3.0
  e.g. Tiger IIh economicRankHistorical=17 → BR=6.7 ✓
"""

from __future__ import annotations
import argparse
import csv
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# BLK parser (Gaijin binary/text BLK)
# ---------------------------------------------------------------------------

def parse_blk_text(text: str) -> dict[str, Any]:
    """
    Minimal text-format BLK parser.
    Real BLK files can be binary; use Gaijin's blk2json tool for binary BLK,
    then pass the JSON result to this pipeline.
    """
    result: dict[str, Any] = {}
    stack = [result]
    current = result

    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("//"):
            continue
        if line == "{":
            continue
        if line == "}":
            stack.pop()
            current = stack[-1]
            continue
        # Block open:  name {  (on same line or next)
        block_match = re.match(r'^(\w+)\s*\{?\s*$', line)
        if block_match and not re.search(r'[:=]', line):
            name = block_match.group(1)
            child: dict[str, Any] = {}
            current.setdefault(name, child)
            stack.append(child)
            current = child
            continue
        # Key-value:  name:type = value
        kv_match = re.match(r'^(\w+)\s*:\s*\w+\s*=\s*(.+)$', line)
        if kv_match:
            key, val = kv_match.group(1), kv_match.group(2).strip()
            # Try to coerce types
            try:
                current[key] = int(val)
                continue
            except ValueError:
                pass
            try:
                current[key] = float(val)
                continue
            except ValueError:
                pass
            if val.lower() in ("true", "yes"):
                current[key] = True
            elif val.lower() in ("false", "no"):
                current[key] = False
            else:
                current[key] = val.strip('"')

    return result


def load_blk(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8", errors="replace") as f:
        return parse_blk_text(f.read())


# ---------------------------------------------------------------------------
# BR formula
# ---------------------------------------------------------------------------

def compute_br(economic_rank_historical: int) -> float:
    return round(1.0 + economic_rank_historical / 3.0, 1)


# ---------------------------------------------------------------------------
# Display name from units.csv
# ---------------------------------------------------------------------------

def load_display_name(units_csv: str, vehicle_id: str) -> str:
    """Read units.csv (id,name,...) and find display name. Strip leading ■."""
    try:
        with open(units_csv, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                row_id = (row.get("id") or row.get("ID") or "").strip()
                if row_id == vehicle_id:
                    name = (row.get("name") or row.get("Name") or vehicle_id).strip()
                    return name.lstrip("■").strip()
    except FileNotFoundError:
        pass
    return vehicle_id


# ---------------------------------------------------------------------------
# Damage parts builder from .blk
# ---------------------------------------------------------------------------

def build_damage_parts(blk: dict[str, Any]) -> dict[str, Any]:
    """
    Extract damageParts from a vehicle BLK.
    BLK structure (simplified):
      DamageParts {
        partName {
          armorThickness:r = 60.0
          armorClass:t = "RHA_tank_modern"
          ...
        }
      }
    """
    raw = blk.get("DamageParts", {})
    parts: dict[str, Any] = {}
    for name, data in raw.items():
        if not isinstance(data, dict):
            continue
        entry: dict[str, Any] = {}
        if "armorThickness" in data:
            entry["armorThickness"] = float(data["armorThickness"])
        if "armorClass" in data:
            entry["armorClass"] = data["armorClass"]
        if data.get("variableThickness"):
            entry["variableThickness"] = True
        if "genericArmorQuality" in data:
            entry["genericArmorQuality"] = float(data["genericArmorQuality"])
        if data.get("isModule"):
            entry["_isModule"] = True
        if data.get("isCrew"):
            entry["_isCrew"] = True
        if data.get("hidableInViewer"):
            entry["hidableInViewer"] = True
        if data.get("hidableInXrayViewer"):
            entry["hidableInXrayViewer"] = True
        # Nested children (groups)
        children = {}
        for child_key, child_val in data.items():
            if isinstance(child_val, dict):
                children[child_key] = child_val
        if children:
            entry["_isGroup"] = True
            entry["children"] = children
        parts[name] = entry
    return parts


# ---------------------------------------------------------------------------
# Shell pen curve builder from cannon BLK
# ---------------------------------------------------------------------------

def build_shells_json(cannon_blk: dict[str, Any], cannon_id: str) -> dict[str, Any]:
    """
    Parse cannon BLK → shells JSON with pen curves.
    ArmorPower<N>m entries are [pen_mm, range_m] pairs.
    """
    caliber = float(cannon_blk.get("caliber", 0)) * 1000  # m → mm
    rounds_raw = cannon_blk.get("bullet", {})
    if not isinstance(rounds_raw, list):
        rounds_raw = [rounds_raw] if rounds_raw else []

    rounds = []
    for r in rounds_raw:
        if not isinstance(r, dict):
            continue
        name = r.get("bulletName", "unknown")
        bullet_type = r.get("bulletType", "")
        display = r.get("shortName", name)
        mass = r.get("mass", None)
        explosive = r.get("explosiveMass", None)

        # Build pen curve from ArmorPower<N>m fields
        pen_curve = []
        flat_pen = None
        for key, val in r.items():
            m = re.match(r"ArmorPower(\d+)m", key)
            if m:
                range_m = int(m.group(1))
                pen_mm = float(val)
                pen_curve.append({"range_m": range_m, "pen_mm": pen_mm})
        pen_curve.sort(key=lambda x: x["range_m"])

        if not pen_curve and "cumulativeDamage" in r:
            flat_pen = float(r["cumulativeDamage"].get("armorPower", 0))

        round_entry: dict[str, Any] = {
            "bulletName": name,
            "bulletType": bullet_type,
            "displayName": display,
        }
        if mass is not None:
            round_entry["mass_kg"] = float(mass)
        if explosive is not None:
            round_entry["explosiveMass_kg"] = float(explosive)
        if flat_pen is not None:
            round_entry["penetration_flat_mm"] = flat_pen
            round_entry["penCurve"] = None
        elif pen_curve:
            round_entry["penetration_flat_mm"] = None
            round_entry["penCurve"] = pen_curve
        else:
            round_entry["penetration_flat_mm"] = None
            round_entry["penCurve"] = None

        rounds.append(round_entry)

    return {"cannonId": cannon_id, "caliber_mm": caliber, "rounds": rounds}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Build vehicle JSON from raw WT extracts")
    parser.add_argument("--blk",      required=True, help="Vehicle .blk file")
    parser.add_argument("--wpcost",   required=True, help="wpcost.blk")
    parser.add_argument("--shop",     required=True, help="shop.blk")
    parser.add_argument("--units",    required=True, help="units.csv")
    parser.add_argument("--unittags", required=True, help="unittags.blk")
    parser.add_argument("--cannon",   required=True, help="Cannon .blk file")
    parser.add_argument("--out-vehicles", default="./backend/data/vehicles")
    parser.add_argument("--out-shells",   default="./backend/data/shells")
    args = parser.parse_args()

    vehicle_blk = load_blk(args.blk)
    wpcost = load_blk(args.wpcost)
    shop = load_blk(args.shop)
    unittags = load_blk(args.unittags)
    cannon_blk = load_blk(args.cannon)

    # Derive IDs from filenames
    vehicle_id = Path(args.blk).stem
    cannon_id = Path(args.cannon).stem

    # Economic rank → BR
    econ_rank = int(wpcost.get(vehicle_id, {}).get("economicRankHistorical", 0))
    br = compute_br(econ_rank)

    # Nation, branch, rank from shop
    shop_entry = shop.get(vehicle_id, {})
    nation = shop_entry.get("country", "unknown")
    branch = shop_entry.get("unitType", "army").lower()
    rank = int(shop_entry.get("rank", 1))

    # Shop armor [front, side, rear] from unittags
    tags_entry = unittags.get(vehicle_id, {})
    shop_armor_hull = tags_entry.get("armorHull", [0, 0, 0])
    shop_armor_turret = tags_entry.get("armorTurret", [0, 0, 0])
    operator = tags_entry.get("operatorCountry", None)
    vtype = tags_entry.get("unitType", "tank").lower()

    display_name = load_display_name(args.units, vehicle_id)
    damage_parts = build_damage_parts(vehicle_blk)

    vehicle_json = {
        "vehicleId": vehicle_id,
        "displayName": display_name,
        "nation": nation,
        "operatorCountry": operator,
        "type": vtype,
        "branch": branch,
        "rank": rank,
        "battleRating": {"arcade": br, "realistic": br, "simulator": br},
        "shopArmor": {
            "hull": shop_armor_hull if isinstance(shop_armor_hull, list) else [0, 0, 0],
            "turret": shop_armor_turret if isinstance(shop_armor_turret, list) else [0, 0, 0],
        },
        "modelId": vehicle_id,
        "damageParts": damage_parts,
        "xrayViewerData": vehicle_blk.get("xrayViewerData", {}),
        "shells": [cannon_id],
    }

    shells_json = build_shells_json(cannon_blk, cannon_id)

    os.makedirs(args.out_vehicles, exist_ok=True)
    os.makedirs(args.out_shells, exist_ok=True)

    v_path = os.path.join(args.out_vehicles, f"{vehicle_id}.json")
    s_path = os.path.join(args.out_shells, f"{cannon_id}.json")

    with open(v_path, "w") as f:
        json.dump(vehicle_json, f, indent=2)
    print(f"Written: {v_path}")

    with open(s_path, "w") as f:
        json.dump(shells_json, f, indent=2)
    print(f"Written: {s_path}")


if __name__ == "__main__":
    main()
