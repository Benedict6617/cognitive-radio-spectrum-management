"""SpectrumSense FastAPI application entrypoint."""
from fastapi import FastAPI

from app.config import get_settings
from app.routers import spectrum, nodes, allocation, power_control, forecasting

settings = get_settings()

app = FastAPI(
    title=settings.api_title,
    description=(
        "Cognitive radio spectrum-management simulation: cooperative "
        "spectrum sensing, protected-band-aware channel allocation, "
        "closed-loop power control, and predictive usage analytics. "
        "This is a software simulation — it does not drive real RF "
        "hardware. See the project README for scope details."
    ),
    version="1.0.0",
)


@app.get("/health", tags=["system"])
def health_check():
    return {"status": "ok", "environment": settings.api_env}


app.include_router(spectrum.router)
app.include_router(nodes.router)
app.include_router(allocation.router)
app.include_router(power_control.router)
app.include_router(forecasting.router)
