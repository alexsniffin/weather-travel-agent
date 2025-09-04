import asyncio
import random
import time
from typing import Any, List

import httpx

from weather_travel_agent.agent.types import TripState
from weather_travel_agent.models.config import settings


class GetWeatherNode:
    """Node for fetching weather data for route stops."""

    def __init__(self):
        pass

    def _rng(self, lat: float, lon: float) -> random.Random:
        """
        Create a Random instance. If settings.mock_seed is provided,
        generate repeatable results per (lat, lon); otherwise, use a time-based seed.
        """
        if settings.mock_seed is None:
            # non-deterministic per run
            return random.Random(time.time_ns())

        # deterministic: mix seed with rounded coords
        base = int(settings.mock_seed)
        lat_i = int(round(lat * 10_000))
        lon_i = int(round(lon * 10_000))
        return random.Random((base ^ lat_i ^ (lon_i << 1)) & 0xFFFFFFFF)

    def _celsius_to_units(self, c: float, units: str) -> float:
        if units == "imperial":  # Fahrenheit
            return c * 9 / 5 + 32
        if units == "standard":  # Kelvin
            return c + 273.15
        return c  # metric (Celsius)

    def _mock_onecall_response(
        self, lat: float, lon: float, units: str
    ) -> dict[str, Any]:
        r = self._rng(lat, lon)

        days = []
        weather_kinds = [
            ("Clear", "clear sky"),
            ("Clouds", "scattered clouds"),
            ("Rain", "light rain"),
            ("Thunderstorm", "thunderstorms possible"),
            ("Drizzle", "drizzle"),
            ("Snow", "light snow"),
            ("Mist", "misty"),
        ]

        for _ in range(7):
            # Start from a realistic max temp in Celsius, then convert
            max_c = r.uniform(15.0, 35.0)  # 59°F–95°F range
            min_c = max_c - r.uniform(4.0, 10.0)  # daily swing 4–10°C
            min_u = round(self._celsius_to_units(min_c, units), 1)
            max_u = round(self._celsius_to_units(max_c, units), 1)

            main, desc = r.choice(weather_kinds)
            days.append(
                {
                    "temp": {"min": min_u, "max": max_u},
                    "weather": [{"main": main, "description": desc}],
                }
            )

        return {"lat": lat, "lon": lon, "units": units, "daily": days}

    async def _fetch_onecall(self, lat: float, lon: float) -> dict[str, Any]:
        params = {
            "lat": lat,
            "lon": lon,
            "appid": settings.openweather_api_key,
            "units": settings.units,
            "exclude": "minutely,alerts",
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                r = await client.get(
                    "https://api.openweathermap.org/data/3.0/onecall", params=params
                )
                r.raise_for_status()
            except Exception:
                r.raise_for_status()

        return r.json()

    async def fetch_weather_one(self, lat: float, lon: float) -> dict[str, Any]:
        """Fetch weather data for a single location (mock or real), and build a short summary."""
        if settings.mock_weather:
            data = self._mock_onecall_response(lat, lon, settings.units)
        else:
            data = await self._fetch_onecall(lat, lon)

        days = (data.get("daily") or [])[:2]

        def day_to_str(d: dict[str, Any]) -> str:
            t = d.get("temp", {})
            w = (d.get("weather") or [{}])[0]

            def fmt(v: Any) -> str:
                try:
                    f = float(v)
                    return str(int(f)) if f.is_integer() else str(f)
                except Exception:
                    return str(v)

            return f"{w.get('main', '?')} (min {fmt(t.get('min', '?'))}°, max {fmt(t.get('max', '?'))}°)"

        summary = "; ".join(day_to_str(d) for d in days) if days else "No daily data"
        return {"raw": data, "summary": summary}

    async def __call__(self, state: TripState) -> TripState:
        """Fetch weather data for all stops along the route."""
        stops = state.get("stops", [])
        if not stops:
            return {"need": "No stops available to fetch weather."}

        coros = [self.fetch_weather_one(s["lat"], s["lon"]) for s in stops]
        gathered = await asyncio.gather(*coros, return_exceptions=True)

        results: List[dict[str, Any]] = []
        for s, g in zip(stops, gathered, strict=False):
            if isinstance(g, Exception):
                results.append({**s, "summary": f"weather error: {g}"})
            else:
                results.append({**s, "summary": g.get("summary", "")})
        return {"forecasts": results}
