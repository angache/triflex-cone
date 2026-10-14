#!/usr/bin/env python3
"""Build a TriFlex variant from a parameter file.

Reads cad/variants/<name>.toml, applies its arm and membrane values to the
base profile, generates the STL, checks it and (optionally) compares it with
another revision. Writes cad/profiles/<name>.json and
models/experimental/triflex-<name>-experimental.stl. An existing file with
different content is never replaced without --force, so a printed revision
cannot be overwritten by accident.

Usage:
    python cad/build.py cad/variants/v32.toml [--force]
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import tomllib
from pathlib import Path

import numpy as np

import compare_sections
from generate_triflex import build
from scale_arms import TAPER_MM, arm_diameter, scale_arms

REPO = Path(__file__).resolve().parent.parent
REFERENCE_STL = "models/stable/triflex-v30.stl"
# Stable or printed revisions: never replaced, not even with --force.
PROTECTED = {"v29", "v30", "v31"}
EXPECTED_BOUNDS = np.array([[-19.0, -19.0, 0.0], [19.0, 19.0, 32.0]])

KEYS = {"": {"name", "base", "compare_with", "arm", "membrane"},
        "arm": {"diameter_mm", "taper_mm"},
        "membrane": {"thickness_mm"}}
LIMITS = {"arm.diameter_mm": (2.0, 4.0),
          "arm.taper_mm": (0.5, 6.0),
          "membrane.thickness_mm": (0.8, 2.0)}
# Below these differences a value counts as unchanged (measurement precision).
ARM_TOLERANCE_MM = 0.005
MEMBRANE_TOLERANCE_MM = 0.01


def fail(message: str):
    raise SystemExit(f"error: {message}")


def read_variant(path: str) -> dict:
    with open(path, "rb") as handle:
        variant = tomllib.load(handle)
    for section, allowed in KEYS.items():
        values = variant.get(section, {}) if section else variant
        unknown = set(values) - allowed
        if unknown:
            fail(f"unknown key(s) in [{section or 'top level'}]: {', '.join(sorted(unknown))}")
    for key, (low, high) in LIMITS.items():
        section, name = key.split(".")
        value = variant.get(section, {}).get(name)
        if value is not None and not low <= value <= high:
            fail(f"{key} = {value} is outside {low}–{high}")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", variant.get("name", "")):
        fail("name must be lowercase letters, digits and dashes, for example \"v33\"")
    variant.setdefault("base", "v31")
    if variant["name"] == variant["base"]:
        fail("name must differ from base")
    if variant["name"] in PROTECTED:
        fail(f"{variant['name']} is a stable or printed revision and cannot be rebuilt; use a new name")
    return variant


def revision_stl(name: str) -> str:
    for path in (f"models/experimental/triflex-{name}-experimental.stl",
                 f"models/stable/triflex-{name}.stl"):
        if Path(path).exists():
            return path
    fail(f"no STL found for revision {name}")


def membrane_thickness(profile: dict) -> float:
    return float(np.median(profile["membrane"]["width"]))


def apply(variant: dict, profile: dict) -> list[str]:
    notes = []
    arm = variant.get("arm", {})
    current = arm_diameter(profile)
    target = float(arm.get("diameter_mm", current))
    taper_mm = float(arm.get("taper_mm", TAPER_MM))
    if abs(target - current) > ARM_TOLERANCE_MM:
        scale = scale_arms(profile, target, taper_mm)
        notes.append(f"arm diameter {current:.3f} -> {target:.3f} mm (scale {scale:.4f}, "
                     f"taper {taper_mm} mm)")
    else:
        notes.append(f"arm diameter unchanged ({current:.3f} mm)")
    membrane = profile["membrane"]
    current = membrane_thickness(profile)
    target = float(variant.get("membrane", {}).get("thickness_mm", current))
    if abs(target - current) > MEMBRANE_TOLERANCE_MM:
        scale = target / current
        membrane["width"] = (np.array(membrane["width"]) * scale).tolist()
        profile["membrane_scale"] = {"from_thickness_mm": round(current, 4),
                                     "to_thickness_mm": target, "scale": round(scale, 5)}
        notes.append(f"membrane thickness {current:.3f} -> {target:.3f} mm (scale {scale:.4f})")
    else:
        notes.append(f"membrane thickness unchanged ({current:.3f} mm)")
    return notes


def check_target(path: Path, data: bytes, force: bool) -> str:
    if not path.exists():
        return "new"
    if path.read_bytes() == data:
        return "unchanged"
    if not force:
        fail(f"{path} already exists with different content. Use a new name, "
             f"or --force if this revision has not been printed.")
    return "replaced"


def main(variant_path: str, force: bool = False):
    variant_path = os.path.abspath(variant_path)
    os.chdir(REPO)
    variant = read_variant(variant_path)
    name, base = variant["name"], variant["base"]
    base_path = f"cad/profiles/{base}.json"
    if not Path(base_path).exists():
        fail(f"base profile {base_path} not found")
    with open(base_path) as handle:
        profile = json.load(handle)
    profile["derived_from"] = base_path
    notes = apply(variant, profile)

    print(f"building {name} from {base}:")
    for note in notes:
        print(f"  {note}")
    mesh = build(profile, REFERENCE_STL)
    if not mesh.is_watertight or mesh.body_count != 1:
        fail(f"mesh is not a single closed solid (watertight={mesh.is_watertight}, "
             f"bodies={mesh.body_count})")
    if not np.allclose(mesh.bounds, EXPECTED_BOUNDS, atol=0.01):
        fail(f"unexpected bounds {np.round(mesh.bounds, 3).tolist()}")

    profile_path = Path(f"cad/profiles/{name}.json")
    stl_path = Path(f"models/experimental/triflex-{name}-experimental.stl")
    profile_data = json.dumps(profile).encode()
    stl_data = mesh.export(file_type="stl")
    states = [check_target(profile_path, profile_data, force), check_target(stl_path, stl_data, force)]
    profile_path.write_bytes(profile_data)
    stl_path.write_bytes(stl_data)

    arm = profile["arm"]
    z = np.array(arm["z"])
    diameter = 2 * np.sqrt(np.array(arm["axis_1"]) * np.array(arm["axis_2"]))
    along = ", ".join(f"z {h:.0f}: {np.interp(h, z, diameter):.2f}" for h in (5, 8, 15, 23, 29))
    print(f"profile: {profile_path} ({states[0]})")
    print(f"STL: {stl_path} ({states[1]}), SHA-256 {hashlib.sha256(stl_data).hexdigest()}")
    print(f"  {len(mesh.faces)} faces, single closed solid, volume {mesh.volume:.1f} mm3, "
          f"bounds 38 x 38 x 32 mm")
    print(f"  equivalent arm diameter along height (mm): {along}")

    compare_with = variant.get("compare_with")
    if compare_with:
        reference = revision_stl(compare_with)
        print(f"\ncomparison with {compare_with} ({reference}):")
        compare_sections.main(reference, str(stl_path), str(profile_path))


if __name__ == "__main__":
    arguments = [a for a in sys.argv[1:] if a != "--force"]
    if len(arguments) != 1:
        raise SystemExit(__doc__)
    main(arguments[0], force="--force" in sys.argv[1:])
