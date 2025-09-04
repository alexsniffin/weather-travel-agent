from langgraph.graph import END

from weather_travel_agent.agent.types import TripState


# Conditional routing from gather
def should_continue_after_gather(state: TripState) -> str:
    return "get_directions" if not state.get("need") else END


# Conditional routing from directions
def cont_after_directions(state: TripState) -> str:
    return "extract_cities" if not state.get("need") else END
