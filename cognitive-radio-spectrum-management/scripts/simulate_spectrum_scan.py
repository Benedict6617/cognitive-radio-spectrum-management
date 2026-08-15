"""
End-to-end demo: run one cooperative-sensing -> channel-allocation ->
power-control cycle against the sample data and print a human-readable
summary. Useful as a smoke test and as a walkthrough of how the pieces
fit together.
"""
from __future__ import annotations

import os
import sys

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.models import NodeReport  # noqa: E402
from app.services.cooperative_sensing import latest_fusion_snapshot  # noqa: E402
from app.services.channel_allocator import allocate_channel, allocate_all_channels_report  # noqa: E402
from app.services.protected_bands import load_protected_bands  # noqa: E402
from app.services.power_control import Link, run_power_control  # noqa: E402
from app.config import get_settings  # noqa: E402

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "sample")


def main() -> None:
    settings = get_settings()

    df = pd.read_csv(os.path.join(SAMPLE_DIR, "spectrum_scans.csv"), parse_dates=["timestamp"])
    reports = [
        NodeReport(
            node_id=row.node_id,
            channel_index=int(row.channel_index),
            center_freq_hz=int(row.center_freq_hz),
            timestamp=row.timestamp.to_pydatetime(),
            measured_power_dbm=float(row.measured_power_dbm),
            occupied=bool(row.occupied),
            reliability_weight=float(row.reliability_weight),
        )
        for row in df.itertuples()
    ]

    print("=== 1. Cooperative spectrum sensing (fusion of all nodes, latest timestamp) ===")
    fused = latest_fusion_snapshot(reports, settings.fusion_occupied_threshold)
    for r in fused:
        print(f"  ch{r.channel_index:2d}  {r.center_freq_hz/1e6:8.3f} MHz  "
              f"score={r.weighted_occupied_score:.3f}  -> {r.decision}")

    print("\n=== 2. Protected-band-aware channel allocation ===")
    bands = load_protected_bands()
    report = allocate_all_channels_report(fused, settings.channel_bandwidth_hz, bands)
    for a in report:
        print(f"  ch{a.channel_index:2d}  {a.center_freq_hz/1e6:8.3f} MHz  {a.status:22s}  {a.reason}")

    best = allocate_channel(fused, settings.channel_bandwidth_hz, bands)
    if best:
        print(f"\n  >> Best channel selected: ch{best.channel_index} "
              f"({best.center_freq_hz/1e6:.3f} MHz) — {best.reason}")
    else:
        print("\n  >> No channel currently available.")

    print("\n=== 3. Closed-loop power control (4 illustrative co-channel links) ===")
    import numpy as np
    rng = np.random.default_rng(3)
    n_links = 4
    links = []
    for i in range(n_links):
        gain_own = 10 ** (rng.uniform(-9, -7))
        gains_other = [10 ** (rng.uniform(-12, -10)) for _ in range(n_links - 1)]
        links.append(Link(link_id=f"link-{i+1}", gain_to_own_receiver=gain_own, gains_to_other_receivers=gains_other))

    history = run_power_control(
        links,
        target_sinr_db=settings.power_control_target_sinr_db,
        max_iterations=settings.power_control_max_iterations,
        max_tx_power_dbm=settings.power_control_max_tx_power_dbm,
    )
    for link_history in history:
        final = link_history[-1]
        print(f"  {final.link_id}: converged={final.converged} in {final.iteration} iterations, "
              f"tx_power={final.tx_power_dbm:.2f} dBm, sinr={final.achieved_sinr_db:.2f} dB")


if __name__ == "__main__":
    main()
