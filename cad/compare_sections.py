#!/usr/bin/env python3
"""Compare two TriFlex STLs the way a slicer sees them.

Reports the solid volume, the horizontal section difference at every print
layer, and the share of sharp edges on the arm and membrane surfaces (a proxy
for the staircase and seam artifacts visible in the slicer preview).

Usage:
    python cad/compare_sections.py models/stable/triflex-v30.stl \
        models/experimental/triflex-v31-experimental.stl
"""

from __future__ import annotations

import sys

import manifold3d as mf
import numpy as np
import trimesh
from shapely.geometry import Polygon
from shapely.ops import unary_union

LAYER_MM = 0.2
FIRST_LAYER_MM = 0.1
HELIX_Z = (3.0, 29.5)
SHARP_EDGE_DEG = 20.0


def load_solid(path: str):
    mesh = trimesh.load(path, process=True)
    parts = mesh.split(only_watertight=False)
    solid = mf.Manifold.batch_boolean(
        [mf.Manifold(mf.Mesh(vert_properties=p.vertices.astype(np.float32),
                             tri_verts=p.faces.astype(np.uint32))) for p in parts],
        mf.OpType.Add)
    out = solid.to_mesh()
    return trimesh.Trimesh(np.asarray(out.vert_properties)[:, :3], np.asarray(out.tri_verts)), mesh


def section(mesh: trimesh.Trimesh, z: float):
    result = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if result is None:
        return Polygon()
    planar, transform = result.to_2D()

    def world(coords):
        coords = np.array(coords)
        return trimesh.transform_points(np.column_stack([coords, np.zeros(len(coords))]), transform)[:, :2]

    return unary_union([Polygon(world(p.exterior.coords), [world(h.coords) for h in p.interiors])
                        for p in planar.polygons_full])


def sharp_edge_share(mesh: trimesh.Trimesh) -> float:
    centers = mesh.triangles_center[mesh.face_adjacency[:, 0]]
    inside = (centers[:, 2] > HELIX_Z[0]) & (centers[:, 2] < HELIX_Z[1])
    angles = np.degrees(mesh.face_adjacency_angles[inside])
    return float(np.mean(angles > SHARP_EDGE_DEG))


def main(reference_path: str, candidate_path: str):
    reference, reference_raw = load_solid(reference_path)
    candidate, candidate_raw = load_solid(candidate_path)
    print(f"volume mm3: reference {reference.volume:.2f}, candidate {candidate.volume:.2f}")
    print(f"bounds: reference {np.round(reference.bounds, 3).tolist()}, "
          f"candidate {np.round(candidate.bounds, 3).tolist()}")

    rows = []
    for z in np.arange(FIRST_LAYER_MM, reference.bounds[1][2], LAYER_MM):
        a, b = section(reference, z), section(candidate, z)
        xor = a.symmetric_difference(b).area
        hausdorff = a.hausdorff_distance(b) if not (a.is_empty or b.is_empty) else 0.0
        rows.append((z, a.area, b.area, xor, hausdorff))
    rows = np.array(rows)
    helix = rows[(rows[:, 0] > HELIX_Z[0]) & (rows[:, 0] < HELIX_Z[1])]
    print(f"layers compared: {len(rows)} at {LAYER_MM} mm")
    print(f"helix layers: mean area change {100 * np.mean(helix[:, 2] / helix[:, 1] - 1):+.2f}%, "
          f"max {100 * np.max(np.abs(helix[:, 2] / helix[:, 1] - 1)):.2f}%")
    print(f"helix layers: mean xor {helix[:, 3].mean():.3f} mm2, "
          f"mean hausdorff {helix[:, 4].mean():.3f} mm, max {helix[:, 4].max():.3f} mm")
    outside = rows[(rows[:, 0] < HELIX_Z[0] - 0.7) | (rows[:, 0] > 30.4)]
    print(f"base/neck/top layers: max xor {outside[:, 3].max():.4f} mm2")
    for name, mesh in (("reference", reference_raw), ("candidate", candidate_raw)):
        print(f"sharp edges (>{SHARP_EDGE_DEG:.0f} deg) on helix surfaces, {name}: "
              f"{100 * sharp_edge_share(mesh):.1f}%")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
