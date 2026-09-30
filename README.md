# TriFlex

**TriFlex — A 3D-printable triple-helix piezo trigger cone for electronic mesh drum pads.**

TriFlex is a mechanical trigger-cone project for electronic drums using mesh heads and piezo sensors. Instead of a conventional solid foam cone, it uses three TPU helical spring arms and stabilizing membranes to tune compliance, lateral stability, sensitivity, and hotspot behavior.

## Project status

**Current stable physical baseline: V29**

- TPU body height: 32 mm
- Base: Ø38 mm
- Top contact: Ø9 mm
- Three helix arms: Ø3.3 mm
- Membrane: 1.30 mm
- Membrane roots connected to base
- Center-open underside
- 3 mm allowance for a compliant top interface

V29 has been physically printed and tested and produced excellent sensitivity with a substantial reduction in hotspot compared with the earlier V26 configuration.

**Current experiment: V30**

V30 preserves the V29 target geometry and reduces only the helix-arm target diameter from Ø3.3 mm to Ø3.1 mm. It is generated but has not yet been physically validated.

## Documentation

- [Design and geometry](docs/DESIGN.md)
- [Printing guide](docs/PRINTING.md)
- [Physical testing log](docs/TESTING.md)
- [Engineering instructions](AGENTS.md)
- [Changelog](CHANGELOG.md)

## Development discipline

TriFlex revisions should normally change one mechanical variable at a time. Generated geometry and engineering hypotheses must be distinguished from physically tested results. V29 remains unchanged as the stable reference while experimental revisions are evaluated.

## License

TriFlex is **source-available for personal and non-commercial use**. Commercial use is not granted by the repository license.

Read [LICENSE.md](LICENSE.md) before downloading, modifying, printing, or redistributing the project. Commercial manufacture, sale, inclusion in paid kits/products, or other commercial exploitation requires a separate written license; see [COMMERCIAL-LICENSE.md](COMMERCIAL-LICENSE.md).

This project is not described as OSI open source because commercial use is restricted.

## Independence / trademarks

TriFlex is an independent project. Any third-party manufacturer or product names used in technical compatibility notes are descriptive only and do not imply affiliation, sponsorship, or endorsement.

## Development state

The repository is under active engineering development. Durability, print-to-print repeatability, and extended strike testing are planned before a public production release.
