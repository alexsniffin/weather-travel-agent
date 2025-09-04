from typing import Any, Optional, TypedDict


class TripState(TypedDict, total=False):
    """State object that flows through the travel agent graph."""

    user_input: str
    origin: str
    destination: str
    travel_date: Optional[str]
    route: dict[str, Any]
    stops: list[dict[str, Any]]
    forecasts: list[dict[str, Any]]
    reply: str
    need: Optional[str]
