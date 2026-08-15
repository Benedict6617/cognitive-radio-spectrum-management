import datetime as dt
import os

import pandas as pd
from fastapi import APIRouter, Depends

from app.config import get_settings
from app.models import NodeReport
from app.services.cooperative_sensing import latest_fusion_snapshot

router = APIRouter(prefix="/spectrum", tags=["spectrum"])

SAMPLE_SCANS_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "sample", "spectrum_scans.csv")


def _load_reports() -> list[NodeReport]:
    df = pd.read_csv(SAMPLE_SCANS_PATH, parse_dates=["timestamp"])
    reports = []
    for _, row in df.iterrows():
        reports.append(NodeReport(
            node_id=row["node_id"],
            channel_index=int(row["channel_index"]),
            center_freq_hz=int(row["center_freq_hz"]),
            timestamp=row["timestamp"].to_pydatetime(),
            measured_power_dbm=float(row["measured_power_dbm"]),
            occupied=bool(row["occupied"]),
            reliability_weight=float(row["reliability_weight"]),
        ))
    return reports


@router.get("/latest-fusion")
def latest_fusion(settings=Depends(get_settings)):
    reports = _load_reports()
    fused = latest_fusion_snapshot(reports, settings.fusion_occupied_threshold)
    return {"threshold": settings.fusion_occupied_threshold, "channels": fused}
