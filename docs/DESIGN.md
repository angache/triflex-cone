# TriFlex Design

## Purpose
TriFlex replaces the conventional foam trigger cone used between a mesh drum head and a piezoelectric sensor. Its mechanical structure uses three helical TPU spring arms plus thin stabilizing membranes.

## Current stable geometry — V29
| Parameter | Value |
|---|---:|
| Body height | 32 mm |
| Base diameter | 38 mm |
| Top contact diameter | 9 mm |
| Helix arms | 3 |
| Helix phase | 120° |
| Helix arm diameter | 3.3 mm |
| Membrane thickness | 1.30 mm |
| Top compliance allowance | 3 mm |
| Underside | Center-open |

The membrane roots are connected to the base plate.

## Mechanical concept
The helix arms provide vertical compliance. The membranes add lateral stability and tune the spring response without turning the geometry into a closed shell.

The center-open underside is intentional. In the current sensor architecture the piezo is supported near its center from below while TriFlex transfers force through an annular/peripheral region from above. This permits piezo flexure and is believed to contribute strongly to sensitivity.

That explanation is a mechanical hypothesis consistent with the observed behavior; it has not yet been instrumented with force/displacement or piezo strain measurements.

## Development history
Early solid-cone concepts were too stiff. Bare helix concepts were too soft and laterally unstable. Adding membranes improved stability. V26 (35 mm height, 9 mm top, 3.3 mm helix, 1.50 mm membrane) achieved excellent sensitivity but had a strong hotspot.

V29 changed the body to 32 mm with a 3 mm compliant-tip allowance, used a 1.30 mm membrane, and connected membrane roots to the base. Physical testing showed excellent sensitivity with a substantial hotspot reduction.

Because multiple parameters changed between earlier prototypes and V29, the hotspot improvement must not be attributed to membrane thickness alone.

## Physically tested experimental V30
V30 keeps the V29 target geometry except for helix arm diameter:
- V29: 3.3 mm
- V30: 3.1 mm

The goal is to reduce vertical spring stiffness while retaining the 1.30 mm membranes and lateral stability.

V30 has been physically printed and completed an initial successful functional test. Excellent sensitivity and ghost-note response, substantially reduced hotspot, and good print quality were observed in a 12-inch test pad. These are subjective initial observations; controlled V29/V30 comparison, repeatability, and durability testing remain outstanding. V30 therefore remains experimental, while V29 remains the stable control.

## Trademark note
TriFlex is an independent project. Compatibility with particular electronic-drum systems may be documented descriptively, but manufacturer names and trademarks are not part of the TriFlex brand.
