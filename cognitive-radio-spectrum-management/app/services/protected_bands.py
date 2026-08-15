"""
Illustrative protected-band registry.

IMPORTANT: this is sample, illustrative data for demonstration and testing
only. It is NOT an authoritative regulatory source. Real deployments must
load an authoritative table (e.g. the FCC Table of Frequency Allocations in
the U.S., or the equivalent national regulator elsewhere) and keep it
current. See docs/REGULATORY_NOTES.md.
"""
from __future__ import annotations

import csv
import os
from dataclasses import dataclass

SAMPLE_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "sample", "protected_bands.csv")


@dataclass
class Band:
    name: str
    start_hz: int
    end_hz: int
    category: str
    source: str = "sample-illustrative"

    def overlaps(self, start_hz: int, end_hz: int) -> bool:
        return self.start_hz < end_hz and start_hz < self.end_hz


def load_protected_bands(path: str = SAMPLE_PATH) -> list[Band]:
    bands = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            bands.append(Band(
                name=row["name"],
                start_hz=int(row["start_hz"]),
                end_hz=int(row["end_hz"]),
                category=row["category"],
                source=row.get("source", "sample-illustrative"),
            ))
    return bands


def is_protected(start_hz: int, end_hz: int, bands: list[Band] | None = None) -> Band | None:
    """Return the first protected band overlapping [start_hz, end_hz), or None."""
    bands = bands if bands is not None else load_protected_bands()
    for band in bands:
        if band.overlaps(start_hz, end_hz):
            return band
    return None
