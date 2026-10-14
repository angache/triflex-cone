#!/usr/bin/env python3
"""Build a TriFlex STL from a smooth profile and a tested reference STL.

The three helix arms are swept as elliptic tubes along the smooth centerline
in the profile JSON, and the three membranes are lofted from its smooth
horizontal sections (see extract_profile.py). The base (with cable notch and
arm root fillets), the neck and the top disc are taken unchanged from the
reference STL; each arm tube runs on into them so the reference seam is
covered, so only the arm and membrane surfaces differ from the tested part.

Usage:
    python cad/generate_triflex.py cad/profiles/v31.json \
        models/stable/triflex-v30.stl models/experimental/triflex-v31-experimental.stl
"""

from __future__ import annotations

import json
import sys

import manifold3d as mf
import numpy as np
import trimesh

from extract_profile import tube_frame

ARM_POINTS = 144
ARM_RING_DZ = 0.10
ARM_FIT_MM = 1.0
# Centerline heights where the tube ends. Its end caps must lie inside the
# reference base and neck: the reference arm ends in the base near z = 1.6
# and the tube protrudes from the neck above z = 31.1.
ARM_START_Z = 1.80
ARM_END_Z = 30.90
MEMBRANE_BOTTOM_Z = 2.25
MEMBRANE_TOP_Z = 29.90
EXTRAPOLATION_FIT_MM = 0.30


def extend(z: np.ndarray, values: np.ndarray, z_low: float, z_high: float, dz: float,
           fit_mm: float = EXTRAPOLATION_FIT_MM):
    """Linearly continue every column of values beyond both ends of z."""
    values = values.reshape(len(z), -1)
    fit = max(2, int(round(fit_mm / dz)))
    low_z = np.arange(z[0] - dz, z_low - dz / 2, -dz)[::-1]
    high_z = np.arange(z[-1] + dz, z_high + dz / 2, dz)
    low_slope = (values[fit] - values[0]) / (z[fit] - z[0])
    high_slope = (values[-1] - values[-1 - fit]) / (z[-1] - z[-1 - fit])
    low = values[0] + np.outer(low_z - z[0], low_slope)
    high = values[-1] + np.outer(high_z - z[-1], high_slope)
    return np.concatenate([low_z, z, high_z]), np.vstack([low, values, high])


def loft(rings: np.ndarray) -> mf.Manifold:
    """Close a stack of rings (K x N x 3) into a solid."""
    count, points, _ = rings.shape
    vertices = rings.reshape(-1, 3)
    bottom = len(vertices)
    top = bottom + 1
    vertices = np.vstack([vertices, rings[0].mean(axis=0), rings[-1].mean(axis=0)])
    faces = []
    for k in range(count - 1):
        a = k * points
        b = (k + 1) * points
        for i in range(points):
            j = (i + 1) % points
            faces += [[a + i, a + j, b + j], [a + i, b + j, b + i]]
    last = (count - 1) * points
    for i in range(points):
        j = (i + 1) % points
        faces += [[bottom, j, i], [top, last + i, last + j]]
    faces = np.array(faces, dtype=np.uint32)
    if trimesh.Trimesh(vertices, faces, process=False).volume < 0:
        faces = faces[:, ::-1]
    return mf.Manifold(mf.Mesh(vert_properties=vertices.astype(np.float32), tri_verts=faces))


def arm_rings(profile: dict):
    """Rings of the elliptic arm tube, perpendicular to its centerline."""
    arm = profile["arm"]
    dz = profile["dz"]
    z = np.array(arm["z"])
    centerline = np.column_stack([arm["radius"], arm["theta"]])
    z, centerline = extend(z, centerline, ARM_START_Z, ARM_END_Z, dz, ARM_FIT_MM)
    # Hold the section shape at its last fitted value beyond the fitted range.
    axis_1 = np.interp(z, arm["z"], arm["axis_1"])
    axis_2 = np.interp(z, arm["z"], arm["axis_2"])
    keep = np.unique(np.r_[np.arange(0, len(z), int(round(ARM_RING_DZ / dz))), len(z) - 1])
    z, centerline, axis_1, axis_2 = z[keep], centerline[keep], axis_1[keep], axis_2[keep]
    radius, theta = centerline.T
    centers = np.column_stack([radius * np.cos(theta), radius * np.sin(theta), z])
    tangents = np.gradient(centers, z, axis=0)
    phis = np.linspace(0, 2 * np.pi, ARM_POINTS, endpoint=False)
    rings = []
    for center, tangent, a1, a2 in zip(centers, tangents, axis_1, axis_2):
        e1, e2 = tube_frame(tangent)
        rings.append(center + np.outer(a1 * np.cos(phis), e1) + np.outer(a2 * np.sin(phis), e2))
    return np.array(rings)


