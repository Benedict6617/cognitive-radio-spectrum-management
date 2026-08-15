"""
"Train" (fit) the usage forecaster for every channel in the sample scan
history and save the fitted forecasters to a single joblib artifact.

The TransformerLiteForecaster is non-parametric (attention over historical
analog windows), so "training" is instantaneous — this script exists to
give the project a conventional train/serve workflow and a persisted
artifact that the API layer (or a batch job) can load without recomputing
from raw CSVs each time.
"""
from __future__ import annotations

import os
import sys

import joblib
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.services.usage_forecaster import TransformerLiteForecaster, build_channel_series  # noqa: E402
from app.config import get_settings  # noqa: E402

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "sample")


def main() -> None:
    settings = get_settings()
    os.makedirs(os.path.dirname(settings.model_path) or ".", exist_ok=True)

    df = pd.read_csv(os.path.join(SAMPLE_DIR, "spectrum_scans.csv"), parse_dates=["timestamp"])
    channels = sorted(df["channel_index"].unique())

    forecasters = {}
    skipped = []
    for channel_index in channels:
        series = build_channel_series(df, channel_index)
        try:
            model = TransformerLiteForecaster(
                window_size=12, horizon_steps=settings.forecast_horizon_steps
            ).fit(series)
            forecasters[int(channel_index)] = model
        except ValueError:
            skipped.append(int(channel_index))

    joblib.dump(forecasters, settings.model_path)
    print(f"Fitted forecasters for {len(forecasters)} channels")
    if skipped:
        print(f"Skipped {len(skipped)} channels with insufficient history: {skipped}")
    print(f"Artifact written to {settings.model_path}")


if __name__ == "__main__":
    main()
