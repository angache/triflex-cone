# TriFlex Engineering Instructions

TriFlex is a 3D-printable triple-helix piezo trigger cone for electronic mesh drum pads.

## Engineering baseline
The physically validated reference is V29:
- Overall TPU body height: 32 mm
- Base diameter: 38 mm
- Top contact diameter: 9 mm
- Helix arm diameter: 3.3 mm
- Membrane thickness: 1.30 mm
- Three independent helix arms at 120 degrees
- Membrane roots connected to the base plate
- Center-open underside
- 3 mm top allowance for felt/other compliant contact material

V29 produced excellent sensitivity and substantially reduced hotspot compared with earlier prototypes.

V30 is experimental and unvalidated:
- Same baseline as V29
- Only intended mechanical change: helix arm diameter 3.3 -> 3.1 mm

## Non-negotiable development rules
1. Change one mechanical variable per experimental revision whenever practical.
2. Keep V29 unchanged as the stable physical reference.
3. Clearly distinguish measured/physical test results from hypotheses.
4. Preserve the center-open piezo load path unless explicitly testing that variable.
5. Do not add a flexible neck below the top platform unless explicitly requested.
6. Do not use generic whole-mesh smoothing to repair membrane geometry.
7. Validate STL dimensions and watertightness before release.
8. Never describe an unprinted model as physically validated.
9. Record each physical test in docs/TESTING.md.
10. Do not use Roland or another manufacturer's trademark as the TriFlex product name.

## Piezo architecture
The piezo is approximately 27-28 mm diameter. A small centered adhesive pad supports the metal side against the drum plate. TriFlex contacts the ceramic side. The current annular/peripheral loading and open center permit piezo flexure and are considered part of the sensitivity mechanism.

## Material and printing reference
Current development material: RhinoLab TPU 95A HS.
Reference printer: Ender-3 S1, direct drive, 0.4 mm nozzle.
See docs/PRINTING.md for the current profile.

## Repository status terminology
- Stable: physically printed and tested with successful results.
- Experimental: generated but not yet physically validated.
- Deprecated: rejected or superseded geometry.
