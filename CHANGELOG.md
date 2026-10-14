# Changelog

## 2026-10-09 — V33 and V34 generated experimental
### Added
- docs/TESTING.md: V33 and V34 (designer-built with the builder).

## 2026-10-09 — Parametric variant builds
### Added
- `cad/build.py` and `cad/variants/*.toml`: variants are built from a parameter file (arm diameter, arm taper length, membrane thickness) with range checks, mesh checks, optional comparison and protection against overwriting an existing revision.
- `cad/variants/v32.toml` reproduces V32 byte for byte.
- `cad/gui.py` and `TriFlex Builder.command`: a small window for building variants and opening them in Cura.
### Fixed
- `cad/generate_triflex.py`: for some membrane thicknesses a membrane root ring touched V30's base surface near z = 2.35 and the result was not watertight; such builds now drop the (linear) inner root rings. V31 and V32 outputs are unchanged. The arm diameter and membrane thickness ranges were swept (65 builds, all single closed solids).

## 2026-10-06 — V32 generated experimental
### Added
- `cad/scale_arms.py` — scales the arm section of a profile to a target diameter, blending back to the original thickness over 2.5 mm at the root and the neck.
- `cad/profiles/v32.json` — V31 profile with Ø3.00 mm arms.
- `models/experimental/triflex-v32-experimental.stl` — V31 with thinner helix arms (Ø3.29 → Ø3.00 mm), the only change. Generated, not yet printed (SHA-256 `1a1ccf2bb3068117fb29de91926a4e548ac2b586d4709e33ae6693eb99fbac7d`).
- docs/TESTING.md: V32 geometry check, hypothesis and required tests.
### Changed
- `cad/compare_sections.py`: arm waviness takes the membrane positions from the profile, so a unioned STL (such as V31) can be the reference.

## 2026-10-06 — V31 first print
### Added
- docs/TESTING.md: V31 print 1 with the reference profile (no supports, no brim). Visually very clean surface; no functional test yet.

## 2026-10-06 — V31 regenerated with swept tube arms
### Changed
- `cad/extract_profile.py`: the arm is now described as an elliptic tube (centerline plus perpendicular section fitted with seam rejection, scaled to V30's section area) instead of order-8 Fourier horizontal sections, which had turned the V30 seam into lengthwise grooves.
- `cad/generate_triflex.py`: arms are swept perpendicular to the centerline and end inside V30's base root and neck; the root fillets stay V30 geometry.
- `cad/compare_sections.py`: optional profile argument adds a direct arm waviness measurement.
- `models/experimental/triflex-v31-experimental.stl` regenerated before any print (SHA-256 `4c81be7d1507448730b0600a13fc3b6006335c0be718009b19d561e1b6b4dd92`); arm waviness 0.5 µm vs 67.5 µm on V30. The first build (`eb9c67e8…`) is superseded.

## 2026-10-06 — V31 generated experimental
### Added
- `cad/` — parametric source pipeline: `extract_profile.py` (smooth profile from a tested STL), `generate_triflex.py` (lofted arms and membranes, unioned with the reference base, neck and top), `compare_sections.py` (layer-by-layer comparison), pinned `requirements.txt`.
- `cad/profiles/v31.json` — smooth profile extracted from the stable V30 STL.
- `models/experimental/triflex-v31-experimental.stl` — V30 geometry with smooth arm and membrane surfaces; single closed solid. Generated, not yet printed (SHA-256 `eb9c67e8ad07a56f6ba62ad608ad35d782ea5ea77b752520962588f391c975b7`).
- docs/TESTING.md: V31 geometry check and required tests.

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
