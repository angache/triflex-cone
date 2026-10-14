# TriFlex CAD source

Scripts that rebuild a clean TriFlex STL from a physically tested reference STL.

The stable STLs (V29, V30) are mesh exports with visible artifacts: a sawtooth seam along each helix arm and membranes built from about 220 stacked slabs, which slice as a staircase. These scripts keep the tested geometry and replace only the arm and membrane surfaces with smooth ones.

## Pipeline

1. `extract_profile.py` reduces one helix arm and one membrane of the reference STL to a few parameters:
   - Arm: an elliptic tube. The arm is cut perpendicular to its centerline every 0.1 mm of height; each section is fitted with an ellipse that rejects the seam as outliers, scaled to the reference section area, and the centerline is refined from the fitted centers (3 passes). Only the height range where the section is a clean tube is kept (z ≈ 4.8–29.25 for V30); the root fillets and the neck stay reference geometry. Stored per 0.05 mm: centerline radius and angle, semi-axes along e1 (horizontal) and e2.
   - Membrane: horizontal sections every 0.05 mm, as center radius and angle, long-axis angle, length and width of the section rectangle.

   Every parameter is smoothed along Z (Savitzky–Golay: 2.05 mm arm centerline, 1.05 mm arm section, 0.75 mm membranes). Output: `profiles/<revision>.json`.
2. `generate_triflex.py` sweeps the three arms (rings perpendicular to the centerline, continued into the reference base root and neck so the tube ends inside them) and lofts the three membranes (120° copies), keeps the reference base (with cable notch and root fillets), neck and top disc unchanged, and unions everything into one closed solid.
3. `compare_sections.py` compares the result with the reference at every 0.2 mm print layer: section area, symmetric difference, Hausdorff distance, and the share of sharp edges on the helix surfaces. Given the profile as a third argument it also measures the arm seam/groove depth directly (peak-to-peak deviation from a smooth tube section).

## Variants (parameter files)

The easiest way is the window: double-click `TriFlex Builder.command` in the repository root (or run `.venv/bin/python cad/gui.py`). Enter the values, press **Oluştur**, then **Cura'da aç**. It suggests the next free name, starts from the newest variant's values, and saves the parameter file to `variants/<name>.toml` when the build succeeds.

From the command line, new variants are built from a parameter file in `variants/`, without touching the scripts:

```sh
python3 -m venv .venv && .venv/bin/pip install -r cad/requirements.txt   # once
cp cad/variants/v32.toml cad/variants/v33.toml                           # set name and values
.venv/bin/python cad/build.py cad/variants/v33.toml
```

Parameters (anything left out keeps the base value):

| Key | Meaning | V30/V31 | Allowed |
|---|---|---|---|
| `name` | revision name; output `profiles/<name>.json` and `models/experimental/triflex-<name>-experimental.stl` | | lowercase, digits, dashes |
| `base` | starting profile in `profiles/` | `v31` | |
| `compare_with` | revision to compare against (optional, ~40 s) | | |
| `arm.diameter_mm` | helix arm diameter in the free span | 3.29 | 2.0–4.0 |
| `arm.taper_mm` | length over which the arm returns to V30 thickness at the root and the neck | 2.5 | 0.5–6.0 |
| `membrane.thickness_mm` | membrane thickness | 1.30 | 0.8–2.0 |

The base plate, root fillets, cable notch, neck and top disc always come from the V30 STL, so height, base diameter and top diameter are not parameters. `build.py` rejects unknown keys and out-of-range values, checks that the result is a single closed 38 × 38 × 32 mm solid, and refuses to replace an existing profile or STL with different content unless given `--force`. Stable and printed revisions (`PROTECTED` in `build.py`: v29, v30, v31) cannot be rebuilt at all; add each revision there once it is printed. Rebuilding an unchanged parameter file reproduces the files byte for byte.

## Low-level scripts

```sh
python3 -m venv .venv && .venv/bin/pip install -r cad/requirements.txt
.venv/bin/python cad/extract_profile.py models/stable/triflex-v30.stl cad/profiles/v31.json
.venv/bin/python cad/generate_triflex.py cad/profiles/v31.json models/stable/triflex-v30.stl models/experimental/triflex-v31-experimental.stl
.venv/bin/python cad/compare_sections.py models/stable/triflex-v30.stl models/experimental/triflex-v31-experimental.stl cad/profiles/v31.json
```

With the pinned versions in `requirements.txt` both outputs are byte-for-byte reproducible.

Arm diameter variants are derived from an existing profile with `scale_arms.py`, which scales both section axes to a target diameter (measured as the median over z 6–23) and blends back to the original thickness over 2.5 mm at each tube end, so the root fillets and the neck keep their tested size. V32:

```sh
.venv/bin/python cad/scale_arms.py cad/profiles/v31.json 3.0 cad/profiles/v32.json
.venv/bin/python cad/generate_triflex.py cad/profiles/v32.json models/stable/triflex-v30.stl models/experimental/triflex-v32-experimental.stl
.venv/bin/python cad/compare_sections.py models/experimental/triflex-v31-experimental.stl models/experimental/triflex-v32-experimental.stl cad/profiles/v32.json
```

## Rules

- These scripts never modify a stable STL; they only read it.
- Any generated STL is a new experimental revision and must be physically tested before it can be called stable (see `AGENTS.md`).
- Change one mechanical variable per revision. To test a geometry change, edit the profile (for example scale the arm section with `scale_arms.py`) in a new profile file, not the reference STL.
