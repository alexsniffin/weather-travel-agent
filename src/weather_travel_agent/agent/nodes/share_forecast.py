from typing import Optional

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from weather_travel_agent.agent.types import TripState
from weather_travel_agent.models.config import settings


class ShareForecastNode:
    """Node for sharing formatted weather forecasts."""

    def __init__(self):
        pass

    def create_response(self, itinerary_text: str) -> Optional[str]:
        """Send the trip itinerary + forecast to the LLM for natural language response."""
        if not settings.openai_api_key:
            return None

        llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.3,
            api_key=settings.openai_api_key,
        )

        prompt = f'''You are a helpful travel assistant.
        
        Goal:
        The user has an itinerary and you've looked up the weather along the way. You're displaying the forecast in map within the same webpage for the user to view with the different conditions along the way. Write a clear summary keeping it concise and helpful, don't go in to details of all the places along the trip as the map outlines the forecast details. Limit to the start, middle and end.

        Example response structure:
        """
        Your trip from `(place A)` to `(place B)` looks like it'll be `(add a fun description)` 🌨️. Check out the map for more details.
        """

        Itinerary and forecasts:
        """
        {itinerary_text}
        """

        Respond in a friendly but concise way.'''  # noqa: W293

        try:
            resp = llm.invoke([HumanMessage(content=prompt)])

            if not resp.content or not resp.content.strip():
                print("LLM returned empty response")
                return None

            return resp.content.strip()

        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return None

    def __call__(self, state: TripState) -> TripState:
        """Format and return the weather forecast results."""
        origin, destination = state.get("origin"), state.get("destination")

        lines = [f"Trip from {origin} to {destination}:"]
        for i, f in enumerate(state.get("forecasts", []), 1):
            lines.append(f"  {i}. {f['name']}: {f['summary']}")
        itinerary_text = "\n".join(lines)

        # Send to LLM
        reply = self.create_response(itinerary_text)

        if not reply:
            reply = itinerary_text

        return {"reply": reply}
