# Regulatory Scope Notes

**This project is a software simulation and decision-logic reference
implementation. It is not a certified spectrum-management product and
must not be used to make real-world transmission decisions without
independent regulatory review.**

## What's included

`data/sample/protected_bands.csv` contains three small, clearly labeled
**sample/illustrative** frequency ranges within the demo's 400-460 MHz scan
window, loosely modeled on general public-safety and federal-reserved band
*categories* that are publicly known to exist in many jurisdictions. They
are placeholders for demonstrating the allocator's protected-band-avoidance
logic — they are not sourced from, and should not be treated as equivalent
to, any official frequency allocation table.

## What you must do before any real-world use

1. Replace the sample protected-band data with an authoritative,
   currently maintained source for your jurisdiction and intended
   frequency range — e.g., in the United States, the FCC Table of
   Frequency Allocations (47 CFR Part 2) and any relevant Part 15/90/97
   rules; consult your national spectrum regulator elsewhere (Ofcom,
   ETSI/CEPT allocations in the EU, ISED in Canada, etc.).
2. Confirm your specific equipment, use case, and frequency range have
   the appropriate license or unlicensed-use authorization.
3. Have any RF hardware integration reviewed by a qualified RF/
   telecommunications engineer and, where applicable, a communications
   lawyer or regulatory compliance specialist before transmitting.
4. Treat `SDRInterface`/`MockSDR` as a software contract only — connecting
   it to real hardware is entirely the integrator's responsibility, and
   this project does not provide, and is not intended to provide, any
   RF transmission capability out of the box.

## Why this matters

Interfering with public-safety, aeronautical, or other protected radio
services can be dangerous and is illegal in virtually every jurisdiction.
The protected-band-avoidance *pattern* demonstrated here (never allocate a
channel overlapping a registered protected band) is a reasonable
architectural pattern — but it is only as safe as the data source feeding
it, and this repository's sample data is not that source.
