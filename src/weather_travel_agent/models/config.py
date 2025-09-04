from typing import Literal, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    google_maps_api_key: str = Field(
        default="",
        description="Google Maps API key for Directions and Geocoding services",
        alias="GOOGLE_MAPS_API_KEY",
    )

    openweather_api_key: str = Field(
        default="",
        description="OpenWeather API key for weather data",
        alias="OPENWEATHER_API_KEY",
    )

    openai_api_key: str = Field(
        default="",
        description="OpenAI API key for LLM fallback extraction",
        alias="OPENAI_API_KEY",
    )

    units: Literal["imperial", "metric"] = Field(
        default="imperial",
        description="Temperature units for weather data",
        alias="UNITS",
    )

    max_stops: int = Field(
        default=8,
        description="Maximum number of stops to include in the itinerary",
        alias="MAX_STOPS",
        ge=1,
        le=20,
    )

    sample_every_nth: int = Field(
        default=10,
        description="Sample every Nth point from the start to end of the path.",
        alias="SAMPLE_EVERY_KM",
        gt=0,
        le=500,
    )

    mock_weather: bool = False
    mock_seed: Optional[int] = None

    openai_model: str = Field(
        default="gpt-4o-mini",
        description="OpenAI model to use for LLM extraction fallback",
        alias="OPENAI_MODEL",
    )

    host: str = Field(
        default="0.0.0.0", description="Host address for the FastAPI server"
    )

    port: int = Field(
        default=8000, description="Port for the FastAPI server", ge=1024, le=65535
    )

    dev_mode: bool = Field(False, description="Enable hot reloading?")

    def validate_required_keys(self) -> None:
        """Validate that required API keys are provided."""
        if not self.google_maps_api_key:
            raise ValueError("GOOGLE_MAPS_API_KEY is required")
        if not self.openweather_api_key:
            raise ValueError("OPENWEATHER_API_KEY is required")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required")

    @property
    def is_metric(self) -> bool:
        """Check if using metric units."""
        return self.units == "metric"


settings = Settings()


def get_settings() -> Settings:
    return settings
