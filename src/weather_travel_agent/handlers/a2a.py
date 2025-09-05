from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import InMemoryQueueManager
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentProvider,
    AgentSkill,
    DataPart,
    TextPart,
)
from a2a.utils.message import new_agent_parts_message, new_agent_text_message

from weather_travel_agent.agent.types import TripState
from weather_travel_agent.models.chat import ChatIn, ChatOut


class WeatherTravelExecutor(AgentExecutor):
    """Agent executor for weather travel planning using LangGraph."""

    def __init__(self, graph):
        self.graph = graph

    async def execute(self, context: RequestContext, event_queue):
        text = context.get_user_input() or "no input"
        payload = ChatIn(message=text)
        result = await self._process_chat(payload)

        parts = []

        # Optional: early return if you're prompting for more info
        if getattr(result, "need", None):
            parts.append(TextPart(text=result.need))
            await event_queue.enqueue_event(
                new_agent_parts_message(
                    parts,
                    context_id=context.context_id,
                    task_id=context.task_id,
                )
            )
            return

        if result.reply:
            parts.append(TextPart(text=result.reply))

        structured = {
            "origin": result.origin,
            "destination": result.destination,
            "stops": result.stops,
            "forecasts": result.forecasts,
        }
        if any(v is not None for v in structured.values()):
            parts.append(DataPart(data=structured))

        # Enqueue a single message with multiple parts
        await event_queue.enqueue_event(
            new_agent_parts_message(
                parts,
                context_id=context.context_id,
                task_id=context.task_id,
            )
        )

    async def cancel(self, context: RequestContext, event_queue):
        """Cancel the current execution."""
        # Send cancellation message
        await event_queue.enqueue_event(
            new_agent_text_message(
                "Request cancelled",
                context_id=context.context_id,
                task_id=context.task_id,
            )
        )

    async def _process_chat(self, body: ChatIn) -> ChatOut:
        """Process chat input through the LangGraph workflow."""
        state: TripState = {
            "user_input": body.message or "",
        }

        # Run the graph
        result: TripState = await self.graph.ainvoke(state)

        # If gather asked for more info, return need message directly
        if result.get("need"):
            return ChatOut(reply=result["need"], need=result["need"])

        return ChatOut(
            reply=result.get("reply", ""),
            origin=result.get("origin"),
            destination=result.get("destination"),
            stops=result.get("stops"),
            forecasts=result.get("forecasts"),
        )


def build_agent_card(base_url: str = "http://localhost:8000") -> AgentCard:
    """Build the agent card for the weather travel agent."""
    return AgentCard(
        name="Weather Travel Agent",
        version="1.0.0",
        description="Plans driving itineraries and summarizes weather along the route",
        url=f"{base_url}/a2a",
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        provider=AgentProvider(
            organization="WeatherTravelCo",
            url="https://github.com/alexsniffin/weather-travel-agent",
        ),
        skills=[
            AgentSkill(
                id="itinerary.plan",
                name="Plan itinerary with weather",
                description="Given origin & destination, compute route, intermediate cities, and weather",
                input_modes=["text/plain"],
                output_modes=["text/plain", "application/json"],
                tags=["weather", "travel"],
            )
        ],
        capabilities=AgentCapabilities(streaming=True),
    )


def create_request_handler(graph) -> DefaultRequestHandler:
    """Create a request handler with the weather travel executor."""
    # Create the executor
    executor = WeatherTravelExecutor(graph)

    task_store = InMemoryTaskStore()
    queue_manager = InMemoryQueueManager()

    # Build the handler
    return DefaultRequestHandler(
        agent_executor=executor,
        task_store=task_store,
        queue_manager=queue_manager,
    )
