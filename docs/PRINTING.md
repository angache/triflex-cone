# TriFlex Printing Guide

## Reference setup
- Printer: Creality Ender-3 S1
- Extruder: Sprite direct drive
- Nozzle: 0.4 mm
- Material: RhinoLab TPU 95A HS
- Slicer reference: Cura 5.2.1

## Current reference profile
Reference Cura profile: `cura/TriFlex_Ender3S1_TPU95A_V29_Validated.curaprofile`.

| Setting | Value |
|---|---:|
| Layer height | 0.20 mm |
| First layer | 0.20 mm |
| Nozzle | 220°C |
| First-layer nozzle | 225°C |
| Bed | 35°C |
| First-layer bed | 40°C |
| Flow | 100% |
| Print speed | 28 mm/s |
| Wall speed | 25 mm/s |
| Outer wall | 22 mm/s |
| Top/bottom | 22 mm/s |
| Travel | 180 mm/s |
| Retraction | 0.5 mm |
| Retraction speed | 15 mm/s |
| Fan | 20-35% after first layer |
| Minimum layer time | 10 s |
| Build plate adhesion | None (`adhesion_type = none`) — no brim |
| Supports | Disabled |

Retraction prime speed: 15 mm/s. Z-hop is off. Combing is set to infill and avoid-other-parts is enabled.

## Validated V29 print
The physically validated V29 test print was sliced in Cura 5.2.1 (machine definition `creality_ender3s1`) with:
- `adhesion_type = none`
- therefore **no brim** was used.

The profile also stores `brim_width = 6`. That value is inactive when `adhesion_type = none` and is not part of the validated V29 setup.

G-code summary of the validated print: max Z 32 mm, estimated print time 3934 s (~66 min), 1.40 m of filament.

The validated G-code is archived outside this repository (SHA-256 `76a47994a570abb57471f831934960b78eb8f7002983c95e7bb85267b698f32d`).

The reference profile `cura/TriFlex_Ender3S1_TPU95A_V29_Validated.curaprofile` was extracted from the settings embedded in that G-code. Only the profile display name was changed; all slicing values are identical to the validated print.

`cura/legacy/Ender3_S1_RhinoLab_TPU95A_HS_V28_SAFE_V24.curaprofile` is the original hand-kept profile, preserved as a source artifact. It is **not** the V29 reference: it sets `adhesion_type = brim` and targets `creality_base`, so importing it as-is would print a brim.

## Brim (optional troubleshooting aid)
A 6 mm brim may be enabled if first-layer adhesion fails or corners lift. It is an adhesion aid only, not the validated V29 default. A print made with a brim deviates from the validated setup and should be noted as such in docs/TESTING.md.

## TPU moisture
TPU moisture strongly affects stringing. The current material produced nearly string-free tower tests after drying at 70°C for approximately 8 hours.

For repeatability:
- dry before critical prints;
- print directly from a filament dryer when practical;
- keep the spool enclosed;
- use a separate room hygrometer rather than treating the dryer's internal RH display as room humidity.

A cautious starting dryer temperature while actively printing is approximately 50-55°C, subject to spool/dryer/material manufacturer limits.

## Supports
The baseline model is intended to minimize support dependency. If support is required, a conservative TPU starting point is:
- Tree support
- Build plate only
- ~55° overhang threshold
- Zig Zag
- 5-8% density
- 0.30 mm Z distance
- ~0.6 mm X/Y distance
- interface enabled, 0.20-0.40 mm thick, 20-25% density

Avoid dense Grid support for this geometry.

## Bed removal
Let the plate cool before removal. Flex the magnetic sheet and avoid pulling the part by its helix arms. If adhesion is excessive, check first-layer squish and consider raising Z offset about 0.05 mm after calibration.
