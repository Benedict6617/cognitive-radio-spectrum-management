"""
Predictive spectrum-usage analytics: a compact, dependency-light
self-attention (transformer-style) time-series forecaster.

Rather than depending on a heavy deep-learning framework, this module
implements the core idea of transformer-style forecasting in plain NumPy:
the recent window of observations is treated as a *query*, historical
windows seen during "training" are treated as *keys*, and each historical
window's known continuation is its *value*. Scaled dot-product attention
over the historical windows produces a weighted blend of their
continuations as the forecast — the same attention mechanism transformers
use, applied non-parametrically so it trains instantly and ships with zero
GPU/deep-learning dependencies.

For teams that want a full learned (parametric) transformer, this class is
designed as a drop-in replacement target: swap `TransformerLiteForecaster`
for a PyTorch `nn.Module` behind the same `fit`/`predict` interface used by
`app/routers/forecasting.py`, without touching the API layer.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


def _softmax(x: np.ndarray) -> np.ndarray:
    x = x - np.max(x)
    e = np.exp(x)
    return e / e.sum()


@dataclass
class TransformerLiteForecaster:
    """Attention-based analog forecaster for a single channel's occupancy series."""

    window_size: int = 12
    horizon_steps: int = 6
    temperature: float = 1.0

    _keys: np.ndarray = field(default=None, repr=False)       # (n_windows, window_size)
    _values: np.ndarray = field(default=None, repr=False)     # (n_windows, horizon_steps)
    _key_mean: float = 0.0
    _key_std: float = 1.0

    def fit(self, series: np.ndarray) -> "TransformerLiteForecaster":
        series = np.asarray(series, dtype=float)
        n = len(series)
        needed = self.window_size + self.horizon_steps
        if n < needed + 1:
            raise ValueError(
                f"Series too short to fit: need at least {needed + 1} points, got {n}"
            )

        keys, values = [], []
        for start in range(0, n - needed + 1):
            window = series[start:start + self.window_size]
            continuation = series[start + self.window_size:start + needed]
            keys.append(window)
            values.append(continuation)

        self._keys = np.stack(keys)
        self._values = np.stack(values)
        self._key_mean = float(self._keys.mean())
        self._key_std = float(self._keys.std() + 1e-8)
        return self

    def _attend(self, query: np.ndarray) -> np.ndarray:
        if self._keys is None:
            raise RuntimeError("Forecaster has not been fit yet.")

        q = (query - self._key_mean) / self._key_std
        k = (self._keys - self._key_mean) / self._key_std

        # scaled dot-product attention scores, scaled by sqrt(d_k) as in
        # standard transformer attention
        d_k = self.window_size
        scores = (k @ q) / np.sqrt(d_k) / max(self.temperature, 1e-6)
        weights = _softmax(scores)

        forecast = weights @ self._values  # weighted blend of historical continuations
        return forecast, weights

    def predict(self, recent_window: np.ndarray) -> np.ndarray:
        recent_window = np.asarray(recent_window, dtype=float)
        if len(recent_window) != self.window_size:
            raise ValueError(f"Expected a window of length {self.window_size}, got {len(recent_window)}")
        forecast, _ = self._attend(recent_window)
        return np.clip(forecast, 0.0, 1.0)

    def attention_weights(self, recent_window: np.ndarray) -> np.ndarray:
        """Expose the attention distribution over historical windows (for explainability)."""
        _, weights = self._attend(np.asarray(recent_window, dtype=float))
        return weights


def build_channel_series(scan_df, channel_index: int) -> np.ndarray:
    """
    Build a chronologically ordered occupancy-fraction series for one
    channel from a long-format scan dataframe with columns:
    channel_index, timestamp, occupied (bool/0-1), grouped across nodes.
    """
    channel_df = scan_df[scan_df["channel_index"] == channel_index].copy()
    grouped = channel_df.groupby("timestamp")["occupied"].mean().sort_index()
    return grouped.to_numpy(dtype=float)
