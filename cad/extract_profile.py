#!/usr/bin/env python3
"""Extract a smooth parametric profile from a physically tested TriFlex STL.

The profile describes one helix arm and one membrane (the other two are
120-degree copies), reduced to a few smooth parameters filtered along Z to
remove mesh artifacts (the arm seam sawtooth and the stacked-slab membrane
staircase) while keeping the tested shape.

The arm is an elliptic tube: in the plane perpendicular to its centerline the
reference section is a circle (an ellipse flattened along e2 near the top) plus
a shallow seam groove. Each perpendicular section is fitted with an ellipse
that rejects the seam as outliers, and the centerline is refined from the
fitted centers. Only the height range where the section is a clean tube is
kept; the base root fillet and the neck stay reference geometry.

Usage:
    python cad/extract_profile.py models/stable/triflex-v30.stl cad/profiles/v31.json
"""

from __future__ import annotations

import json
import sys

import numpy as np
import trimesh
from scipy.signal import savgol_filter

DZ = 0.05
ARM_Z = (2.40, 30.30)
MEMBRANE_Z = (2.40, 29.85)
ARM_FIT_DZ = 0.10
ARM_FIT_ITERATIONS = 3
ARM_SECTION_SAMPLES = 600
# Points of a perpendicular section closer than this to the plate top belong
# to the base, not to the arm.
PLATE_TOP_Z = 2.37
ARM_SEARCH_MM = 2.6
SEAM_TOLERANCE_MM = 0.02
MIN_INLIERS = 0.7
MAX_FIT_GAP = 5
CENTERLINE_WINDOW_MM = 2.05
ELLIPSE_WINDOW_MM = 1.05
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


def tube_frame(tangent: np.ndarray):
    """Unit vectors (e1 horizontal, e2) spanning the plane perpendicular to tangent."""
    tangent = tangent / np.linalg.norm(tangent)
    e1 = np.cross(tangent, [0.0, 0.0, 1.0])
    e1 /= np.linalg.norm(e1)
    return e1, np.cross(tangent, e1)


def fit_ellipse(u: np.ndarray, v: np.ndarray):
    """Least-squares ellipse (center, axis along e1, axis along e2, angle)."""
    design = np.column_stack([u * u, u * v, v * v, u, v])
    (a, b, c, d, e), *_ = np.linalg.lstsq(design, np.ones_like(u), rcond=None)
    den = b * b - 4 * a * c
    u0 = (2 * c * d - b * e) / den
    v0 = (2 * a * e - b * d) / den
    num = 2 * (a * e * e + c * d * d - b * d * e - den)
    spread = np.hypot(a - c, b)
    major = -np.sqrt(num * (a + c + spread)) / den
    minor = -np.sqrt(num * (a + c - spread)) / den
    angle = 0.5 * np.arctan2(-b, c - a)
    # Report the semi-axes along e1 and e2 (the arm ellipse is aligned with them).
    if abs(np.cos(angle)) < abs(np.sin(angle)):
        major, minor = minor, major
        angle -= np.copysign(np.pi / 2, angle)
    return u0, v0, major, minor, angle


def ellipse_residual(u, v, ellipse):
    u0, v0, axis_1, axis_2, angle = ellipse
    x = (u - u0) * np.cos(angle) + (v - v0) * np.sin(angle)
    y = -(u - u0) * np.sin(angle) + (v - v0) * np.cos(angle)
    t = np.arctan2(y / axis_2, x / axis_1)
    return np.hypot(x, y) - np.hypot(axis_1 * np.cos(t), axis_2 * np.sin(t))


def perpendicular_ellipse(body, center: np.ndarray, tangent: np.ndarray):
    """Fit the arm section in the plane through center perpendicular to tangent.

    Returns (u0, v0, axis_1, axis_2, angle, inlier_share, area) or None when
    the section touches the base plate or is not an ellipse. area is the
    reference section area including the seam groove.
    """
    e1, e2 = tube_frame(tangent)
    section = body.section(plane_origin=center, plane_normal=tangent)
    if section is None:
        return None
    loop = min(section.discrete, key=lambda p: np.min(np.linalg.norm(p - center, axis=1)))
    lengths = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(loop, axis=0), axis=1))]
    s = np.linspace(0.0, lengths[-1], ARM_SECTION_SAMPLES)
    points = np.column_stack([np.interp(s, lengths, loop[:, k]) for k in range(3)])
    u, v = (points - center) @ e1, (points - center) @ e2
    if np.any(points[:, 2] < PLATE_TOP_Z) or np.any(np.hypot(u, v) > ARM_SEARCH_MM):
        return None
    keep = np.ones(len(u), dtype=bool)
    try:
        with np.errstate(all="raise"):
            for _ in range(6):
                ellipse = fit_ellipse(u[keep], v[keep])
                residual = np.abs(ellipse_residual(u, v, ellipse))
                keep = residual < max(SEAM_TOLERANCE_MM, 3 * np.median(residual[keep]))
    except (FloatingPointError, ValueError, np.linalg.LinAlgError):
        return None
    area = 0.5 * abs(np.dot(u, np.roll(v, -1)) - np.dot(v, np.roll(u, -1)))
    return (*ellipse, keep.mean(), area)


