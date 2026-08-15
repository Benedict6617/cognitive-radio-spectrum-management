import datetime as dt

from app.models import NodeReport
from app.services.cooperative_sensing import fuse_reports, latest_fusion_snapshot


def _report(node_id, occupied, weight, ts):
    return NodeReport(
        node_id=node_id, channel_index=0, center_freq_hz=402_500_000,
        timestamp=ts, measured_power_dbm=-70.0 if occupied else -100.0,
        occupied=occupied, reliability_weight=weight,
    )


def test_unanimous_occupied_detected():
    ts = dt.datetime(2026, 1, 1, 12, 0)
    reports = [_report(f"n{i}", True, 1.0, ts) for i in range(3)]
    fused = fuse_reports(reports, occupied_threshold=0.55)
    assert fused[0].decision == "occupied"
    assert fused[0].weighted_occupied_score == 1.0


def test_unanimous_unoccupied_detected():
    ts = dt.datetime(2026, 1, 1, 12, 0)
    reports = [_report(f"n{i}", False, 1.0, ts) for i in range(3)]
    fused = fuse_reports(reports, occupied_threshold=0.55)
    assert fused[0].decision == "unoccupied"


def test_high_reliability_node_dominates_low_reliability_disagreement():
    ts = dt.datetime(2026, 1, 1, 12, 0)
    reports = [
        _report("reliable", True, 5.0, ts),
        _report("unreliable_a", False, 0.5, ts),
        _report("unreliable_b", False, 0.5, ts),
    ]
    fused = fuse_reports(reports, occupied_threshold=0.55)
    # weighted score = 5 / (5 + 0.5 + 0.5) = 0.833 -> occupied
    assert fused[0].decision == "occupied"


def test_latest_fusion_snapshot_ignores_older_timestamps():
    old_ts = dt.datetime(2026, 1, 1, 11, 0)
    new_ts = dt.datetime(2026, 1, 1, 12, 0)
    reports = [
        _report("n1", True, 1.0, old_ts),
        _report("n1", False, 1.0, new_ts),
    ]
    fused = latest_fusion_snapshot(reports, occupied_threshold=0.55)
    assert fused[0].timestamp == new_ts
    assert fused[0].decision == "unoccupied"
