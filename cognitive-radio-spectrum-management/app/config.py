"""Application configuration, loaded from environment variables / .env."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    scan_freq_start_hz: int = 400_000_000
    scan_freq_end_hz: int = 6_000_000_000
    channel_bandwidth_hz: int = 5_000_000

    fusion_occupied_threshold: float = 0.55

    power_control_target_sinr_db: float = 10.0
    power_control_max_iterations: int = 50
    power_control_max_tx_power_dbm: float = 30.0

    forecast_horizon_steps: int = 6
    model_path: str = "./models/usage_forecaster.joblib"

    api_title: str = "SpectrumSense Cognitive Radio Management API"
    api_env: str = "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
