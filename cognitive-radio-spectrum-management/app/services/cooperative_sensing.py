"""
Cooperative (distributed) spectrum sensing fusion center.

Combines per-node occupancy reports for the same channel/timestamp into a
single, more robust decision using reliability-weighted soft fusion — a
standard approach in the cognitive-radio literature for overcoming
single-node sensing errors caused by fading, shadowing, or a hidden
primary-user problem.
"""
from __future__ import annotations

import datetime as dt
from collections import defaultdict

from app.models import NodeReport, FusionResult


def fuse_reports(reports: list[NodeReport], occupied_threshold: float) -> list[FusionResult]:
    """
    Group reports by (channel_index, timestamp) and compute a
    reliability-weighted occupancy score in [0, 1]:

        score = sum(weight_i * occupied_i) / sum(weight_i)

    A channel is declared "occupied" if score >= occupied_threshold.
    This is a soft generalization of the classical OR-rule / majority-vote
    fusion rules used in cooperative spectrum sensing.
    """
    groups: dict[tuple[int, dt.datetime], list[NodeReport]] = defaultdict(list)
    for r in reports:
        groups[(r.channel_index, r.timestamp)].append(r)

    results = []
    for (channel_index, timestamp), group in groups.items():
        total_weight = sum(r.reliability_weight for r in group) or 1.0
        weighted_occupied = sum(r.reliability_weight for r in group if r.occupied)
        score = weighted_occupied / total_weight

        results.append(FusionResult(
            channel_index=channel_index,
            center_freq_hz=group[0].center_freq_hz,
            timestamp=timestamp,
            weighted_occupied_score=round(score, 4),
            decision="occupied" if score >= occupied_threshold else "unoccupied",
            n_reports=len(group),
        ))

    return sorted(results, key=lambda r: r.channel_index)


def latest_fusion_snapshot(reports: list[NodeReport], occupied_threshold: float) -> list[FusionResult]:
    """Fuse only the most recent timestamp present in `reports`."""
    if not reports:
        return []
    latest_ts = max(r.timestamp for r in reports)
    latest_reports = [r for r in reports if r.timestamp == latest_ts]
    return fuse_reports(latest_reports, occupied_threshold)
