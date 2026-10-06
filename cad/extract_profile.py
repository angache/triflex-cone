#!/usr/bin/env python3
"""Extract a smooth parametric profile from a physically tested TriFlex STL.

The profile is defined by the horizontal cross-sections of one helix arm and
one membrane (the other two are 120-degree copies). Each section is reduced
to a few smooth parameters, and every parameter is filtered along Z to remove
mesh artifacts (the arm seam sawtooth and the stacked-slab membrane
staircase) while keeping the tested shape.

Arm sections are described in the plane perpendicular to the arm centerline,
where the profile is a near-ellipse that a low Fourier order captures without
following the seam. A horizontal section is the same profile stretched along
the horizontal direction of the centerline.

Usage:
    python cad/extract_profile.py models/stable/triflex-v30.stl cad/profiles/v31.json
"""

from __future__ import annotations

import json
import sys

import numpy as np
import trimesh
from scipy.signal import savgol_filter
from shapely.geometry import LineString, Point

DZ = 0.05
ARM_Z = (2.40, 30.30)
MEMBRANE_Z = (2.40, 29.85)
FOURIER_ORDER = 8
RAY_COUNT = 360
ARM_WINDOW_MM = 1.05
TANGENT_WINDOW_MM = 2.05
# Below this height the arm blends into the base fillet and its centroid no
# longer follows the helix, so the centerline direction is held constant.
TANGENT_CLAMP_Z = 3.0
MEMBRANE_WINDOW_MM = 0.75


def sections(mesh: trimesh.Trimesh, z: float):
    section = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if section is None:
        return []
    planar, transform = section.to_2D()
    polygons = []
    for polygon in planar.polygons_full:
        coords = np.array(polygon.exterior.coords)
        world = trimesh.transform_points(np.column_stack([coords, np.zeros(len(coords))]), transform)[:, :2]
        polygons.append(world)
    return polygons


def polygon_centroid(points: np.ndarray) -> np.ndarray:
    from shapely.geometry import Polygon

    c = Polygon(points).centroid
    return np.array([c.x, c.y])


def track(mesh, z_values, expected_count):
    """Follow the polygon nearest to the previous one through the Z range."""
    tracked = []
    previous = None
    for z in z_values:
        polygons = sections(mesh, z)
        if len(polygons) != expected_count:
            raise RuntimeError(f"expected {expected_count} polygons at z={z:.2f}, got {len(polygons)}")
        centroids = [polygon_centroid(p) for p in polygons]
        if previous is None:
            index = int(np.argmax([np.arctan2(c[1], c[0]) for c in centroids]))
        else:
            index = int(np.argmin([np.linalg.norm(c - previous) for c in centroids]))
        previous = centroids[index]
        tracked.append((z, polygons[index], centroids[index]))
    return tracked


def perpendicular_frame(radius, theta, d_radius, d_theta):
    """Horizontal unit vector e1 and horizontal vector w of the arm section.

    A point a*e1 + b*w in the horizontal section corresponds to a*e1 + b*e2
    in the plane perpendicular to the centerline tangent t.
    """
    tangent = np.array([
        d_radius * np.cos(theta) - radius * d_theta * np.sin(theta),
        d_radius * np.sin(theta) + radius * d_theta * np.cos(theta),
        1.0,
    ])
    tangent /= np.linalg.norm(tangent)
    e1 = np.cross(tangent, [0.0, 0.0, 1.0])
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(tangent, e1)
    w = e2 - (e2[2] / tangent[2]) * tangent
    return e1[:2], w[:2]


def radial_function(points: np.ndarray):
    from shapely.geometry import Polygon

    boundary = Polygon(points).exterior
    center = np.zeros(2)
    phis = np.linspace(0, 2 * np.pi, RAY_COUNT, endpoint=False)
    radii = []
    for phi in phis:
        direction = np.array([np.cos(phi), np.sin(phi)])
        ray = LineString([center, center + direction * 20])
        hit = ray.intersection(boundary)
        candidates = [hit] if hit.geom_type == "Point" else list(getattr(hit, "geoms", []))
        distances = [Point(center).distance(p) for p in candidates if p.geom_type == "Point"]
        radii.append(min(distances))
    return phis, np.array(radii)


def fourier_fit(phis, radii):
    columns = [np.ones_like(phis)]
    for n in range(1, FOURIER_ORDER + 1):
        columns += [np.cos(n * phis), np.sin(n * phis)]
    coefficients, *_ = np.linalg.lstsq(np.column_stack(columns), radii, rcond=None)
    return coefficients


