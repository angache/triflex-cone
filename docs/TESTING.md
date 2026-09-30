# TriFlex Test Log

This file separates physical observations from engineering hypotheses.

## V26 — physical test
Geometry:
- H35
- base Ø38
- top Ø9
- helix Ø3.3
- membrane 1.50 mm
- center-open underside

Observed:
- Excellent sensitivity.
- Tested successfully on 8-inch and 12-inch mesh pads.
- Strong hotspot directly over the cone.

Conclusion:
V26 established that the triple-helix/membrane architecture can achieve very high sensitivity, but hotspot control required further development.

## V29 — physical test / current stable baseline
Geometry:
- H32
- base Ø38
- top Ø9
- helix Ø3.3
- membrane 1.30 mm
- membrane roots connected to base
- center-open underside
- 3 mm top allowance

Observed:
- Excellent overall response.
- Hotspot substantially lower than the previous configuration.
- User assessment: best-performing cone tested in the project so far.

Important:
Several mechanical variables differ from V26, so the hotspot reduction cannot yet be assigned to one variable.

## V30 — experimental / awaiting physical test
Intended geometry:
- Same as V29
- helix Ø3.1 instead of Ø3.3
- membrane remains 1.30 mm

Hypothesis:
Reducing arm diameter should soften the vertical spring response while preserving membrane-controlled lateral stability. A simple beam-style d^4 comparison suggests 3.1 mm arms have roughly 78% of the bending stiffness of 3.3 mm arms, but the actual TriFlex geometry is not a simple beam and physical testing is required.

### V30 test fields
- Printer/material:
- Pad diameter:
- Module:
- Sensitivity:
- Ghost-note response:
- Hotspot:
- Lateral stability:
- Durability observations:
- Result: PASS / MODIFY / REJECT

## Planned durability work
Before a public production release, test repeatability across multiple prints and conduct extended strike testing. Candidate milestones include 10,000 and 20,000 hits, followed by inspection for membrane-root cracking, helix fatigue, permanent set, top deformation, and response drift.
