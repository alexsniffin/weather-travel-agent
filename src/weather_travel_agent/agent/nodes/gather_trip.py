from typing import Optional, Tuple

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.messages.system import SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from weather_travel_agent.agent.types import TripState
from weather_travel_agent.models.config import settings


@tool
def extract_places(
    origin: Optional[str] = None, destination: Optional[str] = None
) -> dict:
    """Extract origin and destination from user input.
    Values may be None if not found."""
    return {"origin": origin, "destination": destination}


class GatherTripNode:
    """Node for gathering trip information from user input."""

    def __init__(self):
        if not settings.openai_api_key:
            raise ValueError("Missing OpenAI API key")

        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.2,
            api_key=settings.openai_api_key,
        ).bind_tools([extract_places])

    def extract_places_from_text(
        self, text: str
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Use LLM with tool calling to extract origin and destination.
        Returns (origin, destination, reply).
        """
        try:
            resp: AIMessage = self.llm.invoke(
                [
                    SystemMessage(
                        content='''You're a helpful travel assistant that will generate the route for a single leg itenirary and the weather forecast along the way.
                        
                        Goal:
                        - Decide if you can make a tool call based on what you know about the message from the user
                        - If you can't use the tool, ask the user a clarifying question to statisfy the contraints of the tool
                        - Your response should be to ask the user for the required content you need

                        Example:
                        """
                        user: Hi
                        assistant: Hi, please provide an origin and desitination.
                        """
                        '''
                    ),
                    HumanMessage(content=text),
                ]
            )

            # If the model chose to call the tool
            if resp.tool_calls:
                tool_call = resp.tool_calls[0]
                if tool_call["name"] == "extract_places":
                    args = tool_call["args"]
                    origin = args.get("origin")
                    destination = args.get("destination")
                    return origin, destination, resp.content.strip()

            # Otherwise, it's a direct response to the user
            if resp.content and resp.content.strip():
                return None, None, resp.content.strip()

            return None, None, None

        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return None, None, None

    def __call__(self, state: TripState) -> TripState:
        """Process the state to extract origin and destination."""
        origin = state.get("origin")
        destination = state.get("destination")

        if not origin or not destination:
            o, d, reply = self.extract_places_from_text(state.get("user_input", ""))
            origin = origin or o
            destination = destination or d

            out: TripState = {}
            if not origin or not destination:
                if reply:
                    out["need"] = reply
                else:
                    out["need"] = (
                        "Could you please provide both an origin and destination?"
                    )
                return out

        return {"origin": origin, "destination": destination}
