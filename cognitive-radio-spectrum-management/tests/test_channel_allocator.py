import datetime as dt

from app.models import FusionResult
from app.services.channel_allocator import allocate_channel, allocate_all_channels_report
from app.services.protected_bands import Band

CHANNEL_BW = 5_000_000
TS = dt.datetime(2026, 1, 1, 12, 0)


def _fusion(channel_index, center_freq_hz, decision, score):
    return FusionResult(
        channel_index=channel_index, center_freq_hz=center_freq_hz, timestamp=TS,
        weighted_occupied_score=score, decision=decision, n_reports=3,
    )


def test_allocator_skips_protected_band():
    fused = [
        _fusion(0, 402_500_000, "unoccupied", 0.1),   # inside protected band below
        _fusion(1, 407_500_000, "unoccupied", 0.2),
    ]
    bands = [Band("Protected", 400_000_000, 405_000_000, "public-safety")]
    allocation = allocate_channel(fused, CHANNEL_BW, bands)
    assert allocation is not None
    assert allocation.channel_index == 1


def test_allocator_skips_occupied_channel():
    fused = [
        _fusion(0, 402_500_000, "occupied", 0.9),
        _fusion(1, 407_500_000, "unoccupied", 0.1),
    ]
    allocation = allocate_channel(fused, CHANNEL_BW, bands=[])
    assert allocation.channel_index == 1


def test_allocator_prefers_quietest_channel():
    fused = [
        _fusion(0, 402_500_000, "unoccupied", 0.4),
        _fusion(1, 407_500_000, "unoccupied", 0.1),
    ]
    allocation = allocate_channel(fused, CHANNEL_BW, bands=[])
    assert allocation.channel_index == 1


def test_allocator_returns_none_when_all_blocked():
    fused = [_fusion(0, 402_500_000, "occupied", 0.9)]
    allocation = allocate_channel(fused, CHANNEL_BW, bands=[])
    assert allocation is None


def test_full_report_labels_each_channel():
    fused = [
        _fusion(0, 402_500_000, "occupied", 0.9),
        _fusion(1, 407_500_000, "unoccupied", 0.1),
    ]
    bands = [Band("Protected", 420_000_000, 425_000_000, "public-safety")]
    report = allocate_all_channels_report(fused, CHANNEL_BW, bands)
    statuses = {r.channel_index: r.status for r in report}
    assert statuses[0] == "unavailable_occupied"
    assert statuses[1] == "assigned"