def smooth(values: np.ndarray, window_mm: float, deriv: int = 0, polyorder: int = 3,
           dz: float = DZ) -> np.ndarray:
    window = int(round(window_mm / dz)) | 1
    return savgol_filter(values, window, polyorder, deriv=deriv, delta=dz, axis=0, mode="interp")


def longest_run(mask: np.ndarray, max_gap: int) -> slice:
    """Longest stretch of True values, bridging gaps of up to max_gap samples."""
    good = np.flatnonzero(mask)
    breaks = np.flatnonzero(np.diff(good) > max_gap + 1)
    starts = np.r_[good[0], good[breaks + 1]]
    ends = np.r_[good[breaks], good[-1]]
    longest = int(np.argmax(ends - starts))
    return slice(starts[longest], ends[longest] + 1)


def extract_arm(body):
    z_values = np.round(np.arange(ARM_Z[0], ARM_Z[1] + ARM_FIT_DZ / 2, ARM_FIT_DZ), 4)
    rows = track(body, z_values, 3)
    centers = np.array([[*center, z] for z, _, center in rows])

    for _ in range(ARM_FIT_ITERATIONS):
        centers = smooth(centers, CENTERLINE_WINDOW_MM, dz=ARM_FIT_DZ)
        tangents = smooth(centers, CENTERLINE_WINDOW_MM, deriv=1, dz=ARM_FIT_DZ)
        fits, refined = [], []
        for center, tangent in zip(centers, tangents):
            fit = perpendicular_ellipse(body, center, tangent)
            ok = (fit is not None and fit[5] > MIN_INLIERS and np.hypot(fit[0], fit[1]) < 0.5
                  and 1.0 < min(fit[2:4]) and max(fit[2:4]) < 2.0)
            e1, e2 = tube_frame(tangent)
            refined.append(center + fit[0] * e1 + fit[1] * e2 if ok else center)
            # Scale the fitted ellipse to the reference section area so the
            # tube keeps the tested amount of material where the seam groove was.
            scale = np.sqrt(fit[6] / (np.pi * fit[2] * fit[3])) if ok else np.nan
            fits.append((fit[2] * scale, fit[3] * scale) if ok else (np.nan, np.nan))
        centers = np.array(refined)
        fits = np.array(fits)

    valid = ~np.isnan(fits[:, 0])
    tube = longest_run(valid, MAX_FIT_GAP)
    centers, fits, valid = centers[tube], fits[tube], valid[tube]
    centers, fits = centers[valid], fits[valid]
    z = np.round(np.arange(np.ceil(centers[0, 2] / DZ) * DZ, centers[-1, 2], DZ), 4)
    radius = np.interp(z, centers[:, 2], np.linalg.norm(centers[:, :2], axis=1))
    theta = np.interp(z, centers[:, 2], np.unwrap(np.arctan2(centers[:, 1], centers[:, 0])))
    axis_1 = np.interp(z, centers[:, 2], fits[:, 0])
    axis_2 = np.interp(z, centers[:, 2], fits[:, 1])
    return {
        "z": z.tolist(),
        "radius": smooth(radius, CENTERLINE_WINDOW_MM).tolist(),
        "theta": smooth(theta, CENTERLINE_WINDOW_MM).tolist(),
        "axis_1": smooth(axis_1, ELLIPSE_WINDOW_MM).tolist(),
        "axis_2": smooth(axis_2, ELLIPSE_WINDOW_MM).tolist(),
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
        "arm": extract_arm(body),
        "membrane": extract_membrane(membrane),
    }
    with open(target, "w") as handle:
        json.dump(profile, handle)
    print(f"wrote {target}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
