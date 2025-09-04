from typing import Any, List, Tuple
import googlemaps
from googlemaps import convert
import geopy.distance

from weather_travel_agent.agent.types import TripState
from weather_travel_agent.models.config import settings


class ExtractCitiesNode:

    def __init__(self, gmaps_client=None):
        self.gmaps_client = gmaps_client or googlemaps.Client(
            key=settings.google_maps_api_key
        )

    def sample_evenly(
        self, coords: List[Tuple[float, float]], km_interval: int, max_stops: int
    ) -> List[Tuple[float, float]]:
        """Spread stops evenly across the full route length."""
        if not coords:
            return []

        # Compute cumulative distances along the route
        cumulative = [0.0]
        for i in range(1, len(coords)):
            d = geopy.distance.distance(coords[i - 1], coords[i]).km
            cumulative.append(cumulative[-1] + d)

        total_dist = cumulative[-1]
        if total_dist == 0:
            return [coords[0]]

        # Decide number of stops
        num_stops = min(max_stops, max(2, int(total_dist // km_interval) + 1))

        # Target distances spaced evenly
        targets = [i * total_dist / (num_stops - 1) for i in range(num_stops)]

        sampled = []
        j = 0
        for t in targets:
            # Find the first point where cumulative distance >= target
            while j < len(cumulative) and cumulative[j] < t:
                j += 1
            sampled.append(coords[min(j, len(coords) - 1)])

        return sampled

    def __call__(self, state: TripState) -> TripState:
        overview = state["route"].get("overview_polyline", {}).get("points")
        if not overview:
            return {"need": "Route polyline missing; cannot extract stops."}

        # Decode polyline
        pts = convert.decode_polyline(overview)
        coords = [(p["lat"], p["lng"]) for p in pts]

        # Evenly spread across full route
        coords = self.sample_evenly(
            coords,
            km_interval=settings.sample_km_interval,
            max_stops=settings.max_stops,
        )

        stops: List[dict[str, Any]] = []
        seen = set()

        for lat, lon in coords:
            rev = (
                self.gmaps_client.reverse_geocode(
                    (lat, lon),
                    result_type="administrative_area_level_2|locality|administrative_area_level_3|sublocality",
                )
                or []
            )

            if not rev:
                continue

            comp = rev[0].get("address_components", [])
            county = next(
                (
                    c
                    for c in comp
                    if "administrative_area_level_2" in c.get("types", [])
                ),
                None,
            )
            locality = next((c for c in comp if "locality" in c.get("types", [])), None)
            admin1 = next(
                (
                    c
                    for c in comp
                    if "administrative_area_level_1" in c.get("types", [])
                ),
                None,
            )
            country = next((c for c in comp if "country" in c.get("types", [])), None)

            primary = county or locality
            if not primary:
                continue

            state_short = (admin1 or {}).get("short_name")
            country_short = (country or {}).get("short_name")

            name_parts = [primary.get("long_name"), state_short, country_short]
            name = ", ".join([p for p in name_parts if p])

            # avoid state only strings slipping through
            if name in {
                f"{state_short}, {country_short}",
                f"{state_short or ''}{', ' if state_short and country_short else ''}{country_short or ''}",
            }:
                continue

            dedupe_key = (primary.get("long_name"), state_short)
            if dedupe_key in seen:
                continue

            seen.add(dedupe_key)
            stops.append({"name": name, "lat": lat, "lon": lon})

            if len(stops) >= settings.max_stops:
                break

        return {"stops": stops}
