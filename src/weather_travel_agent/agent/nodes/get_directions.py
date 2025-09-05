import googlemaps

from weather_travel_agent.agent.types import TripState
from weather_travel_agent.models.config import settings


class GetDirectionsNode:
    """Node for getting driving directions from Google Maps API."""

    def __init__(self, gmaps_client=None):
        self.gmaps_client = gmaps_client

    def __call__(self, state: TripState) -> TripState:
        """Get driving directions for the route."""
        if not self.gmaps_client:
            self.gmaps_client = googlemaps.Client(key=settings.google_maps_api_key)

        origin, destination = state["origin"], state["destination"]
        try:
            directions = self.gmaps_client.directions(origin, destination, mode="driving")
        except googlemaps.exceptions.ApiError as e:
            return {"need": "I was unable to find the route for the origin and destination, try a different name or locations."}

        if not directions:
            return {"need": "No route found. Try different locations."}

        route = directions[0]
        return {"route": route}
