import os

import pandas as pd
from fastapi import APIRouter, HTTPException

from app.services.usage_forecaster import TransformerLiteForecaster, build_channel_series

router = APIRouter(prefix="/forecast", tags=["forecasting"])

SAMPLE_SCANS_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "sample", "spectrum_scans.csv")


@router.get("/channel/{channel_index}")
def forecast_channel(channel_index: int, window_size: int = 12, horizon_steps: int = 6):
    df = pd.read_csv(SAMPLE_SCANS_PATH, parse_dates=["timestamp"])
    series = build_channel_series(df, channel_index)

    if len(series) < window_size + horizon_steps + 1:
        raise HTTPException(
            status_code=400,
            detail=f"Not enough history for channel {channel_index} to forecast with this window/horizon.",
        )

    model = TransformerLiteForecaster(window_size=window_size, horizon_steps=horizon_steps).fit(series)
    recent_window = series[-window_size:]
    forecast = model.predict(recent_window)

    return {
        "channel_index": channel_index,
        "horizon_steps": horizon_steps,
        "forecast_occupancy_fraction": [round(float(v), 4) for v in forecast],
    }
