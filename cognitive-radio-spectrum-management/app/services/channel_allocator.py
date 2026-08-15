"""
Dynamic channel allocation.

Given fused cooperative-sensing results and the protected-band registry,
selects the best available channel for an SDR link — one that does not
overlap any protected band and is not currently assessed as occupied by
cooperative sensing. Ties are broken by preferring the channel with the
lowest weighted-occupancy score (i.e. historically/currently quietest),
which tends to minimize future interference risk.
"""
from __future__ import annotations

from app.models import FusionResult, ChannelAllocation
from app.services.protected_bands import Band, is_protected


def allocate_channel(
    fusion_results: list[FusionResult],
    channel_bandwidth_hz: int,
    protected_bands: list[Band],
) -> ChannelAllocation | None:
    """Pick the best free channel. Returns None if no channel is available."""
    candidates = []
    for result in fusion_results:
        start_hz = result.center_freq_hz - channel_bandwidth_hz // 2
        end_hz = result.center_freq_hz + channel_bandwidth_hz // 2

        blocking_band = is_protected(start_hz, end_hz, protected_bands)
        if blocking_band is not None:
            continue
        if result.decision == "occupied":
            continue
        candidates.append(result)

    if not candidates:
        return None

    best = min(candidates, key=lambda r: r.weighted_occupied_score)
    return ChannelAllocation(
        channel_index=best.channel_index,
        center_freq_hz=best.center_freq_hz,
        status="assigned",
        reason=f"Lowest cooperative-sensing occupancy score ({best.weighted_occupied_score:.3f}) among available channels",
    )


def allocate_all_channels_report(
    fusion_results: list[FusionResult],
    channel_bandwidth_hz: int,
    protected_bands: list[Band],
) -> list[ChannelAllocation]:
    """Build a full per-channel status report (assigned / blocked / occupied)."""
    report = []
    for result in fusion_results:
        start_hz = result.center_freq_hz - channel_bandwidth_hz // 2
        end_hz = result.center_freq_hz + channel_bandwidth_hz // 2

        blocking_band = is_protected(start_hz, end_hz, protected_bands)
        if blocking_band is not None:
            report.append(ChannelAllocation(
                channel_index=result.channel_index,
                center_freq_hz=result.center_freq_hz,
                status="unavailable_protected",
                reason=f"Overlaps protected band '{blocking_band.name}' ({blocking_band.category})",
            ))
        elif result.decision == "occupied":
            report.append(ChannelAllocation(
                channel_index=result.channel_index,
                center_freq_hz=result.center_freq_hz,
                status="unavailable_occupied",
                reason=f"Cooperative sensing score {result.weighted_occupied_score:.3f} indicates occupancy",
            ))
        else:
            report.append(ChannelAllocation(
                channel_index=result.channel_index,
                center_freq_hz=result.center_freq_hz,
                status="assigned",
                reason="Available: unoccupied and outside all protected bands",
            ))
    return report
