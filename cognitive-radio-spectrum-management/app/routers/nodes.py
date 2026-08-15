import os

import pandas as pd
from fastapi import APIRouter

router = APIRouter(prefix="/nodes", tags=["nodes"])

SAMPLE_NODES_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "sample", "node_registry.csv")


@router.get("")
def list_nodes():
    df = pd.read_csv(SAMPLE_NODES_PATH)
    return df.to_dict(orient="records")
