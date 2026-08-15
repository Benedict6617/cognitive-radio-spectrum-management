"""
Simulated wideband spectrum energy-detection sensing.

Generates synthetic per-channel power measurements for a sensing node,
modeling a noise floor, occasional primary-user (incumbent) activity, and
measurement noise/fading. This module never touches real RF hardware —
see app/services/sdr_interface.py for the hardware abstraction boundary.
"""
from __future__ import annotations

import datetime as dt

import numpy as np

NOISE_FLOOR_DBM = -100.0
DETECTION_THRESHOLD_DBM = -90.0


def channel_grid(freq_start_hz: int, freq_end_hz: int, channel_bandwidth_hz: int) -> list[int]:
    """Return the center frequency (Hz) of each channel across the scan range."""
    n_channels = max(1, (freq_end_hz - freq_start_hz) // channel_bandwidth_hz)
    return [
        int(freq_start_hz + channel_bandwidth_hz * i + channel_bandwidth_hz / 2)
        for i in range(n_channels)
    ]


def simulate_node_scan(
    node_id: str,
    freq_start_hz: int,
    freq_end_hz: int,
    channel_bandwidth_hz: int,
    timestamp: dt.datetime,
    occupancy_pattern: np.ndarray,
    reliability_weight: float,
    seed: int,
) -> list[dict]:
    """
    Simulate one wideband scan sweep for a single node.

    `occupancy_pattern` is a per-channel array of "true" occupancy
    probabilities (0..1) representing simulated primary-user activity at
    this timestamp; the node's own noisy measurement is derived from it,
    so cooperative fusion across nodes has a meaningful signal to combine.
    """
    rng = np.random.default_rng(seed)
    centers = channel_grid(freq_start_hz, freq_end_hz, channel_bandwidth_hz)

    reports = []
    for idx, center_hz in enumerate(centers):
        true_occupied = rng.random() < occupancy_pattern[idx]
        if true_occupied:
            measured_power = rng.normal(-70.0, 4.0)
        else:
            measured_power = rng.normal(NOISE_FLOOR_DBM, 3.0)

        # node-level measurement noise / small-scale fading on top of the
        # "true" signal, so imperfect single-node sensing is realistic
        measured_power += rng.normal(0, 2.0)
        occupied = measured_power >= DETECTION_THRESHOLD_DBM

        reports.append({
            "node_id": node_id,
            "channel_index": idx,
            "center_freq_hz": center_hz,
            "timestamp": timestamp.isoformat(),
            "measured_power_dbm": round(float(measured_power), 2),
            "occupied": bool(occupied),
            "reliability_weight": reliability_weight,
        })
    return reports


def generate_occupancy_pattern(n_channels: int, seed: int, busy_fraction: float = 0.25) -> np.ndarray:
    """
    Build a per-channel "ground truth" occupancy-probability vector for one
    time step, with a handful of persistently busy channels (modeling
    incumbent users with regular usage) plus low background usage elsewhere.
    """
    rng = np.random.default_rng(seed)
    pattern = rng.uniform(0.02, 0.08, size=n_channels)
    n_busy = max(1, int(n_channels * busy_fraction))
    busy_channels = rng.choice(n_channels, size=n_busy, replace=False)
    pattern[busy_channels] = rng.uniform(0.6, 0.9, size=n_busy)
    return pattern
