"""
Generate a realistic, fully synthetic sample data set for SpectrumSense.

Writes into data/sample/:
  node_registry.csv, protected_bands.csv, spectrum_scans.csv, power_control_log.csv

Safe to re-run; deterministic given the fixed random seed.
"""
from __future__ import annotations

import datetime as dt
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.services.spectrum_sensor import channel_grid, simulate_node_scan, generate_occupancy_pattern  # noqa: E402
from app.services.power_control import Link, run_power_control  # noqa: E402

RANDOM_SEED = 11
SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "sample")

FREQ_START_HZ = 400_000_000
FREQ_END_HZ = 460_000_000
CHANNEL_BW_HZ = 5_000_000  # -> 12 channels

NODE_LOCATIONS = [
    ("node-01", "Rooftop A - North Campus", 41.881, -87.629),
    ("node-02", "Rooftop B - South Campus", 41.870, -87.625),
    ("node-03", "Water Tower - East Ridge", 41.878, -87.610),
    ("node-04", "Comms Tower - West Field", 41.883, -87.645),
    ("node-05", "Rooftop C - Downtown", 41.876, -87.632),
    ("node-06", "Hilltop Relay - Overlook Park", 41.865, -87.618),
    ("node-07", "Rooftop D - Riverside", 41.890, -87.638),
    ("node-08", "Mast - Industrial Park", 41.860, -87.641),
]


def generate_node_registry() -> pd.DataFrame:
    rng = np.random.default_rng(RANDOM_SEED)
    rows = []
    for node_id, location, lat, lon in NODE_LOCATIONS:
        rows.append({
            "node_id": node_id,
            "location_description": location,
            "latitude": lat,
            "longitude": lon,
            "reliability_weight": round(float(rng.uniform(0.75, 1.0)), 3),
            "status": "active",
        })
    return pd.DataFrame(rows)


def generate_protected_bands() -> pd.DataFrame:
    """
    Illustrative, sample-only protected-band registry within the demo scan
    range (400-460 MHz), loosely inspired by publicly known general-purpose
    allocation categories. NOT an authoritative regulatory source — see
    docs/REGULATORY_NOTES.md.
    """
    rows = [
        {"name": "Sample Public-Safety Band A", "start_hz": 420_000_000, "end_hz": 425_000_000,
         "category": "public-safety", "source": "sample-illustrative"},
        {"name": "Sample Public-Safety Band B", "start_hz": 450_000_000, "end_hz": 454_000_000,
         "category": "public-safety", "source": "sample-illustrative"},
        {"name": "Sample Federal/Government Reserved Band", "start_hz": 406_000_000, "end_hz": 410_000_000,
         "category": "federal-reserved", "source": "sample-illustrative"},
    ]
    return pd.DataFrame(rows)


def generate_spectrum_scans(n_timesteps: int = 48, interval_minutes: int = 30) -> pd.DataFrame:
    centers = channel_grid(FREQ_START_HZ, FREQ_END_HZ, CHANNEL_BW_HZ)
    n_channels = len(centers)

    start_time = dt.datetime.utcnow().replace(minute=0, second=0, microsecond=0) - dt.timedelta(minutes=interval_minutes * n_timesteps)

    all_rows = []
    for t in range(n_timesteps):
        timestamp = start_time + dt.timedelta(minutes=interval_minutes * t)
        occupancy_pattern = generate_occupancy_pattern(n_channels, seed=RANDOM_SEED + t, busy_fraction=0.25)

        for node_id, _, _, _, in [(n[0], n[1], n[2], n[3]) for n in NODE_LOCATIONS]:
            reliability = 0.85  # overwritten below from registry for realism
            reports = simulate_node_scan(
                node_id=node_id,
                freq_start_hz=FREQ_START_HZ,
                freq_end_hz=FREQ_END_HZ,
                channel_bandwidth_hz=CHANNEL_BW_HZ,
                timestamp=timestamp,
                occupancy_pattern=occupancy_pattern,
                reliability_weight=reliability,
                seed=RANDOM_SEED + t + hash(node_id) % 1000,
            )
            all_rows.extend(reports)

    return pd.DataFrame(all_rows)


def generate_power_control_log(n_links: int = 12) -> pd.DataFrame:
    rng = np.random.default_rng(RANDOM_SEED)
    links = []
    for i in range(n_links):
        gain_own = 10 ** (rng.uniform(-9, -7))
        gains_other = [10 ** (rng.uniform(-12, -10)) for _ in range(n_links - 1)]
        links.append(Link(link_id=f"link-{i+1:02d}", gain_to_own_receiver=gain_own, gains_to_other_receivers=gains_other))

    history = run_power_control(
        links, target_sinr_db=10.0, max_iterations=50, max_tx_power_dbm=30.0
    )

    rows = []
    for link_history in history:
        for state in link_history:
            rows.append(state.model_dump())
    return pd.DataFrame(rows)


def main() -> None:
    os.makedirs(SAMPLE_DIR, exist_ok=True)

    node_df = generate_node_registry()
    node_df.to_csv(os.path.join(SAMPLE_DIR, "node_registry.csv"), index=False)

    bands_df = generate_protected_bands()
    bands_df.to_csv(os.path.join(SAMPLE_DIR, "protected_bands.csv"), index=False)

    scans_df = generate_spectrum_scans()
    # apply per-node reliability weight from the registry for consistency
    weight_map = dict(zip(node_df["node_id"], node_df["reliability_weight"]))
    scans_df["reliability_weight"] = scans_df["node_id"].map(weight_map)
    scans_df.to_csv(os.path.join(SAMPLE_DIR, "spectrum_scans.csv"), index=False)

    power_df = generate_power_control_log()
    power_df.to_csv(os.path.join(SAMPLE_DIR, "power_control_log.csv"), index=False)

    print(f"Generated {len(node_df)} sensing nodes")
    print(f"Generated {len(bands_df)} sample protected bands")
    print(f"Generated {len(scans_df)} spectrum scan reports "
          f"({scans_df['timestamp'].nunique()} timesteps x {scans_df['node_id'].nunique()} nodes x "
          f"{scans_df['channel_index'].nunique()} channels)")
    print(f"Generated {len(power_df)} power-control log rows across {power_df['link_id'].nunique()} links")


if __name__ == "__main__":
    main()
