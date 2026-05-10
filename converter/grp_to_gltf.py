#!/usr/bin/env python3
"""
GRP2/DAG → glTF converter for War Thunder xray skeleton meshes.

Usage:
    python grp_to_gltf.py <input.grp> <output_dir>

This script:
1. Parses the GRP2 binary container (magic: 0x47525032 "GRP2")
2. Locates the *_xray_skeleton sub-asset (the low-poly xray viewer mesh)
3. Converts DAG geometry to glTF 2.0 (.glb)
4. Preserves mesh/node names so they match DamageParts zone keys 1:1

NOTE: Full GRP2/DAG format parsing requires the proprietary Gaijin format spec.
This scaffold shows the correct structure — fill in the binary parsing logic
once the format documentation is available.
"""

from __future__ import annotations
import argparse
import json
import os
import struct
import sys
from pathlib import Path
from typing import BinaryIO

GRP2_MAGIC = b"GRP2"
DAG_XRAY_SUFFIX = "_xray_skeleton"


# ---------------------------------------------------------------------------
# GRP2 container parser
# ---------------------------------------------------------------------------

def read_u32(f: BinaryIO) -> int:
    return struct.unpack("<I", f.read(4))[0]


def read_string(f: BinaryIO) -> str:
    length = read_u32(f)
    return f.read(length).decode("utf-8", errors="replace")


def parse_grp2(path: str) -> dict[str, bytes]:
    """
    Parse a GRP2 container and return a dict of {asset_name: raw_bytes}.
    Raises ValueError on bad magic.
    """
    assets: dict[str, bytes] = {}
    with open(path, "rb") as f:
        magic = f.read(4)
        if magic != GRP2_MAGIC:
            raise ValueError(f"Not a GRP2 file (magic={magic!r})")

        _version = read_u32(f)
        num_assets = read_u32(f)

        for _ in range(num_assets):
            name = read_string(f)
            size = read_u32(f)
            data = f.read(size)
            assets[name] = data

    return assets


# ---------------------------------------------------------------------------
# DAG geometry extractor (stub — fill in once DAG spec is confirmed)
# ---------------------------------------------------------------------------

def dag_to_gltf_bytes(dag_bytes: bytes, asset_name: str) -> bytes:
    """
    Convert raw DAG geometry bytes to a glTF 2.0 binary (.glb).

    The DAG format stores:
      - Node hierarchy with named nodes (matching DamageParts keys)
      - Per-node vertex/index buffers
      - Material indices (ignored for xray mesh — we override in the viewer)

    Returns raw .glb bytes.
    """
    raise NotImplementedError(
        "DAG parsing not yet implemented. "
        "Provide the DAG binary spec or use Gaijin's dagor_sdk tools to export glTF directly."
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Convert GRP2/DAG xray skeleton to glTF")
    parser.add_argument("input", help="Path to .grp input file")
    parser.add_argument("output_dir", help="Directory to write .glb output")
    args = parser.parse_args()

    assets = parse_grp2(args.input)
    print(f"Found {len(assets)} assets in {args.input}:")
    for name in sorted(assets):
        print(f"  {name} ({len(assets[name])} bytes)")

    xray_assets = {k: v for k, v in assets.items() if k.endswith(DAG_XRAY_SUFFIX)}
    if not xray_assets:
        print(f"No *{DAG_XRAY_SUFFIX} assets found — nothing to convert.", file=sys.stderr)
        sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)
    for name, data in xray_assets.items():
        vehicle_id = name.replace(DAG_XRAY_SUFFIX, "")
        out_path = os.path.join(args.output_dir, f"{vehicle_id}.glb")
        glb = dag_to_gltf_bytes(data, name)
        with open(out_path, "wb") as f:
            f.write(glb)
        print(f"Written: {out_path}")


if __name__ == "__main__":
    main()
