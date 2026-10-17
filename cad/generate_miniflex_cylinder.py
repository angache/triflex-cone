#!/usr/bin/env python3
"""Generate a cylindrical MiniFlex for rim-mounted short pads (PDX-8 class).

Unlike TriFlex V30 (center-cone taper), this part fills a foam-cylinder envelope:
flat top, flat annular base, three helical arms at roughly constant radius,
and thin stabilizing membranes. Center-open underside preserved.

Usage:
    .venv/bin/python cad/generate_miniflex_cylinder.py \
        models/experimental/triflex-miniflex-pdx8-m02-experimental.stl
"""

from __future__ import annotations

import sys
from pathlib import Path

import manifold3d as mf
import numpy as np
import trimesh


# Envelope (user-locked for M01/M02)
HEIGHT_MM = 16.0
OUTER_DIAMETER_MM = 20.0

# Cylinder layout (M04: thicker continuous base + underside cable groove)
# Envelope stays Ø20 × H16 — thicker base shortens free helix span slightly.
TOP_THICKNESS_MM = 1.4
BASE_THICKNESS_MM = 2.8
INNER_OPEN_DIAMETER_MM = 10.0  # larger center-open for piezo / wires
ARM_DIAMETER_MM = 2.9
ARM_PATH_RADIUS_MM = 8.2  # near outer wall; leaves radial span for membranes
# 0.5 turn: arm and opposite membrane share phase at base and meet again at top.
HELIX_TURNS = 0.50
# Membranes: opposite helix to the arms (TriFlex-like "ters"), not co-wound.
MEMBRANE_THICKNESS_MM = 1.90
MEMBRANE_INNER_RADIUS_MM = 5.15  # just outside the center open
MEMBRANE_ARM_OVERLAP_MM = 0.50  # how far the sheet enters the arm tube at join ends

# Underside cable groove (not a through-cut). Leaving a continuous bridge on
# top of the annulus stops the base from splaying open under load.
# Angle: halfway between arm roots (0°/120°/240°) → 60°.
CABLE_NOTCH_ANGLE_DEG = 60.0
CABLE_NOTCH_WIDTH_MM = 3.4
CABLE_BRIDGE_MM = 1.0  # unbroken material above the groove
CABLE_NOTCH_DEPTH_EXTRA_MM = 0.15  # cut slightly past faces for clean boolean

ARM_RING_POINTS = 48
ARM_Z_STEPS = 64
MEMBRANE_Z_STEPS = 56
MEMBRANE_SECTION_POINTS = 8  # cross-section ring resolution
DISC_SEGMENTS = 96


def manifold_from_trimesh(mesh: trimesh.Trimesh) -> mf.Manifold:
    mesh = mesh.copy()
    mesh.merge_vertices()
    if mesh.volume < 0:
        mesh.invert()
    return mf.Manifold(
        mf.Mesh(
            vert_properties=mesh.vertices.astype(np.float32),
            tri_verts=mesh.faces.astype(np.uint32),
        )
    )


def loft_rings(rings: np.ndarray) -> mf.Manifold:
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
    return mf.Manifold(
        mf.Mesh(vert_properties=vertices.astype(np.float32), tri_verts=faces)
    )


