#!/usr/bin/env python3
from __future__ import annotations

import uvicorn
from a2a.server.apps.jsonrpc import A2AFastAPIApplication
from fastapi import FastAPI
from langgraph.graph import END, StateGraph

from weather_travel_agent.agent.conditions import (
    cont_after_directions,
    should_continue_after_gather,
)
from weather_travel_agent.agent.nodes.extract_cities import ExtractCitiesNode
from weather_travel_agent.agent.nodes.gather_trip import GatherTripNode
from weather_travel_agent.agent.nodes.get_directions import GetDirectionsNode
from weather_travel_agent.agent.nodes.get_weather import GetWeatherNode
from weather_travel_agent.agent.nodes.share_forecast import ShareForecastNode
from weather_travel_agent.agent.types import TripState
from weather_travel_agent.handlers.a2a import build_agent_card, create_request_handler
from weather_travel_agent.models.config import settings

# Load and validate config settings
try:
    settings.validate_required_keys()
except ValueError as e:
    print(f"Configuration error: {e}")
    raise SystemExit(1)

app = FastAPI(
    title="LangGraph Weather Travel Agent (A2A)",
    description="Agent example app for a travel agent that provides weather details with an A2A interface.",
)


@app.get("/health")
def health():
    return {"ok": True}


def build_graph():
    builder = StateGraph(TripState)

    gather_trip_node = GatherTripNode()
    get_directions_node = GetDirectionsNode()
    extract_cities_node = ExtractCitiesNode()
    get_weather_node = GetWeatherNode()
    share_forecast_node = ShareForecastNode()

    builder.add_node("gather_trip", gather_trip_node)
    builder.add_node("get_directions", get_directions_node)
    builder.add_node("extract_cities", extract_cities_node)
    builder.add_node("get_weather", get_weather_node)
    builder.add_node("share_forecast", share_forecast_node)

    builder.set_entry_point("gather_trip")

    builder.add_conditional_edges(
        "gather_trip",
        should_continue_after_gather,
        {"get_directions": "get_directions", END: END},
    )
    builder.add_conditional_edges(
        "get_directions",
        cont_after_directions,
        {"extract_cities": "extract_cities", END: END},
    )

    builder.add_edge("extract_cities", "get_weather")
    builder.add_edge("get_weather", "share_forecast")
    builder.add_edge("share_forecast", END)

    return builder.compile()


graph = build_graph()
agent_card = build_agent_card()
handler = create_request_handler(graph)

a2a_app = A2AFastAPIApplication(agent_card=agent_card, http_handler=handler).build()
app.mount("/a2a", a2a_app)


def main():
    uvicorn.run(
        "src.weather_travel_agent.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.dev_mode,
    )


if __name__ == "__main__":
    main()