def smooth(values: np.ndarray, window_mm: float, deriv: int = 0, polyorder: int = 3) -> np.ndarray:
    window = int(round(window_mm / DZ)) | 1
    return savgol_filter(values, window, polyorder, deriv=deriv, delta=DZ, axis=0, mode="interp")


def extract_arm(body):
    z_values = np.round(np.arange(ARM_Z[0], ARM_Z[1] + DZ / 2, DZ), 4)
    rows = track(body, z_values, 3)
    centers = np.array([center for _, _, center in rows])
    radius = np.linalg.norm(centers, axis=1)
    theta = np.unwrap(np.arctan2(centers[:, 1], centers[:, 0]))
    d_radius = smooth(radius, TANGENT_WINDOW_MM, deriv=1, polyorder=2)
    d_theta = smooth(theta, TANGENT_WINDOW_MM, deriv=1, polyorder=2)
    clamp = int(np.searchsorted(z_values, TANGENT_CLAMP_Z))
    d_radius[:clamp] = d_radius[clamp]
    d_theta[:clamp] = d_theta[clamp]

    shapes = []
    for (_, points, center), r, t, dr, dt in zip(rows, radius, theta, d_radius, d_theta):
        e1, w = perpendicular_frame(r, t, dr, dt)
        offset = points - center
        local = np.column_stack([offset @ e1, offset @ w / np.dot(w, w)])
        phis, radii = radial_function(local)
        shapes.append(fourier_fit(phis, radii))
    return {
        "z": z_values.tolist(),
        "radius": smooth(radius, ARM_WINDOW_MM).tolist(),
        "theta": smooth(theta, ARM_WINDOW_MM).tolist(),
        "d_radius": d_radius.tolist(),
        "d_theta": d_theta.tolist(),
        "shape": smooth(np.array(shapes), ARM_WINDOW_MM).tolist(),
    }


def extract_membrane(membrane):
    from shapely.geometry import Polygon

    z_values = np.round(np.arange(MEMBRANE_Z[0], MEMBRANE_Z[1] + DZ / 2, DZ), 4)
    rows = []
    for z in z_values:
        polygons = sections(membrane, z)
        if len(polygons) != 1:
            raise RuntimeError(f"membrane section count {len(polygons)} at z={z:.2f}")
        rectangle = np.array(Polygon(polygons[0]).minimum_rotated_rectangle.exterior.coords)[:4]
        center = rectangle.mean(axis=0)
        edges = [rectangle[(i + 1) % 4] - rectangle[i] for i in range(4)]
        long_edge = max(edges[:2], key=np.linalg.norm)
        short_edge = min(edges[:2], key=np.linalg.norm)
        radial = center / np.linalg.norm(center)
        axis_angle = np.arctan2(long_edge[1], long_edge[0]) - np.arctan2(radial[1], radial[0])
        axis_angle = (axis_angle + np.pi / 2) % np.pi - np.pi / 2
        rows.append((np.linalg.norm(center), np.arctan2(center[1], center[0]), axis_angle,
                     np.linalg.norm(long_edge), np.linalg.norm(short_edge)))
    rows = np.array(rows)
    rows[:, 1] = np.unwrap(rows[:, 1])
    rows[:, 2] = np.unwrap(rows[:, 2] * 2) / 2
    smoothed = smooth(rows, MEMBRANE_WINDOW_MM)
    return {
        "z": z_values.tolist(),
        "radius": smoothed[:, 0].tolist(),
        "theta": smoothed[:, 1].tolist(),
        "axis_angle": smoothed[:, 2].tolist(),
        "length": smoothed[:, 3].tolist(),
        "width": smoothed[:, 4].tolist(),
    }


def main(source: str, target: str):
    mesh = trimesh.load(source, process=True)
    parts = sorted(mesh.split(only_watertight=False), key=lambda p: -len(p.faces))
    body = parts[0]
    membrane = max(parts[1:4], key=lambda p: np.arctan2(*p.vertices.mean(axis=0)[1::-1]))
    profile = {
        "source": source,
        "dz": DZ,
        "fourier_order": FOURIER_ORDER,
        "arm": extract_arm(body),
        "membrane": extract_membrane(membrane),
    }
    with open(target, "w") as handle:
        json.dump(profile, handle)
    print(f"wrote {target}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