def tube_frame(tangent: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    t = tangent / (np.linalg.norm(tangent) + 1e-12)
    ref = np.array([0.0, 0.0, 1.0]) if abs(t[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    e1 = np.cross(t, ref)
    e1 /= np.linalg.norm(e1) + 1e-12
    e2 = np.cross(t, e1)
    return e1, e2


def annular_disc(z0: float, thickness: float, r_outer: float, r_inner: float) -> mf.Manifold:
    """Flat washer solid between z0 and z0+thickness."""
    mesh = trimesh.creation.annulus(
        r_min=r_inner,
        r_max=r_outer,
        height=thickness,
        sections=DISC_SEGMENTS,
    )
    mesh.apply_translation([0.0, 0.0, z0 + thickness / 2])
    return manifold_from_trimesh(mesh)


def solid_disc(z0: float, thickness: float, radius: float) -> mf.Manifold:
    mesh = trimesh.creation.cylinder(
        radius=radius,
        height=thickness,
        sections=DISC_SEGMENTS,
    )
    mesh.apply_translation([0.0, 0.0, z0 + thickness / 2])
    return manifold_from_trimesh(mesh)


def helix_arm(phase: float) -> mf.Manifold:
    z0 = BASE_THICKNESS_MM * 0.35
    z1 = HEIGHT_MM - TOP_THICKNESS_MM * 0.35
    zs = np.linspace(z0, z1, ARM_Z_STEPS)
    t = (zs - z0) / (z1 - z0)
    theta = phase + 2 * np.pi * HELIX_TURNS * t
    r = ARM_PATH_RADIUS_MM
    centers = np.column_stack([r * np.cos(theta), r * np.sin(theta), zs])
    tangents = np.gradient(centers, zs, axis=0)
    radius = ARM_DIAMETER_MM / 2
    phis = np.linspace(0, 2 * np.pi, ARM_RING_POINTS, endpoint=False)
    rings = []
    for center, tangent in zip(centers, tangents):
        e1, e2 = tube_frame(tangent)
        rings.append(
            center
            + np.outer(radius * np.cos(phis), e1)
            + np.outer(radius * np.sin(phis), e2)
        )
    return loft_rings(np.array(rings))


def membrane(phase: float) -> mf.Manifold:
    """Thin sheet from near the open center out, on the *opposite* helix to the arm.

    Arms advance +HELIX_TURNS; membranes advance -HELIX_TURNS. With 0.5 turn they
    share `phase` at the base and meet again at the top (phase+π), bracing the
    spring the way TriFlex membranes wind against the arms — not parallel to them.
    """
    z0 = BASE_THICKNESS_MM * 0.45
    z1 = HEIGHT_MM - TOP_THICKNESS_MM * 0.45
    zs = np.linspace(z0, z1, MEMBRANE_Z_STEPS)
    t = (zs - z0) / (z1 - z0)
    # Opposite helix ("ters") — minus sign vs helix_arm.
    theta = phase - 2 * np.pi * HELIX_TURNS * t
    r_in = MEMBRANE_INNER_RADIUS_MM
    r_out = ARM_PATH_RADIUS_MM - ARM_DIAMETER_MM / 2 + MEMBRANE_ARM_OVERLAP_MM
    half_t = MEMBRANE_THICKNESS_MM / 2
    corners_uv = np.array([
        [r_in, -half_t],
        [r_out, -half_t],
        [r_out, +half_t],
        [r_in, +half_t],
    ])
    edge_pts = []
    for i in range(4):
        a, b = corners_uv[i], corners_uv[(i + 1) % 4]
        for s in np.linspace(0, 1, max(2, MEMBRANE_SECTION_POINTS // 4), endpoint=False):
            edge_pts.append((1 - s) * a + s * b)
    uv = np.array(edge_pts)

    rings = []
    for z, th in zip(zs, theta):
        ct, st = np.cos(th), np.sin(th)
        radial = np.array([ct, st, 0.0])
        tang = np.array([-st, ct, 0.0])
        ring = np.outer(uv[:, 0], radial) + np.outer(uv[:, 1], tang)
        ring[:, 2] = z
        rings.append(ring)
    return loft_rings(np.array(rings))


def envelope_cylinder() -> mf.Manifold:
    """Exact Ø × H bounding solid used to clip arms that poke past the plates."""
    mesh = trimesh.creation.cylinder(
        radius=OUTER_DIAMETER_MM / 2,
        height=HEIGHT_MM,
        sections=DISC_SEGMENTS,
    )
    mesh.apply_translation([0.0, 0.0, HEIGHT_MM / 2])
    return manifold_from_trimesh(mesh)


def _rotate_z(mesh: trimesh.Trimesh, angle_deg: float) -> trimesh.Trimesh:
    angle = np.radians(angle_deg)
    c, s = np.cos(angle), np.sin(angle)
    mesh.apply_transform(np.array([
        [c, -s, 0.0, 0.0],
        [s, c, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]))
    return mesh


def cable_groove_cutter(r_outer: float, r_inner: float) -> mf.Manifold:
    """Underside radial U-groove for piezo leads — does not sever the annulus.

    Cuts only from z=0 up to (BASE - BRIDGE), so a continuous ring remains on
    top of the base and the plate cannot splay open under compression.
    """
    groove_depth = BASE_THICKNESS_MM - CABLE_BRIDGE_MM
    if groove_depth < 0.6:
        raise ValueError("BASE_THICKNESS_MM too thin for cable bridge")
    length = (r_outer - r_inner) + 1.4
    height = groove_depth + 2 * CABLE_NOTCH_DEPTH_EXTRA_MM
    box = trimesh.creation.box(extents=[length, CABLE_NOTCH_WIDTH_MM, height])
    mid_r = 0.5 * (r_outer + r_inner)
    # Groove sits on the underside: center of cutter near z = groove_depth/2.
    box.apply_translation([mid_r, 0.0, groove_depth / 2 - CABLE_NOTCH_DEPTH_EXTRA_MM])
    _rotate_z(box, CABLE_NOTCH_ANGLE_DEG)
    return manifold_from_trimesh(box)


def build() -> trimesh.Trimesh:
    r_outer = OUTER_DIAMETER_MM / 2
    r_inner = INNER_OPEN_DIAMETER_MM / 2

    base = annular_disc(0.0, BASE_THICKNESS_MM, r_outer, r_inner)
    base = base - cable_groove_cutter(r_outer, r_inner)

    parts = [
        base,
        solid_disc(HEIGHT_MM - TOP_THICKNESS_MM, TOP_THICKNESS_MM, r_outer - 0.15),
    ]
    for k in range(3):
        phase = 2 * np.pi * k / 3
        parts.append(helix_arm(phase))
        parts.append(membrane(phase))

    solid = parts[0]
    for p in parts[1:]:
        solid = solid + p
    solid = solid ^ envelope_cylinder()  # intersect — keep cylinder envelope

    raw = solid.to_mesh()
    mesh = trimesh.Trimesh(
        vertices=np.asarray(raw.vert_properties)[:, :3],
        faces=np.asarray(raw.tri_verts),
        process=True,
    )
    return mesh


def main(argv: list[str]) -> int:
    out = Path(argv[1] if len(argv) > 1 else "models/experimental/triflex-miniflex-pdx8-m04-experimental.stl")
    mesh = build()
    bounds = mesh.bounds
    size = bounds[1] - bounds[0]
    print("bbox size:", size)
    print("watertight:", mesh.is_watertight)
    print("volume:", float(mesh.volume) if mesh.is_watertight else "n/a")
    print("faces:", len(mesh.faces))
    # Soft check against envelope
    if abs(size[0] - OUTER_DIAMETER_MM) > 0.4 or abs(size[1] - OUTER_DIAMETER_MM) > 0.4:
        print("WARNING: XY size off target", OUTER_DIAMETER_MM)
    if abs(size[2] - HEIGHT_MM) > 0.3:
        print("WARNING: height off target", HEIGHT_MM)
    out.parent.mkdir(parents=True, exist_ok=True)
    mesh.export(out)
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
