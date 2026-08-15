"""
Abstract SDR (software-defined radio) hardware interface.

This module defines the *contract* a real hardware backend would implement
(e.g. wrapping GNU Radio, UHD/USRP, or SoapySDR), and ships only a
`MockSDR` implementation that operates on simulated in-memory state. No
code in this file or anywhere else in this repository transmits or
receives real RF signals.

To integrate real hardware, implement `SDRInterface` against your
radio's SDK/driver and inject it wherever `MockSDR` is used today — the
sensing, fusion, allocation, and power-control logic is written against
this interface and does not need to change.
"""
from __future__ import annotations

import abc
from dataclasses import dataclass, field


@dataclass
class SDRLinkConfig:
    link_id: str
    center_freq_hz: int
    bandwidth_hz: int
    tx_power_dbm: float
    enabled: bool = True


class SDRInterface(abc.ABC):
    """Contract for a controllable SDR array. Implement against real hardware here."""

    @abc.abstractmethod
    def apply_channel_assignment(self, link_id: str, center_freq_hz: int, bandwidth_hz: int) -> None:
        """Reconfigure a link's operating channel."""

    @abc.abstractmethod
    def apply_tx_power(self, link_id: str, tx_power_dbm: float) -> None:
        """Set a link's transmit power."""

    @abc.abstractmethod
    def disable_link(self, link_id: str) -> None:
        """Immediately stop transmission on a link (e.g. protected-band conflict detected)."""

    @abc.abstractmethod
    def get_link_state(self, link_id: str) -> SDRLinkConfig:
        """Return the current configuration of a link."""


class MockSDR(SDRInterface):
    """
    In-memory simulated SDR array for development, testing, and demos.

    Tracks configuration state exactly as a real hardware backend would,
    without producing any RF output.
    """

    def __init__(self) -> None:
        self._links: dict[str, SDRLinkConfig] = {}
        self.command_log: list[str] = []

    def register_link(self, link_id: str, center_freq_hz: int, bandwidth_hz: int, tx_power_dbm: float = 0.0) -> None:
        self._links[link_id] = SDRLinkConfig(
            link_id=link_id,
            center_freq_hz=center_freq_hz,
            bandwidth_hz=bandwidth_hz,
            tx_power_dbm=tx_power_dbm,
        )

    def apply_channel_assignment(self, link_id: str, center_freq_hz: int, bandwidth_hz: int) -> None:
        link = self._require_link(link_id)
        link.center_freq_hz = center_freq_hz
        link.bandwidth_hz = bandwidth_hz
        self.command_log.append(
            f"[SIMULATED] {link_id}: retuned to {center_freq_hz / 1e6:.3f} MHz, bw={bandwidth_hz / 1e6:.3f} MHz"
        )

    def apply_tx_power(self, link_id: str, tx_power_dbm: float) -> None:
        link = self._require_link(link_id)
        link.tx_power_dbm = tx_power_dbm
        self.command_log.append(f"[SIMULATED] {link_id}: tx power set to {tx_power_dbm:.2f} dBm")

    def disable_link(self, link_id: str) -> None:
        link = self._require_link(link_id)
        link.enabled = False
        self.command_log.append(f"[SIMULATED] {link_id}: link disabled")

    def get_link_state(self, link_id: str) -> SDRLinkConfig:
        return self._require_link(link_id)

    def _require_link(self, link_id: str) -> SDRLinkConfig:
        if link_id not in self._links:
            raise KeyError(f"Unknown link_id: {link_id}")
        return self._links[link_id]
