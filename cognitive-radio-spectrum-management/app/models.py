"""Pydantic domain models shared across the SpectrumSense services/API."""
from __future__ import annotations

import datetime as dt
from pydantic import BaseModel


class ProtectedBand(BaseModel):
    name: str
    start_hz: int
    end_hz: int
    category: str  # e.g. "public-safety", "aeronautical-radar", "amateur"
    source: str = "sample-illustrative"  # ALWAYS sample data — see docs/REGULATORY_NOTES.md


class NodeReport(BaseModel):
    node_id: str
    channel_index: int
    center_freq_hz: int
    timestamp: dt.datetime
    measured_power_dbm: float
    occupied: bool
    reliability_weight: float = 1.0


class FusionResult(BaseModel):
    channel_index: int
    center_freq_hz: int
    timestamp: dt.datetime
    weighted_occupied_score: float
    decision: str  # "occupied" | "unoccupied"
    n_reports: int


class ChannelAllocation(BaseModel):
    channel_index: int
    center_freq_hz: int
    status: str  # "assigned" | "unavailable_protected" | "unavailable_occupied"
    reason: str


class PowerControlState(BaseModel):
    link_id: str
    iteration: int
    tx_power_dbm: float
    achieved_sinr_db: float
    converged: bool


class OccupancyForecast(BaseModel):
    channel_index: int
    forecast: list[float]
    horizon_steps: int
