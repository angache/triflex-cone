#!/usr/bin/env python3
"""Derive a profile with thinner (or thicker) helix arms from an existing one.

The arm section is scaled uniformly so that its equivalent diameter in the
free span equals the target. At both ends of the fitted arm range (where the
tube meets the reference root fillet and the neck) the scale returns to 1
over taper_mm with a cosine blend, so the root and neck keep the reference
thickness and no step forms at the junction. Membranes are left unchanged.

Usage:
    python cad/scale_arms.py cad/profiles/v31.json 3.0 cad/profiles/v32.json
"""

from __future__ import annotations

import json
import sys

import numpy as np

TAPER_MM = 2.5
# Height range where the V30 arm section is a circle; its equivalent diameter
# defines the current arm diameter.
CIRCULAR_Z = (6.0, 23.0)


def taper(z: np.ndarray, scale: float, taper_mm: float = TAPER_MM) -> np.ndarray:
    distance = np.minimum(z - z[0], z[-1] - z)
    blend = 0.5 - 0.5 * np.cos(np.pi * np.clip(distance / taper_mm, 0.0, 1.0))
    return 1.0 + (scale - 1.0) * blend


def arm_diameter(profile: dict) -> float:
    arm = profile["arm"]
    z = np.array(arm["z"])
    circular = (z >= CIRCULAR_Z[0]) & (z <= CIRCULAR_Z[1])
    return float(np.median(2 * np.sqrt(np.array(arm["axis_1"])[circular] *
                                       np.array(arm["axis_2"])[circular])))


def scale_arms(profile: dict, diameter_mm: float, taper_mm: float = TAPER_MM) -> float:
    """Scale the arm section in place; returns the scale factor."""
    arm = profile["arm"]
    z = np.array(arm["z"])
    current = arm_diameter(profile)
    scale = diameter_mm / current
    factor = taper(z, scale, taper_mm)
    arm["axis_1"] = (np.array(arm["axis_1"]) * factor).tolist()
    arm["axis_2"] = (np.array(arm["axis_2"]) * factor).tolist()
    profile["arm_scale"] = {"from_diameter_mm": round(current, 4), "to_diameter_mm": diameter_mm,
                            "scale": round(scale, 5), "taper_mm": taper_mm}
    return scale


def main(source: str, diameter_mm: float, target: str):
    with open(source) as handle:
        profile = json.load(handle)
    current = arm_diameter(profile)
    profile["derived_from"] = source
    scale = scale_arms(profile, diameter_mm)
    with open(target, "w") as handle:
        json.dump(profile, handle)
    z = profile["arm"]["z"]
    print(f"wrote {target}: arm diameter {current:.3f} -> {diameter_mm:.3f} mm (scale {scale:.4f}), "
          f"taper {TAPER_MM} mm at z {z[0]:.2f} and {z[-1]:.2f}")


if __name__ == "__main__":
    main(sys.argv[1], float(sys.argv[2]), sys.argv[3])
