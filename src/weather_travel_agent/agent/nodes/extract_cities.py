from typing import Any, List

import googlemaps
from googlemaps import convert

from weather_travel_agent.agent.types import TripState
from weather_travel_agent.models.config import settings


class ExtractCitiesNode:
    def __init__(self, gmaps_client=None):
        self.gmaps_client = gmaps_client or googlemaps.Client(
            key=settings.google_maps_api_key
        )

    def sample_polyline_points(
        self, encoded: str, step: int
    ) -> List[tuple[float, float]]:
        pts = convert.decode_polyline(encoded)
        if not pts:
            return []

        pts = [(p["lat"], p["lng"]) for p in pts]

        step = max(1, int(step))
        return pts[::step] + [pts[-1]]

    def __call__(self, state: TripState) -> TripState:
        overview = state["route"].get("overview_polyline", {}).get("points")
        if not overview:
            return {"need": "Route polyline missing; cannot extract stops."}

        coords = self.sample_polyline_points(overview, step=settings.sample_every_nth)

        stops: List[dict[str, Any]] = []
        seen = set()

        for lat, lon in coords:
            rev = (
                self.gmaps_client.reverse_geocode(
                    (lat, lon),
                    # only return county/locality-ish results
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
