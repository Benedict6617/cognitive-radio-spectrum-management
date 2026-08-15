"""
Closed-loop dynamic power control.

Implements a Foschini-Miljanic-style distributed power-control iteration:
each simulated link adjusts its transmit power proportionally to the gap
between its achieved and target SINR, which is known to converge to the
minimum feasible power vector when a feasible solution exists. This keeps
aggregate transmit power (and therefore inter-cell/inter-link interference)
as low as possible while still meeting each link's QoS target.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.models import PowerControlState


@dataclass
class Link:
    link_id: str
    gain_to_own_receiver: float       # linear channel gain, this link's Tx -> its own Rx
    gains_to_other_receivers: list[float]  # linear channel gain, this link's Tx -> every OTHER link's Rx
    noise_power_mw: float = 1e-9


def _sinr_linear(tx_powers: np.ndarray, gains_own: np.ndarray, interference_matrix: np.ndarray, noise: np.ndarray) -> np.ndarray:
    """Vectorized SINR computation for all links given a tx power vector."""
    signal = tx_powers * gains_own
    interference = interference_matrix @ tx_powers - (np.diag(interference_matrix) * tx_powers)
    return signal / (interference + noise)


def run_power_control(
    links: list[Link],
    target_sinr_db: float,
    max_iterations: int,
    max_tx_power_dbm: float,
    initial_power_dbm: float = 0.0,
) -> list[list[PowerControlState]]:
    """
    Run the iterative power-control loop and return, for each link, the
    full convergence history (one PowerControlState per iteration).
    """
    n = len(links)
    target_sinr_linear = 10 ** (target_sinr_db / 10)
    max_tx_power_mw = 10 ** (max_tx_power_dbm / 10)

    gains_own = np.array([l.gain_to_own_receiver for l in links])
    noise = np.array([l.noise_power_mw for l in links])

    # interference_matrix[i][j] = gain from link j's Tx into link i's Rx (j != i contributes interference to i)
    interference_matrix = np.zeros((n, n))
    for i, link in enumerate(links):
        for j in range(n):
            if j == i:
                interference_matrix[i][j] = link.gain_to_own_receiver
            else:
                # gains_to_other_receivers is indexed over the OTHER links in order
                other_idx = j if j < i else j - 1
                if other_idx < len(link.gains_to_other_receivers):
                    interference_matrix[i][j] = link.gains_to_other_receivers[other_idx]

    tx_power_mw = np.full(n, 10 ** (initial_power_dbm / 10))
    history: list[list[PowerControlState]] = [[] for _ in range(n)]

    for iteration in range(1, max_iterations + 1):
        sinr = _sinr_linear(tx_power_mw, gains_own, interference_matrix, noise)
        sinr = np.clip(sinr, 1e-12, None)

        converged_mask = sinr >= target_sinr_linear * 0.98

        for i, link in enumerate(links):
            achieved_db = 10 * np.log10(sinr[i])
            history[i].append(PowerControlState(
                link_id=link.link_id,
                iteration=iteration,
                tx_power_dbm=round(10 * np.log10(tx_power_mw[i]), 3),
                achieved_sinr_db=round(float(achieved_db), 3),
                converged=bool(converged_mask[i]),
            ))

        if converged_mask.all():
            break

        # Foschini-Miljanic update: p_i <- p_i * (target / achieved)
        tx_power_mw = tx_power_mw * (target_sinr_linear / sinr)
        tx_power_mw = np.clip(tx_power_mw, 1e-6, max_tx_power_mw)

    return history
