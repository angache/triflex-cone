# TriFlex Printing Guide

## Reference setup
- Printer: Creality Ender-3 S1
- Extruder: Sprite direct drive
- Nozzle: 0.4 mm
- Material: RhinoLab TPU 95A HS
- Slicer reference: Cura 5.2.1

## Current reference profile
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
| Brim | 6 mm reference; reduce/disable if unnecessary |

Retraction prime speed: 15 mm/s. Z-hop is off. Combing is set to infill and avoid-other-parts is enabled.

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
