#!/usr/bin/env python3
"""Build a TriFlex STL from a smooth profile and a tested reference STL.

The three helix arms and three membranes are lofted from the smooth
horizontal sections in the profile JSON (see extract_profile.py). The base
(with cable notch), the neck and the top disc are taken unchanged from the
reference STL, trimmed at the profile Z limits, so only the arm and membrane
surfaces differ from the tested part.

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

from extract_profile import perpendicular_frame

ARM_POINTS = 240
ARM_RING_STEP = 2
ARM_OVERLAP_MM = 0.15
MEMBRANE_BOTTOM_Z = 2.25
MEMBRANE_TOP_Z = 29.90
EXTRAPOLATION_FIT_MM = 0.30


def extend(z: np.ndarray, values: np.ndarray, z_low: float, z_high: float, dz: float):
    """Linearly continue every column of values beyond both ends of z."""
    values = values.reshape(len(z), -1)
    fit = max(2, int(round(EXTRAPOLATION_FIT_MM / dz)))
    low_z = np.arange(z[0] - dz, z_low - dz / 2, -dz)[::-1]
    high_z = np.arange(z[-1] + dz, z_high + dz / 2, dz)
    low_slope = (values[fit] - values[0]) / (z[fit] - z[0])
    high_slope = (values[-1] - values[-1 - fit]) / (z[-1] - z[-1 - fit])
    low = values[0] + np.outer(low_z - z[0], low_slope)
    high = values[-1] + np.outer(high_z - z[-1], high_slope)
    return np.concatenate([low_z, z, high_z]), np.vstack([low, values, high])


def loft(rings: np.ndarray, z: np.ndarray) -> mf.Manifold:
    """Close a stack of horizontal rings (K x N x 2) into a solid."""
    count, points, _ = rings.shape
    vertices = np.column_stack([rings.reshape(-1, 2), np.repeat(z, points)])
    bottom = len(vertices)
    top = bottom + 1
    vertices = np.vstack([vertices,
                          [*rings[0].mean(axis=0), z[0]],
                          [*rings[-1].mean(axis=0), z[-1]]])
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


def arm_rings(profile: dict, z_low: float, z_high: float):
    arm = profile["arm"]
    dz = profile["dz"]
    z = np.array(arm["z"])
    columns = np.column_stack([arm["radius"], arm["theta"], arm["d_radius"], arm["d_theta"],
                               np.array(arm["shape"])])
    z, columns = extend(z, columns, z_low, z_high, dz)
    radius, theta, d_radius, d_theta = columns[:, :4].T
    shape = columns[:, 4:]
    phis = np.linspace(0, 2 * np.pi, ARM_POINTS, endpoint=False)
    basis = [np.ones_like(phis)]
    for n in range(1, profile["fourier_order"] + 1):
        basis += [np.cos(n * phis), np.sin(n * phis)]
    rho = shape @ np.vstack(basis)
    rings = []
    for r, t, dr, dt, ring_rho in zip(radius, theta, d_radius, d_theta, rho):
        e1, w = perpendicular_frame(r, t, dr, dt)
        center = r * np.array([np.cos(t), np.sin(t)])
        rings.append(center + ring_rho[:, None] * (np.outer(np.cos(phis), e1) + np.outer(np.sin(phis), w)))
    return np.array(rings), z


def membrane_rings(profile: dict):
    membrane = profile["membrane"]
    dz = profile["dz"]
    z = np.array(membrane["z"])
    columns = np.column_stack([membrane[key] for key in
                               ("radius", "theta", "axis_angle", "length", "width")])
    z, columns = extend(z, columns, MEMBRANE_BOTTOM_Z, MEMBRANE_TOP_Z, dz)
    radius, theta, axis_angle, length, width = columns.T
    center = radius[:, None] * np.stack([np.cos(theta), np.sin(theta)], axis=1)
    a = np.stack([np.cos(theta + axis_angle), np.sin(theta + axis_angle)], axis=1)
    b = np.stack([-a[:, 1], a[:, 0]], axis=1)
    half_a = (length / 2)[:, None] * a
    half_b = (width / 2)[:, None] * b
    corners = [center - half_a - half_b, center + half_a - half_b,
               center + half_a + half_b, center - half_a + half_b]
    return np.stack(corners, axis=1), z


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


def main(profile_path: str, reference_path: str, target: str):
    with open(profile_path) as handle:
        profile = json.load(handle)
    arm_z = profile["arm"]["z"]
    arm_bottom, arm_top = arm_z[0], arm_z[-1]

    body, caps = reference_parts(reference_path)
    # Cut between profile layers so no arm ring is coplanar with a cut face.
    half_step = profile["dz"] / 2
    base = body.trim_by_plane([0.0, 0.0, -1.0], -(arm_bottom + half_step))
    neck = body.trim_by_plane([0.0, 0.0, 1.0], arm_top - half_step)

    rings, z = arm_rings(profile, arm_bottom - ARM_OVERLAP_MM, arm_top + ARM_OVERLAP_MM)
    keep = np.unique(np.r_[np.arange(0, len(z), ARM_RING_STEP), len(z) - 1])
    arm = loft(rings[keep], z[keep])
    rings, z = membrane_rings(profile)
    membrane = loft(rings, z)

    solids = [base, neck, *caps]
    solids += [rotated(arm, i) for i in range(3)]
    solids += [rotated(membrane, i) for i in range(3)]
    result = mf.Manifold.batch_boolean(solids, mf.OpType.Add)

    out = result.to_mesh()
    mesh = trimesh.Trimesh(np.asarray(out.vert_properties)[:, :3], np.asarray(out.tri_verts))
    mesh.export(target)
    print(f"wrote {target}: {len(mesh.faces)} faces, watertight={mesh.is_watertight}, "
          f"bounds={np.round(mesh.bounds, 3).tolist()}")


if __name__ == "__main__":
    main(*sys.argv[1:4])
