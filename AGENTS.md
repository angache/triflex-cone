# TriFlex Engineering Instructions

TriFlex is a 3D-printable triple-helix piezo trigger cone for electronic mesh drum pads.

## Engineering baseline
The current stable physical reference is V30:
- Overall TPU body height: 32 mm
- Base diameter: 38 mm
- Top contact diameter: 9 mm
- Helix arm diameter: 3.1 mm
- Membrane thickness: 1.30 mm
- Three independent helix arms at 120 degrees
- Membrane roots connected to the base plate
- Center-open underside
- 3 mm top allowance for felt/other compliant contact material

V30 differs from V29 only in helix arm diameter (3.3 -> 3.1 mm). It showed excellent sensitivity and ghost-note response with substantially reduced hotspot, multiple prints behaved consistently, and it passed strike testing of up to approximately 10,000 hits (2026-10-05). A controlled V29/V30 A/B comparison and longer itemized durability runs remain outstanding.

V29 is the previous stable reference and is preserved unchanged as a control. It produced excellent sensitivity and substantially reduced hotspot compared with earlier prototypes.

## Non-negotiable development rules
1. Change one mechanical variable per experimental revision whenever practical.
2. Keep V30 unchanged as the stable physical reference and V29 unchanged as the previous control.
3. Clearly distinguish measured/physical test results from hypotheses.
4. Preserve the center-open piezo load path unless explicitly testing that variable.
5. Do not add a flexible neck below the top platform unless explicitly requested.
6. Do not use generic whole-mesh smoothing to repair membrane geometry.
7. Validate STL dimensions and watertightness before release.
8. Never describe an unprinted model as physically validated.
9. Record each physical test in docs/TESTING.md.
10. Do not use Roland or another manufacturer's trademark as the TriFlex product name.
11. Reproducibility of a physically validated artifact takes priority over cosmetic CAD/mesh cleanup. Do not repair, boolean-union, remesh, re-export, or normalize a stable file. Any cleaned-up variant is a new experimental revision with its own identifier and must be physically retested before it can be called stable.

## Canonical V30 artifacts
- STL: `models/stable/triflex-v30.stl`, preserved byte-for-byte (SHA-256 `1380294200b95626e5e04df2e983cc174459755fc91b3e286d876464239f929f`). Like V29, it contains 5 closed, non-unioned shells.
- Printing reference: `cura/TriFlex_Ender3S1_TPU95A_V29_Validated.curaprofile` remains the documented reference profile.

## Canonical V29 artifacts (previous stable control)
- STL: `models/stable/triflex-v29.stl`, preserved byte-for-byte (SHA-256 `6ba6824379025cc35e50dc8483c4deec778fa85bb63e8777b1d8f94238a3a9a2`). It contains 5 closed, non-unioned shells; this is intentional because this exact file was physically validated.
- Cura profile: `cura/TriFlex_Ender3S1_TPU95A_V29_Validated.curaprofile`, extracted from the validated G-code (`adhesion_type = none`, no brim).

## Piezo architecture
The piezo is approximately 27-28 mm diameter. A small centered adhesive pad supports the metal side against the drum plate. TriFlex contacts the ceramic side. The current annular/peripheral loading and open center permit piezo flexure and are considered part of the sensitivity mechanism.

## Material and printing reference
Current development material: RhinoLab TPU 95A HS.
Reference printer: Ender-3 S1, direct drive, 0.4 mm nozzle.
See docs/PRINTING.md for the current profile.

## Licensing reference
- Copyright holder: Ali Tuna.
- Repository materials are licensed under CC BY-NC-SA 4.0.
- Non-commercial sharing and adaptation are allowed with attribution and ShareAlike.
- Commercial use requires separate written permission.
- Do not replace or broaden the license without explicit instruction from the rights holder.

## Repository status terminology
- Stable: selected reference revision that has completed the required physical test scope and is preserved as a control.
- Physically tested experimental: printed and functionally tested, but still awaiting required comparison, repeatability, or durability evidence.
- Generated experimental: generated but not yet physically tested.
- Deprecated: rejected or superseded geometry.
