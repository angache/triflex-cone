# TriFlex CAD source

Scripts that rebuild a clean TriFlex STL from a physically tested reference STL.

The stable STLs (V29, V30) are mesh exports with visible artifacts: a sawtooth seam along each helix arm and membranes built from about 220 stacked slabs, which slice as a staircase. These scripts keep the tested geometry and replace only the arm and membrane surfaces with smooth lofts.

## Pipeline

1. `extract_profile.py` slices one helix arm and one membrane of the reference STL every 0.05 mm and reduces each section to a few parameters:
   - Arm: centroid radius and angle, centerline direction, and the cross-section perpendicular to the centerline as an order-8 Fourier radial function.
   - Membrane: center radius and angle, long-axis angle, length and width of the section rectangle.

   Every parameter is smoothed along Z (Savitzky–Golay, 1.05 mm arms / 0.75 mm membranes). Output: `profiles/<revision>.json`.
2. `generate_triflex.py` lofts the three arms and three membranes (120° copies) from the profile, keeps the reference base (with cable notch), neck and top disc unchanged, and unions everything into one closed solid.
3. `compare_sections.py` compares the result with the reference at every 0.2 mm print layer: section area, symmetric difference, Hausdorff distance, and the share of sharp edges on the helix surfaces.

## Usage

```sh
python3 -m venv .venv && .venv/bin/pip install -r cad/requirements.txt
.venv/bin/python cad/extract_profile.py models/stable/triflex-v30.stl cad/profiles/v31.json
.venv/bin/python cad/generate_triflex.py cad/profiles/v31.json models/stable/triflex-v30.stl models/experimental/triflex-v31-experimental.stl
.venv/bin/python cad/compare_sections.py models/stable/triflex-v30.stl models/experimental/triflex-v31-experimental.stl
```

With the pinned versions in `requirements.txt` both outputs are byte-for-byte reproducible.

## Rules

- These scripts never modify a stable STL; they only read it.
- Any generated STL is a new experimental revision and must be physically tested before it can be called stable (see `AGENTS.md`).
- Change one mechanical variable per revision. To test a geometry change, edit the profile (for example scale the arm `shape` coefficients) in a new profile file, not the reference STL.
