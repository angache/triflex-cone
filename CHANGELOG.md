# Changelog

## Unreleased
### Added
- Initial TriFlex repository structure.
- Engineering baseline documentation.
- Printing reference profile documentation.
- Physical test log.
- Repository engineering instructions.
- `models/stable/triflex-v29.stl` — the physically validated V29 STL, preserved byte-for-byte (5 closed, non-unioned shells).
- `models/experimental/triflex-v30-experimental.stl` — generated V30 STL, not physically validated.
- `cura/TriFlex_Ender3S1_TPU95A_V29_Validated.curaprofile` — reference profile extracted from the validated V29 G-code; only the display name changed.
- `cura/legacy/Ender3_S1_RhinoLab_TPU95A_HS_V28_SAFE_V24.curaprofile` — original profile kept as a source artifact (not the V29 reference).

### Changed
- docs/PRINTING.md: validated V29 print used `adhesion_type = none` (no brim); 6 mm brim is documented only as an optional adhesion aid.

### Stable reference
- V29: H32 / base Ø38 / top Ø9 / helix Ø3.3 / membrane 1.30 mm / base-connected membranes / center-open underside / 3 mm compliant-tip allowance.

### Experimental
- V30: V29 baseline with target helix diameter reduced from Ø3.3 to Ø3.1 mm. Physical validation pending.
