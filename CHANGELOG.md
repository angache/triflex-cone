# Changelog

## 2026-10-05 — V30 promoted to stable
### Changed
- V30 promoted to the stable baseline after multiple prints behaved consistently and passed strike testing of up to approximately 10,000 hits.
- `models/experimental/triflex-v30-experimental.stl` moved to `models/stable/triflex-v30.stl` without modification (SHA-256 `1380294200b95626e5e04df2e983cc174459755fc91b3e286d876464239f929f`).
- V29 retained unchanged as the previous stable control.
- README, AGENTS.md, docs/DESIGN.md, docs/TESTING.md and docs/DEVELOPMENT-HISTORY.md updated for the new baseline.

## Unreleased
### Added
- Initial TriFlex repository structure.
- Engineering baseline documentation.
- Printing reference profile documentation.
- Physical test log.
- Repository engineering instructions.
- `models/stable/triflex-v29.stl` — the physically validated V29 STL, preserved byte-for-byte (5 closed, non-unioned shells).
- `models/experimental/triflex-v30-experimental.stl` — physically tested experimental V30 STL; repeatability and durability pending.
- `cura/TriFlex_Ender3S1_TPU95A_V29_Validated.curaprofile` — reference profile extracted from the validated V29 G-code; only the display name changed.
- `cura/legacy/Ender3_S1_RhinoLab_TPU95A_HS_V28_SAFE_V24.curaprofile` — original profile kept as a source artifact (not the V29 reference).
- V30 physical photo set covering PD-128 BC, KD-85, and DIY-pad installations, the felt interface, and original-cone comparisons.
- `docs/V30-PHOTO-LOG.md` — captions and context for the physical photo set.
- Public V30 test video demonstrating PD-128 BC, DIY pad, and KD-85 with SSD5 and raw acoustic audio.

### Changed
- docs/PRINTING.md: validated V29 print used `adhesion_type = none` (no brim); 6 mm brim is documented only as an optional adhesion aid.
- Replaced the custom personal/non-commercial license with the standardized CC BY-NC-SA 4.0 license; copyright holder recorded as Ali Tuna.

### Stable reference
- V30: V29 baseline with helix diameter reduced from Ø3.3 to Ø3.1 mm. Repeatability and ~10,000-hit durability test passed.
- V29 (previous stable control): H32 / base Ø38 / top Ø9 / helix Ø3.3 / membrane 1.30 mm / base-connected membranes / center-open underside / 3 mm compliant-tip allowance.