def membrane_rings(profile: dict, sparse_root: bool = False):
    membrane = profile["membrane"]
    dz = profile["dz"]
    z = np.array(membrane["z"])
    columns = np.column_stack([membrane[key] for key in
                               ("radius", "theta", "axis_angle", "length", "width")])
    first = z[0]
    z, columns = extend(z, columns, MEMBRANE_BOTTOM_Z, MEMBRANE_TOP_Z, dz)
    if sparse_root:
        # The extension is linear, so dropping its inner rings keeps the shape.
        keep = (z >= first - dz / 2) | (np.arange(len(z)) == 0)
        z, columns = z[keep], columns[keep]
    radius, theta, axis_angle, length, width = columns.T
    center = radius[:, None] * np.stack([np.cos(theta), np.sin(theta)], axis=1)
    a = np.stack([np.cos(theta + axis_angle), np.sin(theta + axis_angle)], axis=1)
    b = np.stack([-a[:, 1], a[:, 0]], axis=1)
    half_a = (length / 2)[:, None] * a
    half_b = (width / 2)[:, None] * b
    corners = [center - half_a - half_b, center + half_a - half_b,
               center + half_a + half_b, center - half_a + half_b]
    rings = np.stack(corners, axis=1)
    return np.concatenate([rings, np.broadcast_to(z[:, None, None], (*rings.shape[:2], 1))], axis=2)


def rotated(solid: mf.Manifold, index: int) -> mf.Manifold:
    return solid.rotate([0.0, 0.0, 120.0 * index])


def reference_parts(path: str):
    mesh = trimesh.load(path, process=True)
    parts = sorted(mesh.split(only_watertight=False), key=lambda p: -len(p.faces))
    body = parts[0]
    others = [p for p in parts[1:] if p.bounds[0][2] > 30.0]
    as_manifold = lambda p: mf.Manifold(mf.Mesh(vert_properties=p.vertices.astype(np.float32),
                                                tri_verts=p.faces.astype(np.uint32)))
    return as_manifold(body), [as_manifold(p) for p in others]


def build(profile: dict, reference_path: str) -> trimesh.Trimesh:
    mesh = build_once(profile, reference_path, sparse_root=False)
    if mesh.is_watertight:
        return mesh
    # V30's base surface has vertices near z = 2.35; for some membrane widths a
    # membrane root ring touches them and the union pinches there.
    return build_once(profile, reference_path, sparse_root=True)


def build_once(profile: dict, reference_path: str, sparse_root: bool) -> trimesh.Trimesh:
    arm_z = profile["arm"]["z"]
    arm_bottom, arm_top = arm_z[0], arm_z[-1]

    body, caps = reference_parts(reference_path)
    # Cut between profile layers so no cut edge falls exactly on the tube surface.
    half_step = profile["dz"] / 2
    base = body.trim_by_plane([0.0, 0.0, -1.0], -(arm_bottom - half_step))
    neck = body.trim_by_plane([0.0, 0.0, 1.0], arm_top + half_step)

    arm = loft(arm_rings(profile))
    membrane = loft(membrane_rings(profile, sparse_root))

    solids = [base, neck, *caps]
    solids += [rotated(arm, i) for i in range(3)]
    solids += [rotated(membrane, i) for i in range(3)]
    result = mf.Manifold.batch_boolean(solids, mf.OpType.Add)

    out = result.to_mesh()
    return trimesh.Trimesh(np.asarray(out.vert_properties)[:, :3], np.asarray(out.tri_verts))


def main(profile_path: str, reference_path: str, target: str):
    with open(profile_path) as handle:
        profile = json.load(handle)
    mesh = build(profile, reference_path)
    mesh.export(target)
    print(f"wrote {target}: {len(mesh.faces)} faces, watertight={mesh.is_watertight}, "
          f"bounds={np.round(mesh.bounds, 3).tolist()}")


if __name__ == "__main__":
    main(*sys.argv[1:4])
